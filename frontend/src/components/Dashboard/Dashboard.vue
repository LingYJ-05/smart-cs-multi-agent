<template>
  <div class="dashboard">
    <Sidebar @menu-change="handleMenuChange" />
    <main class="main-content">
      <div class="content-wrapper">
        <div class="main-area">
          <ChatSession @session-change="handleSessionChange" />
        </div>
        <aside class="side-panel">
          <div class="panel-top">
            <ToolCenter />
          </div>
          <div class="panel-bottom">
            <SystemMetrics />
          </div>
        </aside>
      </div>
      <div class="bottom-panel">
        <ChatHistory @select="handleHistorySelect" />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Sidebar from '@/components/Layout/Sidebar.vue'
import ChatSession from '@/components/Chat/ChatSession.vue'
import ToolCenter from '@/components/Tools/ToolCenter.vue'
import SystemMetrics from '@/components/Metrics/SystemMetrics.vue'
import ChatHistory from '@/components/History/ChatHistory.vue'

const activeMenu = ref('chat')

const handleMenuChange = (menuId: string) => {
  activeMenu.value = menuId
}

const handleSessionChange = (sessionId: string) => {
  console.log('Session changed:', sessionId)
}

const handleHistorySelect = (content: string) => {
  console.log('Selected history:', content)
}
</script>

<style scoped>
.dashboard {
  display: flex;
  min-height: 100vh;
  background: #f5f1ec;
}

.main-content {
  flex: 1;
  margin-left: 240px;
  display: flex;
  flex-direction: column;
  padding: 24px;
  gap: 20px;
}

.content-wrapper {
  display: flex;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

.main-area {
  flex: 1;
  min-height: 0;
}

.side-panel {
  width: 320px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex-shrink: 0;
}

.panel-top {
  flex: 0 0 auto;
}

.panel-bottom {
  flex: 1;
  min-height: 0;
}

.bottom-panel {
  height: 200px;
}

@media (max-width: 1200px) {
  .side-panel {
    width: 280px;
  }
}

@media (max-width: 768px) {
  .main-content {
    margin-left: 60px;
    padding: 16px;
  }
  .content-wrapper {
    flex-direction: column;
  }
  .side-panel {
    width: 100%;
    flex-direction: row;
  }
  .panel-top,
  .panel-bottom {
    flex: 1;
    min-width: 0;
  }
  .bottom-panel {
    height: 150px;
  }
}

@media (max-width: 480px) {
  .side-panel {
    flex-direction: column;
  }
}
</style>