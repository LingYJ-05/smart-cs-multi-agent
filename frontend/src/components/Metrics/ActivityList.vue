<template>
  <div class="activity-section">
    <div class="section-header">
      <h3 class="section-title">最近活动</h3>
      <span class="view-all" @click="$emit('view-all')">查看全部</span>
    </div>
    <div class="activity-list">
      <div
        v-for="activity in activities"
        :key="activity.id"
        class="activity-item"
      >
        <div class="activity-icon" :class="activity.type">
          <component :is="getActivityIcon(activity.type)" class="icon" />
        </div>
        <div class="activity-content">
          <p class="activity-desc">{{ activity.description }}</p>
          <span class="activity-time">{{ activity.time }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { markRaw } from "vue";
import { ChatRound, Setting, Monitor } from "@element-plus/icons-vue";

export interface ActivityItem {
  id: number;
  type: string;
  description: string;
  user: string;
  time: string;
}

defineProps<{
  activities: ActivityItem[];
}>();

defineEmits<{
  (e: "view-all"): void;
}>();

const getActivityIcon = (type: string) => {
  const icons: Record<string, any> = {
    session: markRaw(ChatRound),
    tool: markRaw(Setting),
    system: markRaw(Monitor),
  };
  return icons[type] || Monitor;
};
</script>

<style scoped>
.activity-section {
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

.view-all {
  font-size: 13px;
  color: #ff5600;
  cursor: pointer;
}

.view-all:hover {
  text-decoration: underline;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  background: #fafaf9;
  border-radius: 10px;
}

.activity-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.activity-icon.session {
  background: rgba(101, 181, 255, 0.1);
}

.activity-icon.session .icon {
  color: #65b5ff;
}

.activity-icon.tool {
  background: rgba(11, 223, 80, 0.1);
}

.activity-icon.tool .icon {
  color: #0bdf50;
}

.activity-icon.system {
  background: rgba(255, 86, 0, 0.1);
}

.activity-icon.system .icon {
  color: #ff5600;
}

.activity-icon .icon {
  font-size: 16px;
}

.activity-content {
  flex: 1;
}

.activity-desc {
  font-size: 14px;
  color: #111111;
  margin: 0 0 4px;
}

.activity-time {
  font-size: 12px;
  color: #9c9fa5;
}
</style>
