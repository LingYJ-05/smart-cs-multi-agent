import axios from 'axios'
import type { ChatRequest, ChatResponse, Tool, LoginRequest, LoginResponse } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

export const chatApi = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post('/api/chat', request)
    return response.data
  },
}

export const toolApi = {
  listTools: async (): Promise<{ tools: Tool[] }> => {
    const response = await api.get('/api/tools')
    return response.data
  },
}

export const authApi = {
  login: async (request: LoginRequest): Promise<LoginResponse> => {
    const response = await api.post('/api/login', request)
    return response.data
  },
}

export const metricsApi = {
  getMetrics: async () => {
    const response = await api.get('/api/metrics')
    return response.data
  },
}

export const historyApi = {
  getHistory: async (sessionId: string) => {
    const response = await api.get(`/api/history/${sessionId}`)
    return response.data
  },
}

export default api