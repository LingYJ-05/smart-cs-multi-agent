<template>
  <div class="history-container">
    <div class="history-header">
      <h3 class="history-title">对话历史</h3>
      <el-input
        v-model="searchQuery"
        placeholder="搜索历史对话"
        prefix-icon="Search"
        size="small"
        class="search-input"
      />
    </div>
    <div class="history-list">
      <div
        v-for="item in filteredHistory"
        :key="item.id"
        class="history-item"
        :class="{ active: selectedId === item.id }"
        @click="handleSelect(item)"
      >
        <div class="history-content">
          <p class="history-text">{{ item.content }}</p>
          <span class="history-time">{{ item.time }}</span>
        </div>
        <div class="history-actions">
          <el-button size="small" icon="Copy" @click.stop="handleCopy(item.content)" />
        </div>
      </div>
    </div>
    <div v-if="filteredHistory.length === 0" class="empty-state">
      <MessageSquareIcon class="empty-icon" />
      <p class="empty-text">暂无对话历史</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatRound as MessageSquareIcon } from '@element-plus/icons-vue'

const emit = defineEmits<{
  (e: 'select', content: string): void
}>()

const searchQuery = ref('')
const selectedId = ref('')

const history = ref([
  {
    id: '1',
    content: '你们的理财产品年化收益率是多少？',
    time: '15:30',
  },
  {
    id: '2',
    content: '开户需要准备哪些材料？',
    time: '15:28',
  },
  {
    id: '3',
    content: '退款政策是怎样的？',
    time: '15:25',
  },
  {
    id: '4',
    content: '如何进行风险评估？',
    time: '15:20',
  },
])

const filteredHistory = computed(() => {
  if (!searchQuery.value.trim()) {
    return history.value
  }
  return history.value.filter((item) =>
    item.content.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const handleSelect = (item: typeof history.value[0]) => {
  selectedId.value = item.id
  emit('select', item.content)
}

const handleCopy = (content: string) => {
  navigator.clipboard.writeText(content)
  ElMessage.success('已复制')
}
</script>

<style scoped>
.history-container {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.history-title {
  font-size: 16px;
  font-weight: 600;
  color: #111111;
  margin: 0;
}

.search-input {
  width: 200px;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: #fafaf9;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.history-item:hover {
  background: #f5f1ec;
}

.history-item.active {
  background: rgba(255, 86, 0, 0.1);
  border-left: 3px solid #ff5600;
}

.history-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.history-text {
  font-size: 14px;
  color: #111111;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-time {
  font-size: 12px;
  color: #9c9fa5;
}

.history-actions {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.history-item:hover .history-actions {
  opacity: 1;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px;
}

.empty-icon {
  font-size: 48px;
  color: #d3cec6;
}

.empty-text {
  font-size: 14px;
  color: #626260;
  margin: 0;
}

@media (max-width: 768px) {
  .search-input {
    width: 150px;
  }
}
</style>