<template>
  <div class="health-card" :class="status">
    <div class="health-icon">
      <component :is="icon" class="icon" />
    </div>
    <div class="health-content">
      <span class="health-status-text">{{ statusText }}</span>
      <span class="health-desc">{{ description }}</span>
    </div>
    <div class="health-indicator"></div>
  </div>
</template>

<script setup lang="ts">
import type { Component } from "vue";

defineProps<{
  status: "healthy" | "warning" | "error";
  statusText: string;
  description: string;
  icon: Component;
}>();
</script>

<style scoped>
.health-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border-left: 4px solid transparent;
}

.health-card.healthy {
  border-left-color: #0bdf50;
}

.health-card.warning {
  border-left-color: #ff5600;
}

.health-card.error {
  border-left-color: #c41c1c;
}

.health-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.health-card.healthy .health-icon {
  background: rgba(11, 223, 80, 0.1);
}

.health-card.warning .health-icon {
  background: rgba(255, 86, 0, 0.1);
}

.health-card.error .health-icon {
  background: rgba(196, 28, 28, 0.1);
}

.health-card.healthy .icon {
  color: #0bdf50;
}

.health-card.warning .icon {
  color: #ff5600;
}

.health-card.error .icon {
  color: #c41c1c;
}

.health-icon .icon {
  font-size: 24px;
}

.health-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.health-status-text {
  font-size: 16px;
  font-weight: 600;
  color: #111111;
}

.health-desc {
  font-size: 13px;
  color: #626260;
}

.health-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.health-card.healthy .health-indicator {
  background: #0bdf50;
  animation: pulse-green 2s infinite;
}

.health-card.warning .health-indicator {
  background: #ff5600;
  animation: pulse-orange 2s infinite;
}

.health-card.error .health-indicator {
  background: #c41c1c;
  animation: pulse-red 2s infinite;
}

@keyframes pulse-green {
  0%, 100% { box-shadow: 0 0 0 0 rgba(11, 223, 80, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(11, 223, 80, 0); }
}

@keyframes pulse-orange {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255, 86, 0, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(255, 86, 0, 0); }
}

@keyframes pulse-red {
  0%, 100% { box-shadow: 0 0 0 0 rgba(196, 28, 28, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(196, 28, 28, 0); }
}
</style>