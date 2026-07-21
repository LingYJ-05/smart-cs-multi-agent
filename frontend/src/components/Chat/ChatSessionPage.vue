<template>
  <div class="chat-page">
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">会话聊天</h2>
        <p class="page-subtitle">当前会话: {{ currentSessionId }}</p>
      </div>
      <div class="header-actions">
        <el-button size="small" @click="createNewSession">
          <Plus class="btn-icon" />
          新建会话
        </el-button>
        <el-button size="small" type="warning" @click="clearMessages">
          <Delete class="btn-icon" />
          清空对话
        </el-button>
      </div>
    </div>

    <div class="content-wrapper">
      <div class="chat-area">
        <ChatSession @session-change="handleSessionChange" />
      </div>
      <aside class="side-panel">
        <div class="panel-section">
          <ToolCenter />
        </div>
        <div class="panel-section">
          <SystemMetrics />
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Plus, Delete } from "@element-plus/icons-vue";
import ChatSession from "./ChatSession.vue";
import ToolCenter from "../Tools/ToolCenter.vue";
import SystemMetrics from "../Metrics/SystemMetrics.vue";

const currentSessionId = ref(localStorage.getItem("sessionId") || "新会话");

const handleSessionChange = (sessionId: string) => {
  currentSessionId.value = sessionId;
};

const createNewSession = () => {
  localStorage.removeItem("sessionId");
  currentSessionId.value = "新会话";
  window.location.reload();
};

const clearMessages = () => {
  localStorage.removeItem("sessionId");
  currentSessionId.value = "新会话";
  window.location.reload();
};
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 24px;
  background: #f5f1ec;
  overflow: hidden;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.header-info .page-title {
  font-size: 24px;
  font-weight: 600;
  color: #111111;
  margin: 0 0 4px;
}

.header-info .page-subtitle {
  font-size: 14px;
  color: #626260;
  margin: 0;
}

.btn-icon {
  font-size: 14px;
  margin-right: 4px;
}

.content-wrapper {
  display: flex;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

.chat-area {
  flex: 1;
  min-width: 0;
  max-width: calc(100% - 340px);
}

.side-panel {
  width: 320px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex-shrink: 0;
  flex-grow: 0;
  overflow-y: auto;
  padding-right: 4px;
}

.side-panel::-webkit-scrollbar {
  width: 6px;
}

.side-panel::-webkit-scrollbar-track {
  background: transparent;
}

.side-panel::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.panel-section {
  flex: 0 0 auto;
}

@media (max-width: 1200px) {
  .side-panel {
    width: 280px;
  }
  .chat-area {
    max-width: calc(100% - 300px);
  }
}

@media (max-width: 768px) {
  .content-wrapper {
    flex-direction: column;
  }
  .chat-area {
    max-width: 100%;
    min-height: 400px;
  }
  .side-panel {
    width: 100%;
    flex-direction: row;
    overflow-x: auto;
  }
  .panel-section {
    flex: 1;
    min-width: 280px;
  }
}

@media (max-width: 480px) {
  .side-panel {
    flex-direction: column;
    overflow-x: visible;
  }
  .panel-section {
    min-width: 0;
  }
}
</style>
