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
          <div class="history-name-row">
            <el-input
              v-if="editingId === item.id"
              v-model="item.name"
              size="small"
              @blur="handleSave(item)"
              @keyup.enter="handleSave(item)"
              class="name-input"
              autofocus
            />
            <span v-else class="history-name">{{ item.name }}</span>
          </div>
          <p class="history-text">{{ item.content }}</p>
          <span class="history-time">{{ item.time }}</span>
        </div>
        <div class="history-actions">
          <el-button size="small" :icon="Edit" @click.stop="handleEdit(item)"
            >编辑</el-button
          >
          <el-button
            size="small"
            :icon="Delete"
            type="danger"
            @click.stop="handleDelete(item.id)"
            >删除</el-button
          >
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
import { ref, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import {
  ChatRound as MessageSquareIcon,
  Edit,
  Delete,
} from "@element-plus/icons-vue";
import { historyApi, sessionApi } from "@/api";

const emit = defineEmits<{
  (e: "select", content: string): void;
}>();

const searchQuery = ref("");
const selectedId = ref("");
const editingId = ref<string | null>(null);

interface HistoryItem {
  id: string;
  name: string;
  content: string;
  time: string;
}

const history = ref<HistoryItem[]>([]);

const filteredHistory = computed(() => {
  if (!searchQuery.value.trim()) {
    return history.value;
  }
  return history.value.filter(
    (item) =>
      item.content.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      item.name.toLowerCase().includes(searchQuery.value.toLowerCase()),
  );
});

const loadHistory = async () => {
  try {
    const data = await historyApi.getChatHistory({ limit: 20 });
    const list = data as unknown as any[];
    history.value = list.map((item: any) => ({
      id: item.id,
      name: item.username || "未命名会话",
      content: item.content,
      time: item.time,
    }));
  } catch {
    history.value = [];
  }
};

const handleSelect = (item: HistoryItem) => {
  selectedId.value = item.id;
  emit("select", item.content);
};

const handleEdit = (item: HistoryItem) => {
  editingId.value = item.id;
};

const handleSave = async (item: HistoryItem) => {
  if (!item.name.trim()) {
    item.name = "未命名会话";
  }
  try {
    await sessionApi.updateSession(item.id, { name: item.name.trim() });
    ElMessage.success("重命名成功");
  } catch {
    ElMessage.error("重命名失败");
  } finally {
    editingId.value = null;
  }
};

const handleDelete = async (sessionId: string) => {
  try {
    await sessionApi.deleteSession(sessionId);
    history.value = history.value.filter((item) => item.id !== sessionId);
    ElMessage.success("删除成功");
  } catch {
    ElMessage.error("删除失败");
  }
};

onMounted(() => {
  loadHistory();
});
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

.history-name-row {
  display: flex;
  align-items: center;
}

.name-input {
  flex: 1;
  max-width: 200px;
}

.history-name {
  font-size: 13px;
  font-weight: 600;
  color: #111111;
}

.history-text {
  font-size: 14px;
  color: #626260;
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
  display: flex;
  gap: 4px;
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
