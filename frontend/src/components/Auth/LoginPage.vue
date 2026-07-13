<template>
  <div class="login-container">
    <div class="login-visual">
      <div class="visual-content">
        <div class="logo-wrapper">
          <div class="logo-icon">
            <ChatRound class="bot-icon" />
          </div>
        </div>
        <h1 class="visual-title">AI 智能客服</h1>
        <p class="visual-subtitle">基于多Agent架构的智能服务系统</p>
        <div class="feature-list">
          <div class="feature-item">
            <div class="feature-icon">
              <Lock class="icon" />
            </div>
            <span class="feature-text">合规检测</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <Star class="icon" />
            </div>
            <span class="feature-text">智能意图识别</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <Timer class="icon" />
            </div>
            <span class="feature-text">实时响应</span>
          </div>
        </div>
      </div>
      <div class="visual-decoration">
        <div class="decoration-circle circle-1"></div>
        <div class="decoration-circle circle-2"></div>
        <div class="decoration-circle circle-3"></div>
      </div>
    </div>
    <div class="login-form-wrapper">
      <div class="form-container">
        <div class="form-header">
          <div class="form-logo">
            <ChatRound class="form-bot-icon" />
          </div>
          <h2 class="form-title">欢迎回来</h2>
          <p class="form-subtitle">请登录您的账号</p>
        </div>
        <el-form :model="form" :rules="rules" ref="formRef" class="login-form">
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="用户名"
              prefix-icon="User"
              :class="['custom-input', { 'input-focus': isUsernameFocus }]"
              @focus="isUsernameFocus = true"
              @blur="isUsernameFocus = false"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              prefix-icon="Lock"
              :show-password="showPassword"
              :class="['custom-input', { 'input-focus': isPasswordFocus }]"
              @focus="isPasswordFocus = true"
              @blur="isPasswordFocus = false"
            />
          </el-form-item>
          <el-form-item class="form-options">
            <el-checkbox v-model="rememberMe">记住我</el-checkbox>
            <a href="#" class="forgot-link">忘记密码?</a>
          </el-form-item>
          <el-form-item class="form-actions">
            <el-button
              type="primary"
              :loading="loading"
              @click="handleLogin"
              :class="['login-btn']"
            >
              <span v-if="!loading">登录</span>
              <span v-else>登录中...</span>
            </el-button>
          </el-form-item>
        </el-form>
        <div class="form-footer">
          <p class="footer-text">
            还没有账号?
            <a href="#" class="register-link">立即注册</a>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { ChatRound, Lock, Star, Timer } from "@element-plus/icons-vue";

const router = useRouter();
const formRef = ref();
const loading = ref(false);
const showPassword = ref(false);
const isUsernameFocus = ref(false);
const isPasswordFocus = ref(false);
const rememberMe = ref(false);

const form = reactive({
  username: "",
  password: "",
});

const rules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

const handleLogin = async () => {
  const valid = await formRef.value?.validate();
  if (!valid) return;

  loading.value = true;
  await new Promise((resolve) => setTimeout(resolve, 800));
  localStorage.setItem("token", "demo-token-12345");
  localStorage.setItem(
    "user",
    JSON.stringify({ username: form.username || "admin", role: "管理员" }),
  );
  ElMessage.success("登录成功");
  router.push("/dashboard");
  loading.value = false;
};
</script>

<style scoped>
.login-container {
  display: flex;
  min-height: 100vh;
  width: 100%;
}

.login-visual {
  flex: 1;
  background: linear-gradient(135deg, #111111 0%, #2a2a28 50%, #111111 100%);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.visual-content {
  z-index: 1;
  text-align: center;
  padding: 40px;
}

.logo-wrapper {
  margin-bottom: 32px;
}

.logo-icon {
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, #ff5600, #ff7838);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  box-shadow: 0 20px 60px rgba(255, 86, 0, 0.3);
  animation: float 6s ease-in-out infinite;
}

.bot-icon {
  font-size: 48px;
  color: #ffffff;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}

.visual-title {
  font-size: 48px;
  font-weight: 500;
  color: #ffffff;
  margin-bottom: 16px;
  letter-spacing: -2px;
}

.visual-subtitle {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 48px;
}

.feature-list {
  display: flex;
  gap: 40px;
  justify-content: center;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.feature-icon {
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.feature-icon .icon {
  font-size: 24px;
  color: #ff5600;
}

.feature-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
}

.visual-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

.decoration-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.1;
}

.circle-1 {
  width: 600px;
  height: 600px;
  background: #ff5600;
  top: -100px;
  left: -100px;
  animation: pulse 8s ease-in-out infinite;
}

.circle-2 {
  width: 400px;
  height: 400px;
  background: #65b5ff;
  bottom: -50px;
  right: 100px;
  animation: pulse 6s ease-in-out infinite 2s;
}

.circle-3 {
  width: 300px;
  height: 300px;
  background: #0bdf50;
  top: 50%;
  right: -50px;
  animation: pulse 7s ease-in-out infinite 1s;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 0.1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.2;
  }
}

.login-form-wrapper {
  width: 420px;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.form-container {
  width: 100%;
}

.form-header {
  text-align: center;
  margin-bottom: 40px;
}

.form-logo {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #111111, #2a2a28);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}

.form-bot-icon {
  font-size: 28px;
  color: #ffffff;
}

.form-title {
  font-size: 28px;
  font-weight: 500;
  color: #111111;
  margin-bottom: 8px;
}

.form-subtitle {
  font-size: 14px;
  color: #626260;
}

.login-form {
  width: 100%;
}

.custom-input {
  height: 48px;
  border-radius: 8px;
  font-size: 15px;
  transition: all 0.3s ease;
}

.custom-input input {
  font-size: 15px;
}

.custom-input.input-focus {
  box-shadow: 0 0 0 3px rgba(255, 86, 0, 0.1);
  border-color: #ff5600;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.form-options .el-checkbox {
  font-size: 14px;
  color: #626260;
}

.forgot-link {
  font-size: 14px;
  color: #ff5600;
  text-decoration: none;
}

.forgot-link:hover {
  text-decoration: underline;
}

.login-btn {
  width: 100%;
  height: 48px;
  background: #111111;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.login-btn:hover:not(:disabled) {
  background: #2a2a28;
  transform: translateY(-1px);
}

.form-footer {
  margin-top: 32px;
  text-align: center;
}

.footer-text {
  font-size: 14px;
  color: #626260;
}

.register-link {
  color: #ff5600;
  text-decoration: none;
  font-weight: 500;
}

.register-link:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
  }
  .login-visual {
    padding: 40px 20px;
  }
  .visual-title {
    font-size: 32px;
  }
  .feature-list {
    gap: 20px;
  }
  .login-form-wrapper {
    width: 100%;
    min-height: 50vh;
  }
}
</style>
