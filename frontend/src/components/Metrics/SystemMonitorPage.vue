<template>
  <div class="monitor-page">
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">系统监控</h2>
        <p class="page-subtitle">实时监控系统运行状态和性能指标</p>
      </div>
      <div class="header-actions">
        <el-button
          :type="isAutoRefresh ? 'primary' : 'default'"
          @click="toggleAutoRefresh"
        >
          <Refresh class="btn-icon" :class="{ spinning: isAutoRefresh }" />
          {{ isAutoRefresh ? "自动刷新中" : "手动刷新" }}
        </el-button>
        <el-button type="primary" @click="loadAllData">
          <Refresh class="btn-icon" />
          刷新数据
        </el-button>
      </div>
    </div>

    <div class="health-status-row">
      <HealthStatusCard
        :status="healthStatus.system.status"
        :status-text="healthStatus.system.statusText"
        :description="healthStatus.system.description"
        :icon="healthStatus.system.icon"
      />
      <HealthStatusCard
        :status="healthStatus.db.status"
        :status-text="healthStatus.db.statusText"
        :description="healthStatus.db.description"
        :icon="healthStatus.db.icon"
      />
      <HealthStatusCard
        :status="healthStatus.api.status"
        :status-text="healthStatus.api.statusText"
        :description="healthStatus.api.description"
        :icon="healthStatus.api.icon"
      />
    </div>

    <div class="stats-grid">
      <StatCard
        label="今日会话数"
        :value="metrics.dailySessions"
        :icon="ChatRound"
        :change="metrics.dailySessionsChange"
        :max-value="500"
      />
      <StatCard
        label="今日工具调用"
        :value="metrics.dailyToolCalls"
        :icon="Setting"
        icon-class="calls"
        :change="metrics.dailyToolCallsChange"
        :max-value="1000"
        bar-class="orange"
      />
      <StatCard
        label="合规通过率"
        :value="metrics.complianceRate"
        :icon="Lock"
        icon-class="success"
        :change="metrics.complianceRateChange"
        :max-value="100"
        bar-class="green"
      />
      <StatCard
        label="平均响应时间"
        :value="metrics.avgResponseTime"
        :icon="Clock"
        icon-class="time"
        :change="metrics.avgResponseTimeChange"
        :max-value="5"
        bar-class="blue"
      />
    </div>

    <div class="charts-row">
      <SessionTrendChart :trend-data="sessionTrend" />
      <ToolDistributionChart :distribution-data="toolDistribution" />
    </div>

    <div class="content-row">
      <ActivityList
        :activities="recentActivity"
        @view-all="showActivityDialog = true"
      />
      <PerformanceBar :metrics="performanceMetrics" />
    </div>

    <el-dialog v-model="showActivityDialog" title="活动日志" width="800px">
      <div class="activity-filter">
        <el-select
          v-model="filterActivityType"
          placeholder="类型筛选"
          size="small"
          style="width: 120px"
        >
          <el-option label="全部" :value="''" />
          <el-option label="会话" :value="'session'" />
          <el-option label="工具" :value="'tool'" />
          <el-option label="系统" :value="'system'" />
        </el-select>
      </div>
      <div class="activity-table-wrapper">
        <el-table :data="filteredActivity" border size="small">
          <el-table-column prop="type" label="类型" width="80">
            <template #default="{ row }">
              <el-tag :type="getActivityTypeTag(row.type)" size="small">
                {{ getActivityTypeName(row.type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" />
          <el-table-column prop="user" label="用户" width="100" />
          <el-table-column prop="time" label="时间" width="160" />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, markRaw, onMounted, onUnmounted } from "vue";
import {
  Refresh,
  ChatRound,
  Setting,
  Lock,
  Clock,
  CircleCheck,
} from "@element-plus/icons-vue";
import { metricsApi, toolCallLogApi, historyApi } from "@/api";
import HealthStatusCard from "./HealthStatusCard.vue";
import StatCard from "./StatCard.vue";
import SessionTrendChart from "./SessionTrendChart.vue";
import ToolDistributionChart from "./ToolDistributionChart.vue";
import ActivityList from "./ActivityList.vue";
import PerformanceBar from "./PerformanceBar.vue";
import type { ActivityItem } from "./ActivityList.vue";

interface MetricData {
  dailySessions: string;
  dailyToolCalls: string;
  complianceRate: string;
  avgResponseTime: string;
  dailySessionsChange: number;
  dailyToolCallsChange: number;
  complianceRateChange: number;
  avgResponseTimeChange: number;
}

interface PerformanceData {
  memoryUsage: number;
  cpuUsage: number;
  networkRequests: number;
  dbConnections: number;
  maxDbConnections: number;
}

const metrics = ref<MetricData>({
  dailySessions: "0",
  dailyToolCalls: "0",
  complianceRate: "0%",
  avgResponseTime: "0s",
  dailySessionsChange: 0,
  dailyToolCallsChange: 0,
  complianceRateChange: 0,
  avgResponseTimeChange: 0,
});

const performance = ref<PerformanceData>({
  memoryUsage: 45,
  cpuUsage: 32,
  networkRequests: 45,
  dbConnections: 8,
  maxDbConnections: 20,
});

const recentActivity = ref<ActivityItem[]>([]);
const allActivity = ref<ActivityItem[]>([]);
const isAutoRefresh = ref(true);
const showActivityDialog = ref(false);
const filterActivityType = ref("");
const healthCheckResult = ref<"healthy" | "unhealthy" | null>(null);
const sessionTrend = ref<{ label: string; value: number }[]>([]);
const toolDistribution = ref<
  { name: string; percent: number; color: string }[]
>([]);

let refreshInterval: ReturnType<typeof setInterval> | null = null;

const healthStatus = computed(() => {
  const status = healthCheckResult.value;
  return {
    system: {
      status:
        status === "unhealthy" ? ("error" as const) : ("healthy" as const),
      statusText: status === "unhealthy" ? "系统异常" : "系统正常",
      description: status === "unhealthy" ? "部分服务异常" : "所有服务运行正常",
      icon: markRaw(CircleCheck),
    },
    db: {
      status:
        status === "unhealthy" ? ("warning" as const) : ("healthy" as const),
      statusText: status === "unhealthy" ? "数据库异常" : "数据库正常",
      description: status === "unhealthy" ? "连接不稳定" : "连接稳定",
      icon: markRaw(CircleCheck),
    },
    api: {
      status:
        status === "unhealthy" ? ("error" as const) : ("healthy" as const),
      statusText: status === "unhealthy" ? "API服务异常" : "API服务正常",
      description: status === "unhealthy" ? "响应超时" : "响应时间正常",
      icon: markRaw(CircleCheck),
    },
  };
});

const performanceMetrics = computed(() => [
  {
    label: "内存使用",
    value: `${performance.value.memoryUsage}%`,
    percentage: performance.value.memoryUsage,
    color: performance.value.memoryUsage > 80 ? "#c41c1c" : "#65b5ff",
  },
  {
    label: "CPU使用率",
    value: `${performance.value.cpuUsage}%`,
    percentage: performance.value.cpuUsage,
    color: performance.value.cpuUsage > 80 ? "#c41c1c" : "#0bdf50",
  },
  {
    label: "网络请求",
    value: `${performance.value.networkRequests} req/s`,
    percentage: Math.min((performance.value.networkRequests / 100) * 100, 100),
    color: "#ff5600",
  },
  {
    label: "数据库连接",
    value: `${performance.value.dbConnections} / ${performance.value.maxDbConnections}`,
    percentage:
      (performance.value.dbConnections / performance.value.maxDbConnections) *
      100,
    color:
      performance.value.dbConnections > performance.value.maxDbConnections * 0.8
        ? "#c41c1c"
        : "#b3e01c",
  },
]);

const filteredActivity = computed(() => {
  if (!filterActivityType.value) return allActivity.value;
  return allActivity.value.filter((a) => a.type === filterActivityType.value);
});

const getActivityTypeTag = (type: string) => {
  const tags: Record<string, string> = {
    session: "info",
    tool: "success",
    system: "warning",
  };
  return tags[type] || "info";
};

const getActivityTypeName = (type: string) => {
  const names: Record<string, string> = {
    session: "会话",
    tool: "工具",
    system: "系统",
  };
  return names[type] || type;
};

const loadMetrics = async () => {
  try {
    const data = await metricsApi.getMetrics();
    const result = data as any;
    if (result.metrics) {
      result.metrics.forEach((m: any) => {
        switch (m.metric_type) {
          case "daily_sessions":
            metrics.value.dailySessions = m.value;
            metrics.value.dailySessionsChange = m.change || 0;
            break;
          case "daily_tool_calls":
            metrics.value.dailyToolCalls = m.value;
            metrics.value.dailyToolCallsChange = m.change || 0;
            break;
          case "compliance_rate":
            metrics.value.complianceRate = m.value;
            metrics.value.complianceRateChange = m.change || 0;
            break;
          case "avg_response_time":
            metrics.value.avgResponseTime = m.value;
            metrics.value.avgResponseTimeChange = m.change || 0;
            break;
        }
      });
    }
  } catch (error) {
    console.error("Failed to load metrics:", error);
  }
};

const loadActivity = async () => {
  try {
    const logsData = await toolCallLogApi.getLogs({ limit: 20 });
    const result = logsData as any;
    const logs = result.data || result || [];

    const logActivities: ActivityItem[] = logs.map(
      (log: any, index: number) => ({
        id: log.id || index + 1,
        type: "tool",
        description: `调用工具: ${log.tool_name} ${log.success ? "(成功)" : "(失败)"}`,
        user: log.user_id || "admin",
        time: log.created_at || "",
      }),
    );
    recentActivity.value = logActivities.slice(0, 5);
    allActivity.value = logActivities;
  } catch (error) {
    console.error("Failed to load activity:", error);
    const activities: ActivityItem[] = [
      {
        id: 1,
        type: "session",
        description: "系统初始化完成",
        user: "system",
        time: new Date().toLocaleString("zh-CN"),
      },
    ];
    recentActivity.value = activities;
    allActivity.value = activities;
  }
};

const loadSessionTrend = async () => {
  try {
    const data = await historyApi.getChatHistory({ limit: 50 });
    const result = data as any;
    const sessions = result.data || result || [];

    const hours: Record<string, number> = {};
    for (let i = 0; i < 24; i += 4) {
      hours[`${i.toString().padStart(2, "0")}:00`] = 0;
    }

    sessions.forEach((session: any) => {
      if (session.created_at) {
        const hour = session.created_at.substring(11, 5);
        const hourKey = `${hour.substring(0, 2)}:00`;
        if (hours[hourKey] !== undefined) {
          hours[hourKey]++;
        }
      }
    });

    sessionTrend.value = Object.keys(hours).map((label) => ({
      label,
      value: hours[label],
    }));
  } catch (error) {
    console.error("Failed to load session trend:", error);
    sessionTrend.value = [
      { label: "00:00", value: 0 },
      { label: "04:00", value: 0 },
      { label: "08:00", value: 0 },
      { label: "12:00", value: 0 },
      { label: "16:00", value: 0 },
      { label: "20:00", value: 0 },
      { label: "24:00", value: 0 },
    ];
  }
};

const loadToolDistribution = async () => {
  try {
    const logsData = await toolCallLogApi.getLogs({ limit: 100 });
    const result = logsData as any;
    const logs = result.data || result || [];

    const toolCounts: Record<string, number> = {};
    logs.forEach((log: any) => {
      const toolName = log.tool_name || "未知工具";
      toolCounts[toolName] = (toolCounts[toolName] || 0) + 1;
    });

    const total = Object.values(toolCounts).reduce((a, b) => a + b, 0);
    const colors = ["#65b5ff", "#ff5600", "#0bdf50", "#b3e01c", "#ff6b9d"];

    toolDistribution.value = Object.entries(toolCounts)
      .map(([name, count], index) => ({
        name,
        percent: total > 0 ? Math.round((count / total) * 100) : 0,
        color: colors[index % colors.length],
      }))
      .sort((a, b) => b.percent - a.percent);

    if (toolDistribution.value.length === 0) {
      toolDistribution.value = [
        { name: "暂无数据", percent: 100, color: "#cccccc" },
      ];
    }
  } catch (error) {
    console.error("Failed to load tool distribution:", error);
    toolDistribution.value = [
      { name: "暂无数据", percent: 100, color: "#cccccc" },
    ];
  }
};

const checkHealth = async () => {
  try {
    await fetch("/health");
    healthCheckResult.value = "healthy";
  } catch {
    healthCheckResult.value = "unhealthy";
  }
};

const loadAllData = async () => {
  await loadMetrics();
  await loadActivity();
  await loadSessionTrend();
  await loadToolDistribution();
  await checkHealth();
};

const toggleAutoRefresh = () => {
  isAutoRefresh.value = !isAutoRefresh.value;
  if (isAutoRefresh.value) startAutoRefresh();
  else stopAutoRefresh();
};

const startAutoRefresh = () => {
  if (refreshInterval) return;
  refreshInterval = setInterval(() => {
    loadMetrics();
    loadActivity();
    loadToolDistribution();
  }, 10000);
};

const stopAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
    refreshInterval = null;
  }
};

onMounted(() => {
  loadAllData();
  startAutoRefresh();
});

onUnmounted(() => {
  stopAutoRefresh();
});
</script>

<style scoped>
.monitor-page {
  padding: 24px;
  background: #f5f1ec;
  min-height: calc(100vh - 240px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
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

.btn-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.health-status-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.content-row {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 20px;
}

.activity-filter {
  margin-bottom: 16px;
}

.activity-table-wrapper {
  max-height: 400px;
  overflow-y: auto;
}

@media (max-width: 1200px) {
  .charts-row {
    grid-template-columns: 1fr;
  }
  .content-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .health-status-row {
    grid-template-columns: 1fr;
  }
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
