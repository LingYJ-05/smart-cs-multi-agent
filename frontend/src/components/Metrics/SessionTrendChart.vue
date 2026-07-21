<template>
  <div class="chart-card">
    <div class="chart-header">
      <h3 class="chart-title">会话趋势</h3>
      <el-select v-model="timeRange" size="small" style="width: 120px">
        <el-option label="今日" :value="0" />
        <el-option label="本周" :value="1" />
        <el-option label="本月" :value="2" />
      </el-select>
    </div>
    <div class="chart-content">
      <div class="bar-chart">
        <div v-for="(item, index) in trendData" :key="index" class="bar-item">
          <div class="bar-wrapper">
            <div class="bar" :style="{ height: (item.value / maxValue * 100) + '%' }"></div>
          </div>
          <span class="bar-label">{{ item.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";

interface TrendItem {
  label: string;
  value: number;
}

const props = defineProps<{
  trendData: TrendItem[];
}>();

const timeRange = ref(0);

const maxValue = computed(() => {
  return Math.max(...props.trendData.map((s) => s.value), 1);
});
</script>

<style scoped>
.chart-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #111111;
  margin: 0;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  height: 200px;
  padding-top: 20px;
}

.bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.bar-wrapper {
  width: 32px;
  height: 160px;
  background: #f5f1ec;
  border-radius: 8px;
  display: flex;
  align-items: flex-end;
  overflow: hidden;
}

.bar {
  width: 100%;
  background: linear-gradient(180deg, #65b5ff, #4a9eff);
  border-radius: 8px;
  transition: height 0.5s ease;
  min-height: 4px;
}

.bar-label {
  font-size: 12px;
  color: #626260;
}
</style>