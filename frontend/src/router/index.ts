import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import LoginPage from '@/components/Auth/LoginPage.vue'
import Dashboard from '@/components/Dashboard/Dashboard.vue'
import ChatSessionPage from '@/components/Chat/ChatSessionPage.vue'
import HistoryPage from '@/components/History/HistoryPage.vue'
import ToolsCenterPage from '@/components/Tools/ToolsCenterPage.vue'
import SystemMonitorPage from '@/components/Metrics/SystemMonitorPage.vue'
import KnowledgeBasePage from '@/components/Knowledge/KnowledgeBasePage.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Login',
    component: LoginPage,
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    redirect: '/chat',
    children: [
      {
        path: '/chat',
        name: 'Chat',
        component: ChatSessionPage,
      },
      {
        path: '/history',
        name: 'History',
        component: HistoryPage,
      },
      {
        path: '/tools',
        name: 'Tools',
        component: ToolsCenterPage,
      },
      {
        path: '/knowledge',
        name: 'Knowledge',
        component: KnowledgeBasePage,
      },
      {
        path: '/monitor',
        name: 'Monitor',
        component: SystemMonitorPage,
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
