<template>
  <div class="dashboard">
    <Sidebar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import Sidebar from "@/components/Layout/Sidebar.vue";
</script>

<style scoped>
.dashboard {
  display: flex;
  min-height: 100vh;
  background: #f5f1ec;
}

.main-content {
  flex: 1;
  margin-left: 240px;
  padding: 0;
  min-height: 100vh;
}

@media (max-width: 768px) {
  .main-content {
    margin-left: 60px;
  }
}
</style>
