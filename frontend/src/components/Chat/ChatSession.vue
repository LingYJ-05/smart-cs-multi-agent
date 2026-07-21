<template>
  <div class="chat-container">
    <div class="chat-messages">
      <VirtualScroll ref="virtualScrollRef" :items="messages" item-key="id">
        <template #default="{ item }">
          <div :key="item.id" class="message-item">
            <div :class="['message-wrapper', item.role]">
              <div class="message-avatar">
                <component
                  :is="item.role === 'user' ? User : ChatRound"
                  class="avatar-icon"
                />
              </div>
              <div class="message-content">
                <div class="message-bubble">
                  <p class="message-text">{{ item.content }}</p>
                </div>
                <div class="message-meta">
                  <span class="message-time">{{
                    formatTime(item.timestamp)
                  }}</span>
                </div>
              </div>
            </div>
            <div
              v-if="
                item.role === 'assistant' &&
                (item.intent || item.compliancePassed !== undefined)
              "
              class="message-tags"
            >
              <el-tag type="info" size="small">
                <span class="tag-icon"><Aim class="icon" /></span>
                意图识别: {{ item.intent }}
              </el-tag>
              <el-tag
                :type="item.compliancePassed ? 'success' : 'danger'"
                size="small"
              >
                <span class="tag-icon"><Lock class="icon" /></span>
                合规检查: {{ item.compliancePassed ? "通过" : "未通过" }}
              </el-tag>
              <el-tag
                v-if="item.complianceViolations?.length"
                type="warning"
                size="small"
              >
                {{ item.complianceViolations.join("; ") }}
              </el-tag>
            </div>
          </div>
        </template>
      </VirtualScroll>
      <div v-if="isLoading" class="loading-indicator">
        <el-skeleton :rows="3" animated />
      </div>
    </div>
    <div class="chat-input-wrapper">
      <el-input
        v-model="inputMessage"
        placeholder="请输入您的问题..."
        :disabled="isLoading"
        @keyup.enter="handleSend"
        class="chat-input"
      >
        <template #append>
          <el-button
            type="primary"
            :disabled="!inputMessage.trim() || isLoading"
            @click="handleSend"
            class="send-btn"
          >
            <ArrowRight class="send-icon" />
            发送
          </el-button>
        </template>
      </el-input>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from "vue";
import { ElMessage } from "element-plus";
import {
  ChatRound,
  User,
  Aim,
  Lock,
  ArrowRight,
} from "@element-plus/icons-vue";
import { chatApi, historyApi } from "@/api";
import type { Message, ChatRequest, ChatResponse } from "@/types";
import VirtualScroll from "@/components/VirtualScroll.vue";

const emit = defineEmits<{
  (e: "session-change", sessionId: string): void;
}>();

const virtualScrollRef = ref<InstanceType<typeof VirtualScroll> | null>(null);
const sessionId = ref<string>(localStorage.getItem("sessionId") || "");
const inputMessage = ref("");
const isLoading = ref(false);

const messages = ref<Message[]>([]);

const formatTime = (timestamp: string) => timestamp;

const scrollToBottom = async () => {
  await nextTick();
  if (virtualScrollRef.value) {
    virtualScrollRef.value.scrollToBottom();
  }
};

const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
};

const getCurrentTime = () => {
  return new Date().toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
};

const typeWriter = async (
  messageId: string,
  text: string,
  speed: number = 30,
) => {
  const messageIndex = messages.value.findIndex((m) => m.id === messageId);
  if (messageIndex === -1) return;

  messages.value[messageIndex].content = "";
  let index = 0;
  return new Promise<void>((resolve) => {
    const interval = setInterval(() => {
      if (index < text.length) {
        messages.value[messageIndex].content += text[index];
        index++;
        nextTick(() => {
          scrollToBottom();
        });
      } else {
        clearInterval(interval);
        resolve();
      }
    }, speed);
  });
};

