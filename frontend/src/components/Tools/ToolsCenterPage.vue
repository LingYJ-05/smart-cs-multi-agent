<template>
  <div class="tools-page">
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">工具中心</h2>
        <p class="page-subtitle">管理和监控所有可用工具及其调用情况</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="refreshData">
          <Refresh class="btn-icon" />
          刷新数据
        </el-button>
      </div>
    </div>

    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon tools">
          <Setting class="icon" />
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ tools.length }}</span>
          <span class="stat-label">可用工具</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon calls">
          <TrendCharts class="icon" />
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ totalCalls }}</span>
          <span class="stat-label">今日调用</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon success">
          <CircleCheck class="icon" />
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ successRate }}%</span>
          <span class="stat-label">成功率</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon avg-time">
          <Clock class="icon" />
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ avgDuration }}ms</span>
          <span class="stat-label">平均耗时</span>
        </div>
      </div>
    </div>

    <div class="content-grid">
      <div class="tools-section">
        <div class="section-header">
          <h3 class="section-title">工具列表</h3>
          <el-select
            v-model="filterStatus"
            placeholder="状态筛选"
            size="small"
            style="width: 120px"
          >
            <el-option label="全部" :value="''" />
            <el-option label="可用" :value="true" />
            <el-option label="维护中" :value="false" />
          </el-select>
        </div>
        <div class="tools-grid">
          <div
            v-for="tool in filteredTools"
            :key="tool.id"
            class="tool-card"
            :class="{ disabled: !tool.available }"
            @click="handleToolClick(tool)"
          >
            <div class="tool-icon-wrapper" :class="tool.icon">
              <component :is="getToolIcon(tool.icon)" class="tool-icon" />
            </div>
            <div class="tool-info">
              <h4 class="tool-name">{{ tool.name }}</h4>
              <p class="tool-description">{{ tool.description }}</p>
              <div class="tool-meta">
                <span class="tool-count"
                  >调用 {{ getToolCallCount(tool.name) }} 次</span
                >
              </div>
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

      <div class="logs-section">
        <div class="section-header">
          <h3 class="section-title">最近调用记录</h3>
          <el-button size="small" text @click="showAllLogs = true"
            >查看全部</el-button
          >
        </div>
        <div class="logs-list">
          <div
            v-for="log in recentLogs"
            :key="log.id"
            class="log-item"
            :class="{ success: log.success, failed: !log.success }"
          >
            <div class="log-status-dot"></div>
            <div class="log-content">
              <div class="log-header">
                <span class="log-tool-name">{{ log.tool_name }}</span>
                <span class="log-time">{{ formatTime(log.created_at) }}</span>
              </div>
              <div class="log-meta">
                <span class="log-session"
                  >会话: {{ log.session_id?.slice(0, 8) }}...</span
                >
                <span class="log-duration">{{ log.duration_ms }}ms</span>
              </div>
            </div>
          </div>
          <div v-if="recentLogs.length === 0" class="empty-logs">
            <Document class="empty-icon" />
            <p>暂无调用记录</p>
          </div>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="showAllLogs"
      title="工具调用日志"
      width="900px"
      :close-on-click-modal="true"
    >
      <div class="logs-filter-bar">
        <el-input
          v-model="filterToolName"
          placeholder="按工具名称搜索"
          size="small"
          style="width: 200px"
          prefix-icon="Search"
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
        <el-input
          v-model="filterSession"
          placeholder="会话ID"
          size="small"
          style="width: 150px; margin-left: 12px"
        />
        <el-button size="small" type="primary" @click="loadLogs">
          查询
        </el-button>
      </div>
      <el-table :data="allLogs" border size="small" class="logs-table">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="tool_name" label="工具名称" width="120" />
        <el-table-column
          prop="session_id"
          label="会话ID"
          width="180"
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
      <div class="logs-pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadLogs"
          @current-change="loadLogs"
        />
      </div>

      <el-dialog v-model="showDetailDialog" title="日志详情" width="700px">
        <el-form :model="currentLog" label-width="100px" size="small">
          <el-form-item label="工具名称">
            <el-tag type="info">{{ currentLog.tool_name }}</el-tag>
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
          <el-form-item label="调用状态">
            <el-tag
              :type="currentLog.success ? 'success' : 'danger'"
              size="small"
            >
              {{ currentLog.success ? "成功" : "失败" }}
            </el-tag>
          </el-form-item>
          <el-form-item label="调用耗时">
            {{ currentLog.duration_ms }} ms
          </el-form-item>
          <el-form-item label="调用时间">
            {{ currentLog.created_at }}
          </el-form-item>
        </el-form>
      </el-dialog>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, markRaw, onMounted } from "vue";
