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
      <span class="view-all" @click="showLogsDialog = true">查看全部</span>
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

    <el-dialog
      v-model="showLogsDialog"
      title="工具调用日志"
      width="800px"
      :close-on-click-modal="true"
    >
      <div class="logs-filter">
        <el-input
          v-model="filterToolName"
          placeholder="按工具名称搜索"
          size="small"
          style="width: 200px"
        />
        <el-select
          v-model="filterSuccess"
          placeholder="状态筛选"
          size="small"
          style="width: 120px; margin-left: 12px"
        >
          <el-option label="全部" :value="''" />
          <el-option label="成功" :value="true" />
          <el-option label="失败" :value="false" />
        </el-select>
        <el-button size="small" type="primary" @click="loadLogs">
          查询
        </el-button>
      </div>
      <el-table :data="toolLogs" border size="small" class="logs-table">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="tool_name" label="工具名称" width="120" />
        <el-table-column
          prop="session_id"
          label="会话ID"
          width="150"
          show-overflow-tooltip
        />
        <el-table-column prop="user_id" label="用户ID" width="100" />
        <el-table-column prop="success" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.success ? 'success' : 'danger'" size="small">
              {{ row.success ? "成功" : "失败" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
        <el-table-column prop="created_at" label="时间" width="160" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" @click="showLogDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-dialog v-model="showDetailDialog" title="日志详情" width="600px">
        <el-form :model="currentLog" label-width="80px" size="small">
          <el-form-item label="工具名称">
            {{ currentLog.tool_name }}
          </el-form-item>
          <el-form-item label="会话ID">
            {{ currentLog.session_id || "-" }}
          </el-form-item>
          <el-form-item label="用户ID">
            {{ currentLog.user_id || "-" }}
          </el-form-item>
          <el-form-item label="输入参数">
            <pre class="log-content">{{ currentLog.input_params || "-" }}</pre>
          </el-form-item>
          <el-form-item label="输出结果">
            <pre class="log-content">{{ currentLog.output_result || "-" }}</pre>
          </el-form-item>
          <el-form-item label="错误信息">
            <pre class="log-content error">{{
              currentLog.error_message || "-"
            }}</pre>
          </el-form-item>
          <el-form-item label="状态">
            <el-tag
              :type="currentLog.success ? 'success' : 'danger'"
              size="small"
            >
              {{ currentLog.success ? "成功" : "失败" }}
            </el-tag>
          </el-form-item>
          <el-form-item label="耗时">
            {{ currentLog.duration_ms }} ms
          </el-form-item>
          <el-form-item label="时间">
            {{ currentLog.created_at }}
          </el-form-item>
        </el-form>
      </el-dialog>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, markRaw, onMounted, reactive } from "vue";
import {
  ChatRound,
  Setting,
  Lock,
  Clock,
  Refresh,
} from "@element-plus/icons-vue";
import { metricsApi, toolCallLogApi } from "@/api";
import type { ToolCallLog } from "@/types";

interface MetricWithIcon {
  label: string;
  value: string;
  icon: typeof ChatRound;
  color: string;
}

const metrics = ref<MetricWithIcon[]>([]);
const recentCalls = ref<{ name: string; time: string; color: string }[]>([]);

const showLogsDialog = ref(false);
const showDetailDialog = ref(false);
const filterToolName = ref("");
const filterSuccess = ref<boolean | "">("");
const toolLogs = ref<ToolCallLog[]>([]);

const currentLog = reactive<ToolCallLog>({
  id: 0,
  tool_name: "",
  session_id: "",
  user_id: "",
  input_params: "",
  output_result: "",
  error_message: "",
  success: true,
  duration_ms: 0,
  created_at: "",
});

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

const loadLogs = async () => {
  try {
    const params: any = { limit: 50 };
    if (filterToolName.value) params.tool_name = filterToolName.value;
    if (filterSuccess.value !== "") params.success = filterSuccess.value;
    const data = await toolCallLogApi.getLogs(params);
    const result = data as any;
    toolLogs.value = result.data || result || [];
  } catch (error) {
    console.error("Failed to load logs:", error);
    toolLogs.value = [];
  }
};

const showLogDetail = (row: ToolCallLog) => {
  Object.assign(currentLog, row);
  showDetailDialog.value = true;
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
  cursor: pointer;
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

.logs-filter {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.logs-table {
  max-height: 400px;
  overflow-y: auto;
}

.log-content {
  max-height: 150px;
  overflow-y: auto;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}

.log-content.error {
  background: #fef2f2;
  color: #dc2626;
}

@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