const handleSend = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return;

  const userMessage: Message = {
    id: generateId(),
    content: inputMessage.value,
    role: "user",
    timestamp: getCurrentTime(),
  };
  messages.value.push(userMessage);
  inputMessage.value = "";
  scrollToBottom();

  isLoading.value = true;

  try {
    const request: ChatRequest = {
      message: userMessage.content,
      user_id: "admin",
      session_id: sessionId.value || undefined,
    };
    const response: ChatResponse = await chatApi.sendMessage(request);

    if (!sessionId.value) {
      sessionId.value = response.session_id;
      localStorage.setItem("sessionId", response.session_id);
      emit("session-change", response.session_id);
    }

    const assistantMessage: Message = {
      id: generateId(),
      content: "",
      role: "assistant",
      timestamp: getCurrentTime(),
      intent: response.intent,
      compliancePassed: response.compliance_passed,
      complianceRiskLevel: response.compliance_risk_level,
      complianceViolations: response.compliance_violations,
    };
    messages.value.push(assistantMessage);
    await typeWriter(assistantMessage.id, response.response);
  } catch {
    ElMessage.error("发送失败，请稍后重试");
    messages.value.push({
      id: generateId(),
      content: "系统处理异常，请稍后重试",
      role: "assistant",
      timestamp: getCurrentTime(),
    });
  } finally {
    isLoading.value = false;
    scrollToBottom();
  }
};

const loadHistory = async () => {
  if (!sessionId.value) return;
  try {
    const data = await historyApi.getHistory(sessionId.value);
    const result = data as any;
    const historyMessages: Message[] = [];

    if (result.messages && Array.isArray(result.messages)) {
      historyMessages.push(
        ...result.messages.map((msg: any) => ({
          id: msg.id || generateId(),
          content: msg.content || "",
          role: msg.role || "assistant",
          timestamp: msg.timestamp || getCurrentTime(),
          intent: msg.intent,
          compliancePassed: msg.compliance_passed,
          complianceRiskLevel: msg.compliance_risk_level,
          complianceViolations: msg.compliance_violations || [],
        })),
      );
    }

    messages.value = historyMessages;
    await scrollToBottom();
  } catch (error) {
    console.error("加载历史消息失败:", error);
    messages.value = [];
  }
};

onMounted(() => {
  loadHistory();
});
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #ebe7e1;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #111111;
  margin: 0;
}

.session-id {
  font-size: 12px;
  color: #626260;
  font-family: "JetBrains Mono", monospace;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-icon {
  font-size: 14px;
  margin-right: 4px;
}

.chat-messages {
  flex: 1;
  padding: 24px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.message-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message-wrapper {
  display: flex;
  gap: 12px;
}

.message-wrapper.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-wrapper.user .message-avatar {
  background: linear-gradient(135deg, #111111, #2a2a28);
}

.message-wrapper.assistant .message-avatar {
  background: linear-gradient(135deg, #ff5600, #ff7838);
}

.avatar-icon {
  font-size: 18px;
  color: #ffffff;
}

.message-content {
  max-width: 70%;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.message-wrapper.user .message-content {
  align-items: flex-end;
}

.message-bubble {
  padding: 14px 18px;
  border-radius: 12px;
  line-height: 1.6;
}

.message-wrapper.user .message-bubble {
  background: #111111;
  border-bottom-right-radius: 4px;
}

.message-wrapper.assistant .message-bubble {
  background: #f5f1ec;
  border-bottom-left-radius: 4px;
}

.message-text {
  font-size: 15px;
  margin: 0;
  white-space: pre-wrap;
}

.message-wrapper.user .message-text {
  color: #ffffff;
}

.message-wrapper.assistant .message-text {
  color: #111111;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.message-time {
  font-size: 12px;
  color: #9c9fa5;
}

.message-tags {
  display: flex;
  gap: 8px;
  padding-left: 52px;
  flex-wrap: wrap;
}

.message-wrapper.user .message-tags {
  padding-left: 0;
  padding-right: 52px;
  justify-content: flex-end;
}

.tag-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  vertical-align: middle;
  margin-right: 4px;
  line-height: 1;
}

.tag-icon .icon {
  font-size: 10px;
  width: 10px;
  height: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.tag-icon .icon svg {
  width: 10px !important;
  height: 10px !important;
}

.loading-indicator {
  padding: 16px;
}

.chat-input-wrapper {
  padding: 20px 24px;
  border-top: 1px solid #ebe7e1;
  flex-shrink: 0;
}

.chat-input {
  border-radius: 8px;
}

.send-btn {
  border-radius: 0 8px 8px 0;
  padding: 0 20px;
}

.send-icon {
  font-size: 14px;
  margin-right: 4px;
}

@media (max-width: 768px) {
  .message-content {
    max-width: 85%;
  }
  .chat-header {
    padding: 16px;
  }
  .chat-messages {
    padding: 16px;
  }
  .chat-input-wrapper {
    padding: 16px;
  }
}
</style>
