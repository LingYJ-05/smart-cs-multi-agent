<template>
  <div class="performance-section">
    <div class="section-header">
      <h3 class="section-title">性能指标</h3>
    </div>
    <div class="performance-grid">
      <div v-for="item in metrics" :key="item.label" class="perf-item">
        <div class="perf-header">
          <span class="perf-label">{{ item.label }}</span>
          <span class="perf-value">{{ item.value }}</span>
        </div>
        <div class="perf-bar">
          <div class="perf-bar-fill" :style="{ width: item.percentage + '%', background: item.color }"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface PerformanceMetric {
  label: string;
  value: string;
  percentage: number;
  color: string;
}

defineProps<{
  metrics: PerformanceMetric[];
}>();
</script>

<style scoped>
.performance-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
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

.performance-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.perf-item {
  padding: 16px;
  background: #fafaf9;
  border-radius: 10px;
}

.perf-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.perf-label {
  font-size: 13px;
  color: #626260;
}

.perf-value {
  font-size: 14px;
  font-weight: 600;
  color: #111111;
}

.perf-bar {
  height: 8px;
  background: #ebe7e1;
  border-radius: 4px;
  overflow: hidden;
}

.perf-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}
</style>