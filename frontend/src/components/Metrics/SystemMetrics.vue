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
import { ref, markRaw, onMounted } from "vue";
import {
  ChatRound,
  Setting,
  Lock,
  Clock,
  Refresh,
} from "@element-plus/icons-vue";
import { metricsApi } from "@/api";

interface MetricWithIcon {
  label: string;
  value: string;
  icon: typeof ChatRound;
  color: string;
}

const metrics = ref<MetricWithIcon[]>([]);

const recentCalls = ref<{ name: string; time: string; color: string }[]>([]);

const iconMap: Record<string, typeof ChatRound> = {
  daily_sessions: ChatRound,
  daily_tool_calls: Setting,
  compliance_rate: Lock,
  avg_response_time: Clock,
};

const colorMap: Record<string, string> = {
  daily_sessions: "linear-gradient(135deg, #65b5ff, #4a9eff)",
  daily_tool_calls: "linear-gradient(135deg, #ff5600, #ff7838)",
  compliance_rate: "linear-gradient(135deg, #0bdf50, #0ac747)",
  avg_response_time: "linear-gradient(135deg, #b3e01c, #a0c918)",
};

const loadMetrics = async () => {
  try {
    const data = await metricsApi.getMetrics();
    const result = data as any;
    metrics.value = result.metrics.map((m: any) => ({
      label: m.label,
      value: m.value,
      icon: markRaw(iconMap[m.metric_type] || ChatRound),
      color: colorMap[m.metric_type] || "#65b5ff",
    }));
    recentCalls.value = result.recent_calls.map((call: any) => ({
      name: call.name,
      time: call.time,
      color: call.success ? "#0bdf50" : "#ff5600",
    }));
  } catch {
    metrics.value = [];
    recentCalls.value = [];
  }
};

const handleRefresh = () => {
  loadMetrics();
};

onMounted(() => {
  loadMetrics();
});
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
