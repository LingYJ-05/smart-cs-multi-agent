<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <div class="logo-container">
        <div class="logo-icon">
          <ChatRound class="bot-icon" />
        </div>
        <span class="logo-text">AI 智能客服</span>
      </div>
    </div>
    <nav class="sidebar-nav">
      <div
        v-for="item in menuItems"
        :key="item.id"
        class="nav-item"
        :class="{ active: activeMenu === item.id }"
        @click="handleNavClick(item.id)"
      >
        <component :is="item.icon" class="nav-icon" />
        <span class="nav-text">{{ item.label }}</span>
      </div>
    </nav>
    <div class="sidebar-footer">
      <div class="user-profile">
        <div class="user-avatar">
          <User class="avatar-icon" />
        </div>
        <div class="user-info">
          <span class="user-name">{{ userInfo.username }}</span>
          <span class="user-role">{{ userInfo.role }}</span>
        </div>
      </div>
      <div class="logout-btn" @click="handleLogout">
        <SwitchButton class="logout-icon" />
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import {
  ChatRound,
  ChatLineRound,
  Clock,
  Setting,
  Monitor,
  User,
  SwitchButton,
} from "@element-plus/icons-vue";

const emit = defineEmits<{
  (e: "menu-change", menuId: string): void;
}>();

const router = useRouter();
const activeMenu = ref("chat");

const menuItems = [
  { id: "chat", label: "会话聊天", icon: ChatLineRound },
  { id: "history", label: "对话历史", icon: Clock },
  { id: "tools", label: "工具中心", icon: Setting },
  { id: "monitor", label: "系统监控", icon: Monitor },
];

const userInfo = computed(() => {
  const user = localStorage.getItem("user");
  return user ? JSON.parse(user) : { username: "admin", role: "管理员" };
});

const handleNavClick = (menuId: string) => {
  activeMenu.value = menuId;
  emit("menu-change", menuId);
};

const handleLogout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  ElMessage.success("已退出登录");
  router.push("/");
};
</script>

<style scoped>
.sidebar {
  width: 240px;
  background: linear-gradient(180deg, #1a1a18 0%, #111111 100%);
  height: 100vh;
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
}

.sidebar-header {
  padding: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #ff5600, #ff7838);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bot-icon {
  font-size: 16px;
  color: #ffffff;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.nav-item.active {
  background: rgba(255, 86, 0, 0.15);
  border-left-color: #ff5600;
}

.nav-icon {
  font-size: 12px;
  width: 12px;
  height: 12px;
  color: rgba(255, 255, 255, 0.6);
  flex-shrink: 0;
}

.nav-icon svg {
  width: 12px !important;
  height: 12px !important;
}

.nav-item.active .nav-icon {
  color: #ff5600;
}

.nav-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
}

.nav-item.active .nav-text {
  color: #ffffff;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-icon {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7);
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
}

.user-role {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.logout-btn {
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.logout-btn:hover {
  background: rgba(196, 28, 28, 0.2);
}

.logout-icon {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.6);
}

@media (max-width: 768px) {
  .sidebar {
    width: 60px;
  }
  .logo-text {
    display: none;
  }
  .nav-text {
    display: none;
  }
  .user-info {
    display: none;
  }
  .nav-item {
    justify-content: center;
    padding: 14px 0;
  }
}
</style>
