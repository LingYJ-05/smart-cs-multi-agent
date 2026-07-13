<template>
  <div class="metrics-container">
    <div class="metrics-header">
      <h3 class="metrics-title">系统指标</h3>
      <el-button size="small" @click="handleRefresh">
        <Refresh class="refresh-icon" />
        刷新
      </el-button>
    </div>
    <div class="metrics-grid">
      <div v-for="metric in metrics" :key="metric.label" class="metric-card">
        <div class="metric-icon-wrapper" :style="{ background: metric.color }">
          <component :is="metric.icon" class="metric-icon" />
        </div>
        <div class="metric-content">
          <span class="metric-value">{{ metric.value }}</span>
          <span class="metric-label">{{ metric.label }}</span>
        </div>
      </div>
    </div>
    <div class="recent-calls">
      <h4 class="recent-title">最近工具调用</h4>
      <a href="#" class="view-all">查看全部</a>
      <div class="calls-list">
        <div
          v-for="(call, index) in recentCalls"
          :key="index"
          class="call-item"
        >
          <div class="call-dot" :style="{ background: call.color }"></div>
          <span class="call-name">{{ call.name }}</span>
          <span class="call-time">{{ call.time }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, markRaw } from "vue";
import {
  ChatRound,
  Setting,
  Lock,
  Clock,
  Refresh,
} from "@element-plus/icons-vue";

interface MetricWithIcon {
  label: string;
  value: string;
  icon: typeof ChatRound;
  color: string;
}

const metrics = ref<MetricWithIcon[]>([
  {
    label: "今日会话数",
    value: "128",
    icon: markRaw(ChatRound),
    color: "linear-gradient(135deg, #65b5ff, #4a9eff)",
  },
  {
    label: "今日工具调用",
    value: "356",
    icon: markRaw(Setting),
    color: "linear-gradient(135deg, #ff5600, #ff7838)",
  },
  {
    label: "合规通过率",
    value: "98.6%",
    icon: markRaw(Lock),
    color: "linear-gradient(135deg, #0bdf50, #0ac747)",
  },
  {
    label: "平均响应时间",
    value: "1.2s",
    icon: markRaw(Clock),
    color: "linear-gradient(135deg, #b3e01c, #a0c918)",
  },
]);

const recentCalls = ref([
  { name: "产品查询", time: "15:30:20", color: "#65b5ff" },
  { name: "账户查询", time: "15:29:58", color: "#ff5600" },
  { name: "政策解读", time: "15:29:31", color: "#0bdf50" },
  { name: "计算工具", time: "15:28:45", color: "#b3e01c" },
  { name: "产品查询", time: "15:28:12", color: "#65b5ff" },
]);

const handleRefresh = () => {
  metrics.value = metrics.value.map((metric) => ({
    ...metric,
    value:
      typeof metric.value === "string" && metric.value.includes("%")
        ? `${(98 + Math.random() * 2).toFixed(1)}%`
        : typeof metric.value === "string" && metric.value.includes("s")
          ? `${(1 + Math.random()).toFixed(1)}s`
          : String(Math.floor(100 + Math.random() * 200)),
  }));
};
</script>

<style scoped>
.metrics-container {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.metrics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.metrics-title {
  font-size: 16px;
  font-weight: 600;
  color: #111111;
  margin: 0;
}

.refresh-icon {
  font-size: 14px;
  margin-right: 4px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: #fafaf9;
  border-radius: 8px;
  overflow: hidden;
}

.metric-icon-wrapper {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.metric-icon {
  font-size: 16px;
  color: #ffffff;
}

.metric-icon svg {
  width: 16px !important;
  height: 16px !important;
}

.metric-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.metric-value {
  font-size: 18px;
  font-weight: 600;
  color: #111111;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.metric-label {
  font-size: 11px;
  color: #626260;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.recent-calls {
  border-top: 1px solid #ebe7e1;
  padding-top: 16px;
}

.recent-title {
  font-size: 14px;
  font-weight: 500;
  color: #111111;
  margin: 0;
  display: inline-block;
  margin-right: 8px;
}

.view-all {
  font-size: 13px;
  color: #ff5600;
  text-decoration: none;
}

.view-all:hover {
  text-decoration: underline;
}

.calls-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
}

.call-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.call-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.call-name {
  flex: 1;
  font-size: 13px;
  color: #111111;
}

.call-time {
  font-size: 12px;
  color: #9c9fa5;
}

@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
