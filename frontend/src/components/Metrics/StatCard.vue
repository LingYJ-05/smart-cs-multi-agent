<template>
  <div class="stat-card">
    <div class="stat-header">
      <el-icon class="stat-icon" :class="iconClass">
        <component :is="icon" class="icon" />
      </el-icon>
      <span class="stat-label">{{ label }}</span>
    </div>
    <div class="stat-value-wrapper">
      <span class="stat-value">{{ value }}</span>
      <span v-if="change !== undefined" class="stat-change" :class="changeClass">
        {{ change > 0 ? "+" : "" }}{{ change }}%
      </span>
    </div>
    <div class="stat-bar">
      <div class="stat-bar-fill" :class="barClass" :style="{ width: barWidth + '%' }"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { Component } from "vue";

const props = defineProps<{
  label: string;
  value: string | number;
  icon: Component;
  iconClass?: string;
  change?: number;
  maxValue?: number;
  barClass?: string;
}>();

const changeClass = computed(() => {
  if (props.change === undefined) return "";
  return props.change >= 0 ? "positive" : "negative";
});

const barWidth = computed(() => {
  const numValue = typeof props.value === "string" ? parseFloat(props.value) : props.value;
  const max = props.maxValue || 100;
  return Math.min((numValue / max) * 100, 100);
});
</script>

<style scoped>
.stat-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.stat-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.stat-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(101, 181, 255, 0.1);
}

.stat-icon.calls {
  background: rgba(255, 86, 0, 0.1);
}

.stat-icon.success {
  background: rgba(11, 223, 80, 0.1);
}

.stat-icon.time {
  background: rgba(179, 224, 28, 0.1);
}

.stat-icon .icon {
  font-size: 16px;
  color: #65b5ff;
}

.stat-icon.calls .icon {
  color: #ff5600;
}

.stat-icon.success .icon {
  color: #0bdf50;
}

.stat-icon.time .icon {
  color: #b3e01c;
}

.stat-label {
  font-size: 13px;
  color: #626260;
}

.stat-value-wrapper {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 12px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #111111;
}

.stat-change {
  font-size: 13px;
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 4px;
}

.stat-change.positive {
  color: #0bdf50;
  background: rgba(11, 223, 80, 0.1);
}

.stat-change.negative {
  color: #c41c1c;
  background: rgba(196, 28, 28, 0.1);
}

.stat-bar {
  height: 6px;
  background: #ebe7e1;
  border-radius: 3px;
  overflow: hidden;
}

.stat-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #65b5ff, #4a9eff);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.stat-bar-fill.orange {
  background: linear-gradient(90deg, #ff5600, #ff7838);
}

.stat-bar-fill.green {
  background: linear-gradient(90deg, #0bdf50, #0ac747);
}

.stat-bar-fill.blue {
  background: linear-gradient(90deg, #b3e01c, #a0c918);
}
</style>