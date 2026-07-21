<template>
  <div class="history-page">
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">对话历史</h2>
        <p class="page-subtitle">管理您的所有会话记录</p>
      </div>
    </div>
    <div class="page-content">
      <ChatHistory />
    </div>
  </div>
</template>

<script setup lang="ts">
import ChatHistory from './ChatHistory.vue'
</script>

<style scoped>
.history-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 24px;
  background: #f5f1ec;
  overflow: hidden;
}

.page-header {
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

.page-content {
  flex: 1;
  min-height: 0;
}
</style>
