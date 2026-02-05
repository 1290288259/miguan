<template>
  <div class="register-container">
    <div class="register-card">
      <h1 class="register-title">用户注册</h1>
      
      <form @submit.prevent="handleRegister" class="register-form">
        <!-- 用户名输入框 -->
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="registerForm.username"
            type="text"
            placeholder="请输入用户名（至少6位）"
            :class="{ 'error': errors.username }"
            @blur="validateUsername"
            @keyup.enter="handleRegister"
          />
          <span v-if="errors.username" class="error-message">{{ errors.username }}</span>
        </div>
        
        <!-- 手机号输入框 -->
        <div class="form-group">
          <label for="phone">手机号</label>
          <input
            id="phone"
            v-model="registerForm.phone"
            type="tel"
            placeholder="请输入手机号"
            :class="{ 'error': errors.phone }"
            @blur="validatePhone"
            @keyup.enter="handleRegister"
          />
          <span v-if="errors.phone" class="error-message">{{ errors.phone }}</span>
        </div>
        
        <!-- 邮箱输入框 -->
        <div class="form-group">
          <label for="email">邮箱</label>
          <input
            id="email"
            v-model="registerForm.email"
            type="email"
            placeholder="请输入邮箱地址"
            :class="{ 'error': errors.email }"
            @blur="validateEmail"
            @keyup.enter="handleRegister"
          />
          <span v-if="errors.email" class="error-message">{{ errors.email }}</span>
        </div>
        
        <!-- 密码输入框 -->
        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码（至少6位）"
            :class="{ 'error': errors.password }"
            @blur="validatePassword"
            @keyup.enter="handleRegister"
          />
          <span v-if="errors.password" class="error-message">{{ errors.password }}</span>
        </div>
        
        <!-- 确认密码输入框 -->
        <div class="form-group">
          <label for="confirmPassword">确认密码</label>
          <input
            id="confirmPassword"
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            :class="{ 'error': errors.confirmPassword }"
            @blur="validateConfirmPassword"
            @keyup.enter="handleRegister"
          />
          <span v-if="errors.confirmPassword" class="error-message">{{ errors.confirmPassword }}</span>
        </div>
        
        <!-- 注册按钮 -->
        <button 
          type="submit" 
          class="register-button" 
          :disabled="loading || !isFormValid"
        >
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>
      
      <!-- 错误提示 -->
      <div v-if="registerError" class="register-error">
        {{ registerError }}
      </div>
      
      <!-- 登录链接 -->
      <div class="login-link">
        已有账号？<a @click="goToLogin" href="#">立即登录</a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { registerUser } from '../services/auth'

// 路由实例
const router = useRouter()