import {
  Setting,
  Refresh,
  TrendCharts,
  CircleCheck,
  Clock,
  DataBoard,
  User,
  Files,
  DataAnalysis,
  Document,
} from "@element-plus/icons-vue";
import { toolApi, toolCallLogApi } from "@/api";
import type { ToolCallLog } from "@/types";

interface ToolWithIcon {
  id: number;
  name: string;
  description: string;
  icon: string;
  available: boolean;
}

const tools = ref<ToolWithIcon[]>([]);
const allLogs = ref<ToolCallLog[]>([]);
const showAllLogs = ref(false);
const showDetailDialog = ref(false);
const filterStatus = ref<boolean | "">("");
const filterToolName = ref("");
const filterSuccess = ref<boolean | "">("");
const filterSession = ref("");
const currentPage = ref(1);
const pageSize = ref(20);
const total = ref(0);

const currentLog = ref<ToolCallLog>({
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

const iconMap: Record<string, any> = {
  DataBoard,
  User,
  Files,
  DataAnalysis,
};

const getToolIcon = (iconName: string) => {
  return markRaw(iconMap[iconName] || DataBoard);
};

const filteredTools = computed(() => {
  if (filterStatus.value === "") return tools.value;
  return tools.value.filter((t) => t.available === filterStatus.value);
});

const recentLogs = computed(() => {
  return allLogs.value.slice(0, 10);
});

const totalCalls = computed(() => {
  return allLogs.value.length;
});

const successRate = computed(() => {
  if (allLogs.value.length === 0) return 0;
  const successCount = allLogs.value.filter((l) => l.success).length;
  return Math.round((successCount / allLogs.value.length) * 100);
});

const avgDuration = computed(() => {
  if (allLogs.value.length === 0) return 0;
  const total = allLogs.value.reduce((sum, l) => sum + (l.duration_ms || 0), 0);
  return Math.round(total / allLogs.value.length);
});

const getToolCallCount = (toolName: string) => {
  return allLogs.value.filter((l) => l.tool_name === toolName).length;
};

const formatTime = (dateStr: string) => {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  return date.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
};

const loadTools = async () => {
  try {
    const data = await toolApi.listTools();
    const list = data as any;
    const toolList = Array.isArray(list) ? list : list.tools || [];
    tools.value = toolList.map((tool: any) => ({
      id: tool.id,
      name: tool.name,
      description: tool.description,
      icon: tool.icon,
      available: tool.available,
    }));
  } catch (error) {
    console.error("加载工具列表失败:", error);
    tools.value = [];
  }
};

const loadLogs = async () => {
  try {
    const params: any = {
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value,
    };
    if (filterToolName.value) params.tool_name = filterToolName.value;
    if (filterSuccess.value !== "") params.success = filterSuccess.value;
    if (filterSession.value) params.session_id = filterSession.value;
    const data = await toolCallLogApi.getLogs(params);
    const result = data as any;
    if (result.data && result.total !== undefined) {
      allLogs.value = result.data;
      total.value = result.total;
    } else if (Array.isArray(result)) {
      allLogs.value = result;
      total.value = result.length;
    } else {
      allLogs.value = [];
      total.value = 0;
    }
  } catch (error) {
    console.error("加载工具调用日志失败:", error);
    allLogs.value = [];
    total.value = 0;
  }
};

const handleToolClick = (tool: ToolWithIcon) => {
  filterToolName.value = tool.name;
  loadLogs();
  showAllLogs.value = true;
};

const showLogDetail = (row: ToolCallLog) => {
  currentLog.value = { ...row };
  showDetailDialog.value = true;
};

const refreshData = () => {
  loadTools();
  loadLogs();
};

onMounted(() => {
  loadTools();
  loadLogs();
});
</script>

<style scoped>
.tools-page {
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

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon.tools {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.stat-icon.calls {
  background: linear-gradient(135deg, #11998e, #38ef7d);
}

.stat-icon.success {
  background: linear-gradient(135deg, #0bdf50, #00d99d);
}

.stat-icon.avg-time {
  background: linear-gradient(135deg, #ff5600, #ff7838);
}

.stat-icon .icon {
  font-size: 22px;
  color: #ffffff;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #111111;
}

.stat-label {
  font-size: 13px;
  color: #626260;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #111111;
  margin: 0;
}

.tools-section,
.logs-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.tool-card {
  display: flex;
  flex-direction: column;
  padding: 20px;
  background: #fafaf9;
  border-radius: 12px;
  transition: all 0.2s ease;
  cursor: pointer;
  border: 2px solid transparent;
}

.tool-card:hover:not(.disabled) {
  background: #f5f1ec;
  border-color: #ff5600;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 86, 0, 0.1);
}

.tool-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.tool-icon-wrapper {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
}

.tool-icon-wrapper.DataBoard {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.tool-icon-wrapper.User {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.tool-icon-wrapper.Files {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}

.tool-icon-wrapper.DataAnalysis {
  background: linear-gradient(135deg, #43e97b, #38f9d7);
}

.tool-icon {
  font-size: 24px;
  color: #ffffff;
}

.tool-info {
  flex: 1;
}

.tool-name {
  font-size: 15px;
  font-weight: 600;
  color: #111111;
  margin: 0 0 6px;
}

.tool-description {
  font-size: 13px;
  color: #626260;
  margin: 0 0 8px;
  line-height: 1.5;
}

.tool-meta {
  display: flex;
  align-items: center;
}

.tool-count {
  font-size: 12px;
  color: #9c9fa5;
}

.tool-status {
  margin-top: 12px;
  align-self: flex-start;
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.log-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  background: #fafaf9;
  border-radius: 10px;
  border-left: 3px solid transparent;
}

.log-item.success {
  border-left-color: #0bdf50;
}

.log-item.failed {
  border-left-color: #c41c1c;
}

.log-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}

.log-item.success .log-status-dot {
  background: #0bdf50;
}

.log-item.failed .log-status-dot {
  background: #c41c1c;
}

.log-content {
  flex: 1;
  min-width: 0;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.log-tool-name {
  font-size: 14px;
  font-weight: 500;
  color: #111111;
}

.log-time {
  font-size: 12px;
  color: #9c9fa5;
}

.log-meta {
  display: flex;
  gap: 12px;
}

.log-session,
.log-duration {
  font-size: 12px;
  color: #626260;
}

.empty-logs {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  gap: 12px;
}

.empty-icon {
  font-size: 40px;
  color: #d3cec6;
}

.empty-logs p {
  font-size: 14px;
  color: #626260;
  margin: 0;
}

.logs-filter-bar {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.logs-table {
  max-height: 400px;
  overflow-y: auto;
}

.logs-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.log-content {
  max-height: 150px;
  overflow-y: auto;
  padding: 10px;
  background: #f5f5f5;
  border-radius: 6px;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}

.log-content.error {
  background: #fef2f2;
  color: #dc2626;
}

@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .tools-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
}
</style>
