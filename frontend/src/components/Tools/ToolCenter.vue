<template>
  <div class="tool-center">
    <div class="tool-header">
      <h3 class="tool-title">工具中心</h3>
      <span class="view-all" @click="showLogsDialog = true">查看全部</span>
    </div>
    <div class="tool-grid">
      <div
        v-for="tool in tools"
        :key="tool.name"
        class="tool-card"
        :class="{ disabled: !tool.available }"
        @click="handleToolClick(tool)"
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

    <el-dialog
      v-model="showLogsDialog"
      :title="
        selectedToolName ? `${selectedToolName} - 调用日志` : '工具调用日志'
      "
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
import { DataBoard, User, Files, DataAnalysis } from "@element-plus/icons-vue";
import { toolApi, toolCallLogApi } from "@/api";
import type { ToolCallLog } from "@/types";

interface ToolWithIcon {
  id: number;
  name: string;
  description: string;
  available: boolean;
  icon: typeof DataBoard;
}

const tools = ref<ToolWithIcon[]>([]);

const showLogsDialog = ref(false);
const showDetailDialog = ref(false);
const selectedToolName = ref("");
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

const iconMap: Record<string, typeof DataBoard> = {
  DataBoard,
  User,
  Files,
  DataAnalysis,
};

const loadTools = async () => {
  try {
    const data = await toolApi.listTools();
    const list = data as any;
    const toolList = Array.isArray(list) ? list : list.data || list.tools || [];
    tools.value = toolList.map((tool: any) => ({
      id: tool.id,
      name: tool.name,
      description: tool.description,
      available: tool.available,
      icon: markRaw(iconMap[tool.icon] || DataBoard),
    }));
  } catch (error) {
    console.error("加载工具列表失败:", error);
    tools.value = [];
  }
};

const handleToolClick = (tool: ToolWithIcon) => {
  selectedToolName.value = tool.name;
  filterToolName.value = tool.name;
  loadLogs();
  showLogsDialog.value = true;
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
    console.error("加载工具调用日志失败:", error);
    toolLogs.value = [];
  }
};

const showLogDetail = (row: ToolCallLog) => {
  Object.assign(currentLog, row);
  showDetailDialog.value = true;
};

onMounted(() => {
  loadTools();
});
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
  cursor: pointer;
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
  .tool-grid {
    grid-template-columns: 1fr;
  }
}
</style>