// 注册表单数据
const registerForm = ref({
  username: '',
  phone: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 表单验证错误
const errors = ref({
  username: '',
  phone: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 注册状态
const loading = ref(false)
const registerError = ref('')

// 计算表单是否有效
const isFormValid = computed(() => {
  return (
    registerForm.value.username.length >= 6 &&
    (!registerForm.value.phone || registerForm.value.phone.length >= 11) &&
    (!registerForm.value.email || registerForm.value.email.includes('@')) &&
    registerForm.value.password.length >= 6 &&
    registerForm.value.confirmPassword === registerForm.value.password &&
    !errors.value.username &&
    !errors.value.phone &&
    !errors.value.email &&
    !errors.value.password &&
    !errors.value.confirmPassword
  )
})

// 验证用户名
const validateUsername = () => {
  if (registerForm.value.username.length < 6) {
    errors.value.username = '用户名不能少于6位'
  } else {
    errors.value.username = ''
  }
}

// 验证手机号
const validatePhone = () => {
  if (registerForm.value.phone && registerForm.value.phone.length < 11) {
    errors.value.phone = '请输入正确的手机号'
  } else {
    errors.value.phone = ''
  }
}

// 验证邮箱
const validateEmail = () => {
  if (registerForm.value.email && !registerForm.value.email.includes('@')) {
    errors.value.email = '请输入正确的邮箱地址'
  } else {
    errors.value.email = ''
  }
}

// 验证密码
const validatePassword = () => {
  if (registerForm.value.password.length < 6) {
    errors.value.password = '密码不能少于6位'
  } else {
    errors.value.password = ''
  }
  
  // 如果确认密码已填写，则重新验证确认密码
  if (registerForm.value.confirmPassword) {
    validateConfirmPassword()
  }
}

// 验证确认密码
const validateConfirmPassword = () => {
  if (registerForm.value.confirmPassword !== registerForm.value.password) {
    errors.value.confirmPassword = '两次输入的密码不一致'
  } else {
    errors.value.confirmPassword = ''
  }
}

// 处理注册
const handleRegister = async () => {
  // 先进行表单验证
  validateUsername()
  validatePhone()
  validateEmail()
  validatePassword()
  validateConfirmPassword()
  
  // 如果表单无效，则不提交
  if (!isFormValid.value) {
    return
  }
  
  loading.value = true
  registerError.value = ''
  
  try {
    // 调用后端注册接口
    const response: any = await registerUser(
      registerForm.value.username, 
      registerForm.value.password,
      2, // 默认角色
      registerForm.value.phone,
      registerForm.value.email
    )
    
    // 注册成功处理
    if (response.code === 200 || response.code === 201) {
      // 显示成功消息
      alert('注册成功！请登录')
      
      // 跳转到登录页面
      router.push('/login')
    } else {
      // 显示错误消息
      registerError.value = response.message || '注册失败，请稍后重试'
    }
  } catch (error: any) {
    // 处理错误
    if (error.response && error.response.data) {
      registerError.value = error.response.data.message || '注册失败'
    } else {
      registerError.value = '网络错误，请稍后重试'
    }
    console.error('注册错误:', error)
  } finally {
    loading.value = false
  }
}

// 跳转到登录页面
const goToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  /* background-color: #f5f7fa; 移除原有背景 */
  padding: 20px;
}

.register-card {
  width: 100%;
  max-width: 400px;
  padding: 30px;
  background-color: var(--scifi-card-bg);
  backdrop-filter: var(--scifi-glass);
  border: 1px solid var(--scifi-border-color);
  border-radius: 8px;
  box-shadow: var(--scifi-shadow);
  color: var(--scifi-text-color);
}

.register-title {
  text-align: center;
  margin-bottom: 30px;
  color: var(--scifi-primary-color);
  font-size: 24px;
  font-weight: bold;
  text-shadow: 0 0 10px rgba(0, 243, 255, 0.5);
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 500;
  color: var(--scifi-text-color);
}

.form-group input {
  padding: 12px;
  background-color: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--scifi-border-color);
  border-radius: 4px;
  font-size: 16px;
  color: var(--scifi-text-color);
  transition: all 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: var(--scifi-primary-color);
  box-shadow: 0 0 10px rgba(0, 243, 255, 0.3);
}

.form-group input.error {
  border-color: #f56c6c;
}

.error-message {
  color: #f56c6c;
  font-size: 14px;
}

.register-button {
  padding: 12px;
  background-color: rgba(0, 243, 255, 0.1);
  color: var(--scifi-primary-color);
  border: 1px solid var(--scifi-primary-color);
  border-radius: 4px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 10px;
  box-shadow: 0 0 5px rgba(0, 243, 255, 0.2);
}

.register-button:hover:not(:disabled) {
  background-color: var(--scifi-primary-color);
  color: #000;
  box-shadow: 0 0 15px rgba(0, 243, 255, 0.6);
}

.register-button:disabled {
  background-color: rgba(255, 255, 255, 0.1);
  border-color: #666;
  color: #666;
  cursor: not-allowed;
}

.register-error {
  margin-top: 15px;
  padding: 10px;
  background-color: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
  border: 1px solid #f56c6c;
  border-radius: 4px;
  text-align: center;
}

.login-link {
  margin-top: 20px;
  text-align: center;
  color: var(--scifi-text-muted);
}

.login-link a {
  color: var(--scifi-primary-color);
  text-decoration: none;
  cursor: pointer;
}

.login-link a:hover {
  text-decoration: underline;
  text-shadow: 0 0 5px rgba(0, 243, 255, 0.5);
}
</style>