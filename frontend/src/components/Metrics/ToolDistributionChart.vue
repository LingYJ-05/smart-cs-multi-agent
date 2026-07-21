<template>
  <div class="chart-card">
    <div class="chart-header">
      <h3 class="chart-title">工具调用分布</h3>
    </div>
    <div class="chart-content">
      <div class="pie-chart">
        <svg viewBox="0 0 100 100" class="pie-svg">
          <circle
            v-for="(slice, index) in pieData"
            :key="index"
            :cx="50"
            :cy="50"
            :r="40"
            :fill="slice.color"
            :stroke="slice.color"
            :stroke-width="20"
            :stroke-dasharray="slice.dashArray"
            :stroke-dashoffset="slice.offset"
            class="pie-slice"
          />
        </svg>
        <div class="pie-legend">
          <div v-for="(item, index) in pieData" :key="index" class="legend-item">
            <span class="legend-color" :style="{ background: item.color }"></span>
            <span class="legend-label">{{ item.name }}</span>
            <span class="legend-value">{{ item.percent }}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface ToolDistributionItem {
  name: string;
  percent: number;
  color: string;
}

interface PieSlice extends ToolDistributionItem {
  dashArray: string;
  offset: number;
}

const props = defineProps<{
  distributionData: ToolDistributionItem[];
}>();

const pieData = computed<PieSlice[]>(() => {
  let offset = 0;
  return props.distributionData.map((tool) => {
    const dashArray = `${tool.percent * 2.51} 251`;
    const currentOffset = offset;
    offset -= tool.percent * 2.51;
    return { ...tool, dashArray, offset: currentOffset };
  });
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

.pie-chart {
  display: flex;
  align-items: center;
  gap: 32px;
  justify-content: center;
}

.pie-svg {
  width: 160px;
  height: 160px;
  transform: rotate(-90deg);
}

.pie-slice {
  transition: opacity 0.2s ease;
}

.pie-slice:hover {
  opacity: 0.7;
}

.pie-legend {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.legend-label {
  flex: 1;
  font-size: 14px;
  color: #111111;
}

.legend-value {
  font-size: 14px;
  font-weight: 600;
  color: #626260;
}
</style>