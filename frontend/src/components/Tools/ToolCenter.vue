<template>
  <div class="tool-center">
    <div class="tool-header">
      <h3 class="tool-title">工具中心</h3>
      <a href="#" class="view-all">查看全部</a>
    </div>
    <div class="tool-grid">
      <div
        v-for="tool in tools"
        :key="tool.name"
        class="tool-card"
        :class="{ disabled: !tool.available }"
      >
        <div class="tool-icon-wrapper">
          <component :is="tool.icon" class="tool-icon" />
        </div>
        <div class="tool-info">
          <h4 class="tool-name">{{ tool.name }}</h4>
          <p class="tool-description">{{ tool.description }}</p>
        </div>
        <el-tag
          :type="tool.available ? 'success' : 'warning'"
          size="small"
          class="tool-status"
        >
          {{ tool.available ? "可用" : "维护中" }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, markRaw } from "vue";
import { DataBoard, User, Files, DataAnalysis } from "@element-plus/icons-vue";

interface ToolWithIcon {
  name: string;
  description: string;
  available: boolean;
  icon: typeof DataBoard;
}

const tools = ref<ToolWithIcon[]>([
  {
    name: "产品查询",
    description: "查询产品信息、收益率等",
    available: true,
    icon: markRaw(DataBoard),
  },
  {
    name: "账户查询",
    description: "查询账户信息、余额等",
    available: true,
    icon: markRaw(User),
  },
  {
    name: "政策解读",
    description: "解读相关政策和规则",
    available: true,
    icon: markRaw(Files),
  },
  {
    name: "计算工具",
    description: "理财计算、收益计算等",
    available: true,
    icon: markRaw(DataAnalysis),
  },
]);
</script>

<style scoped>
.tool-center {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.tool-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.tool-title {
  font-size: 16px;
  font-weight: 600;
  color: #111111;
  margin: 0;
}

.view-all {
  font-size: 13px;
  color: #ff5600;
  text-decoration: none;
}

.view-all:hover {
  text-decoration: underline;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.tool-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #fafaf9;
  border-radius: 10px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.tool-card:hover:not(.disabled) {
  background: #f5f1ec;
  transform: translateY(-2px);
}

.tool-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.tool-icon-wrapper {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #ff5600, #ff7838);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tool-icon {
  font-size: 20px;
  color: #ffffff;
}

.tool-info {
  flex: 1;
  min-width: 0;
}

.tool-name {
  font-size: 14px;
  font-weight: 500;
  color: #111111;
  margin: 0 0 4px;
}

.tool-description {
  font-size: 12px;
  color: #626260;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tool-status {
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .tool-grid {
    grid-template-columns: 1fr;
  }
}
</style>
