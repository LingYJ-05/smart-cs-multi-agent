<template>
  <div class="history-container">
    <div class="history-header">
      <div class="header-left">
        <div class="header-icon">
          <Clock class="icon" />
        </div>
        <div class="header-text">
          <h3 class="history-title">对话历史</h3>
          <p class="history-count">{{ total }} 条记录</p>
        </div>
      </div>
      <el-input
        v-model="searchQuery"
        placeholder="搜索历史对话..."
        prefix-icon="Search"
        size="small"
        class="search-input"
        @input="handleSearch"
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
        <div class="item-avatar">
          <ChatRound class="avatar-icon" />
        </div>
        <div class="item-content">
          <div class="item-header">
            <el-input
              v-if="editingId === item.id"
              v-model="item.name"
              size="small"
              @blur="handleSave(item)"
              @keyup.enter="handleSave(item)"
              class="name-input"
              autofocus
            />
            <span v-else class="item-name">{{ item.name }}</span>
            <span class="item-time">{{ item.time }}</span>
          </div>
          <p class="item-text">{{ item.content }}</p>
        </div>
        <div class="item-actions">
          <el-button
            size="small"
            :icon="Edit"
            @click.stop="handleEdit(item)"
            class="action-btn edit-btn"
            >编辑</el-button
          >
          <el-button
            size="small"
            :icon="Delete"
            type="danger"
            @click.stop="handleDelete(item.id)"
            class="action-btn delete-btn"
            >删除</el-button
          >
        </div>
      </div>
    </div>
    <div v-if="filteredHistory.length === 0" class="empty-state">
      <div class="empty-icon-wrapper">
        <MessageSquareIcon class="empty-icon" />
      </div>
      <p class="empty-title">暂无对话历史</p>
      <p class="empty-subtitle">开始您的第一次对话，记录将保存在这里</p>
    </div>
    <div v-if="total > 0" class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[5, 10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        class="pagination"
        @size-change="handlePageChange"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import {
  ChatRound as MessageSquareIcon,
  ChatRound,
  Clock,
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
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);

interface HistoryItem {
  id: string;
  session_id: string;
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
    const data = await historyApi.getChatHistory({
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value,
    });
    const result = data as unknown as { list: any[]; total: number };
    history.value = result.list.map((item: any) => ({
      id: item.id,
      session_id: item.session_id,
      name: item.username || "未命名会话",
      content: item.content,
      time: item.time,
    }));
    total.value = result.total;
  } catch {
    history.value = [];
    total.value = 0;
  }
};

const handleSearch = () => {
  currentPage.value = 1;
  loadHistory();
};

const handlePageChange = () => {
  loadHistory();
};

const handleSelect = (item: HistoryItem) => {
  selectedId.value = item.id;
  emit("select", item.session_id);
};

const handleEdit = (item: HistoryItem) => {
  editingId.value = item.id;
};

const handleSave = async (item: HistoryItem) => {
  if (!item.name.trim()) {
    item.name = "未命名会话";
  }
  try {
    await sessionApi.updateSession(item.session_id, { name: item.name.trim() });
    ElMessage.success("重命名成功");
  } catch {
    ElMessage.error("重命名失败");
  } finally {
    editingId.value = null;
  }
};

const handleDelete = async (itemId: string) => {
  const item = history.value.find((h) => h.id === itemId);
  if (!item) return;

  try {
    await sessionApi.deleteSession(item.session_id);
    history.value = history.value.filter((h) => h.id !== itemId);
    total.value -= 1;
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
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #ff5600, #ff7838);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-icon .icon {
  font-size: 18px;
  color: #ffffff;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.history-title {
  font-size: 18px;
  font-weight: 600;
  color: #111111;
  margin: 0;
}

.history-count {
  font-size: 13px;
  color: #9c9fa5;
  margin: 0;
}

.search-input {
  width: 220px;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.search-input:focus-within {
  box-shadow: 0 0 0 3px rgba(255, 86, 0, 0.1);
}

.history-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-right: 4px;
}

.history-list::-webkit-scrollbar {
  width: 6px;
}

.history-list::-webkit-scrollbar-track {
  background: #f5f5f5;
  border-radius: 3px;
}

.history-list::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.history-list::-webkit-scrollbar-thumb:hover {
  background: #c0c4cc;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  background: #fafafa;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.history-item:hover {
  background: #f5f1ec;
  transform: translateX(4px);
}

.history-item.active {
  background: rgba(255, 86, 0, 0.06);
  border-color: rgba(255, 86, 0, 0.3);
}

.item-avatar {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #f5f1ec, #ebe7e1);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.item-avatar .avatar-icon {
  font-size: 20px;
  color: #ff5600;
}

.item-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.name-input {
  flex: 1;
  max-width: 200px;
  border-radius: 6px;
}

.item-name {
  font-size: 14px;
  font-weight: 600;
  color: #111111;
  flex-shrink: 0;
}

.item-time {
  font-size: 12px;
  color: #9c9fa5;
  flex-shrink: 0;
}

.item-text {
  font-size: 13px;
  color: #626260;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-actions {
  opacity: 0;
  transition: opacity 0.3s ease;
  display: flex;
  gap: 6px;
}

.history-item:hover .item-actions {
  opacity: 1;
}

.action-btn {
  border-radius: 8px;
  padding: 6px 12px;
}

.edit-btn {
  background: #f5f1ec;
  color: #626260;
  border-color: transparent;
}

.edit-btn:hover {
  background: #ebe7e1;
}

.delete-btn {
  background: rgba(245, 108, 108, 0.1);
  border-color: transparent;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 60px 40px;
}

.empty-icon-wrapper {
  width: 80px;
  height: 80px;
  background: #f5f1ec;
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-icon {
  font-size: 40px;
  color: #d3cec6;
}

.empty-title {
  font-size: 16px;
  font-weight: 500;
  color: #111111;
  margin: 0;
}

.empty-subtitle {
  font-size: 14px;
  color: #9c9fa5;
  margin: 0;
}

.pagination-wrapper {
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}

.pagination {
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .search-input {
    width: 150px;
  }

  .item-actions {
    opacity: 1;
  }

  .history-item:hover {
    transform: none;
  }

  .pagination {
    justify-content: center;
  }
}
</style>
