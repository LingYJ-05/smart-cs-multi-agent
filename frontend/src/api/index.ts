import axios from "axios";
import { ElMessage } from "element-plus";
import type {
  ChatRequest,
  ChatResponse,
  Tool,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  ApiResponse,
} from "@/types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => {
    const data = response.data as ApiResponse;

    if (data.code === 200) {
      console.log("[API成功]", response.config.url, data.message);
      return data.data;
    } else {
      console.error("[API失败]", response.config.url, data);
      ElMessage.error(data.message);
      return Promise.reject(new Error(data.message));
    }
  },
  (error) => {
    if (error.response) {
      const responseData = error.response.data as ApiResponse;
      const message = responseData.message || "请求失败";

      console.error(
        "[API错误]",
        error.config?.url,
        error.response.status,
        message,
      );

      if (error.response.status === 401) {
        const requestUrl = error.config?.url || "";
        if (!requestUrl.includes("/api/login")) {
          localStorage.removeItem("token");
          localStorage.removeItem("user");
          ElMessage.error("登录已过期，请重新登录");
          window.location.href = "/";
        } else {
          ElMessage.error(message);
        }
      } else {
        ElMessage.error(message);
      }
    } else if (error.request) {
      console.error("[API网络错误]", error.config?.url);
      ElMessage.error("网络连接失败，请检查网络");
    } else {
      console.error("[API请求错误]", error.message);
      ElMessage.error(error.message || "请求出错");
    }

    return Promise.reject(error);
  },
);

export const chatApi = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    return api.post("/api/chat", request);
  },
};

export const toolApi = {
  listTools: async (): Promise<{ tools: Tool[] }> => {
    return api.get("/api/tools");
  },
};

export const authApi = {
  login: async (request: LoginRequest): Promise<LoginResponse> => {
    return api.post("/api/login", request);
  },
  register: async (request: RegisterRequest): Promise<LoginResponse> => {
    return api.post("/api/register", request);
  },
  getCaptcha: async (): Promise<{ captchaId: string; imageUrl: string }> => {
    const timestamp = Date.now();
    const data = await api.get(`/api/captcha?${timestamp}`);
    const result = data as any;
    return {
      captchaId: result.captcha_id || "",
      imageUrl: result.image || "",
    };
  },
};

export const metricsApi = {
  getMetrics: async () => {
    return api.get("/api/metrics");
  },
};

export const historyApi = {
  getHistory: async (sessionId: string) => {
    return api.get(`/api/history/${sessionId}`);
  },
  getChatHistory: async (params?: { user_id?: string; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.user_id) query.set("user_id", params.user_id);
    if (params?.limit) query.set("limit", params.limit.toString());
    return api.get(`/api/chat-history?${query.toString()}`);
  },
};

export const sessionApi = {
  listSessions: async (user_id?: string) => {
    const query = new URLSearchParams();
    if (user_id) query.set("user_id", user_id);
    return api.get(`/api/chat-sessions?${query.toString()}`);
  },
  updateSession: async (session_id: string, data: { name: string }) => {
    return api.put(`/api/chat-sessions/${session_id}`, data);
  },
  deleteSession: async (session_id: string) => {
    return api.delete(`/api/chat-sessions/${session_id}`);
  },
};

export default api;
