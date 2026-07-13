<template>
  <div class="chat-container">
    <div class="chat-header">
      <div class="header-left">
        <h2 class="header-title">会话聊天</h2>
        <span class="session-id">当前会话: {{ sessionId }}</span>
      </div>
      <div class="header-right">
        <el-button type="primary" plain size="small" @click="handleNewSession">
          <Plus class="btn-icon" />
          新建会话
        </el-button>
        <el-tag :type="isServiceRunning ? 'success' : 'danger'" size="small">
          {{ isServiceRunning ? "服务运行中" : "服务异常" }}
        </el-tag>
        <el-button size="small" @click="handleHealthCheck">
          <CircleCheck class="btn-icon" />
          系统健康
        </el-button>
      </div>
    </div>
    <div class="chat-messages" ref="messagesContainer">
      <div v-for="message in messages" :key="message.id" class="message-item">
        <div :class="['message-wrapper', message.role]">
          <div class="message-avatar">
            <component
              :is="message.role === 'user' ? User : ChatRound"
              class="avatar-icon"
            />
          </div>
          <div class="message-content">
            <div class="message-bubble">
              <p class="message-text">{{ message.content }}</p>
            </div>
            <div class="message-meta">
              <span class="message-time">{{
                formatTime(message.timestamp)
              }}</span>
            </div>
          </div>
        </div>
        <div
          v-if="message.intent || message.compliancePassed !== undefined"
          class="message-tags"
        >
          <el-tag type="info" size="small">
            <span class="tag-icon">
              <Aim class="icon" />
            </span>
            意图识别: {{ message.intent }}
          </el-tag>
          <el-tag
            :type="message.compliancePassed ? 'success' : 'danger'"
            size="small"
          >
            <span class="tag-icon">
              <Lock class="icon" />
            </span>
            合规检查: {{ message.compliancePassed ? "通过" : "未通过" }}
          </el-tag>
        </div>
      </div>
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
  Plus,
  CircleCheck,
  Aim,
  Lock,
  ArrowRight,
} from "@element-plus/icons-vue";
import { chatApi } from "@/api";
import type { Message, ChatRequest, ChatResponse } from "@/types";

const emit = defineEmits<{
  (e: "session-change", sessionId: string): void;
}>();

const messagesContainer = ref<HTMLElement | null>(null);
const sessionId = ref<string>(localStorage.getItem("sessionId") || "");
const inputMessage = ref("");
const isLoading = ref(false);
const isServiceRunning = ref(true);

const messages = ref<Message[]>([
  {
    id: "1",
    content: "你们的理财产品年化收益率是多少？",
    role: "user",
    timestamp: "2024-01-15 15:30:21",
  },
  {
    id: "2",
    content:
      "我们的理财产品A年化收益率为3.5%-5.2%，投资期限为6个月至3年，最低投资金额10000元。\n\n注意：理财非存款，产品有风险，投资须谨慎。",
    role: "assistant",
    timestamp: "2024-01-15 15:30:23",
    intent: "产品咨询",
    compliancePassed: true,
  },
]);

const formatTime = (timestamp: string) => {
  return timestamp;
};

const scrollToBottom = async () => {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
};

const getCurrentTime = () => {
  const now = new Date();
  return now.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
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
      content: response.response,
      role: "assistant",
      timestamp: getCurrentTime(),
      intent: response.intent,
      compliancePassed: response.compliance_passed,
    };
    messages.value.push(assistantMessage);
  } catch (error) {
    ElMessage.error("发送失败，请稍后重试");
    const errorMessage: Message = {
      id: generateId(),
      content: "系统处理异常，请稍后重试",
      role: "assistant",
      timestamp: getCurrentTime(),
    };
    messages.value.push(errorMessage);
  } finally {
    isLoading.value = false;
    scrollToBottom();
  }
};

const handleNewSession = () => {
  sessionId.value = "";
  localStorage.removeItem("sessionId");
  messages.value = [];
  emit("session-change", "");
  ElMessage.success("已创建新会话");
};

const handleHealthCheck = () => {
  isServiceRunning.value = !isServiceRunning.value;
  ElMessage.info(`系统健康状态: ${isServiceRunning.value ? "正常" : "异常"}`);
};

onMounted(() => {
  scrollToBottom();
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
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
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
