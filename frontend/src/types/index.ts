export interface Message {
  id: string;
  content: string;
  role: "user" | "assistant";
  timestamp: string;
  intent?: string;
  compliancePassed?: boolean;
  complianceRiskLevel?: string;
  complianceViolations?: string[];
}

export interface Tool {
  name: string;
  description: string;
  available: boolean;
}

export interface SystemMetric {
  label: string;
  value: string | number;
  icon: string;
  color?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  intent: string;
  compliance_passed: boolean;
  compliance_risk_level: string;
  compliance_violations: string[];
}

export interface ChatRequest {
  message: string;
  user_id: string;
  session_id?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  captcha_id: string;
  captcha_code: string;
  role?: string;
}

export interface LoginResponse {
  token: string;
  username: string;
  role: string;
}

export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}
