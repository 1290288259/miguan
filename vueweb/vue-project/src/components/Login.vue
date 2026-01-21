<template>
  <div class="login-container">
    <el-card class="login-card">
      <h1 class="login-title">用户登录</h1>
      
      <el-form @submit.prevent="handleLogin" :model="loginForm" :rules="formRules" ref="loginFormRef">
        <!-- 用户名输入框 -->
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名（至少6位）"
            prefix-icon="User"
            @blur="validateUsername"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <!-- 密码输入框 -->
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码（至少6位）"
            prefix-icon="Lock"
            show-password
            @blur="validatePassword"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <!-- 登录按钮 -->
        <el-form-item>
          <el-button 
            type="primary" 
            class="login-button" 
            :loading="loading"
            :disabled="!isFormValid"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <!-- 错误提示 -->
      <el-alert
        v-if="loginError"
        :title="loginError"
        type="error"
        center
        show-icon
        :closable="false"
        class="login-error"
      />
      
      <!-- 注册链接 -->
      <div class="register-link">
        还没有账号？<el-link type="primary" @click="goToRegister">立即注册</el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElForm, ElMessage } from 'element-plus'
import useUserStore from '../stores/user'

// 路由实例
const router = useRouter()

// 用户状态管理store
const userStore = useUserStore()

// 表单引用
const loginFormRef = ref<InstanceType<typeof ElForm>>()

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: ''
})

// 表单验证规则
const formRules = reactive({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 6, message: '用户名不能少于6位', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码不能少于6位', trigger: 'blur' }
  ]
})

// 登录状态
const loading = ref(false)
const loginError = ref('')

// 计算表单是否有效
const isFormValid = computed(() => {
  return (
    loginForm.username.length >= 6 &&
    loginForm.password.length >= 6
  )
})

// 验证用户名
const validateUsername = () => {
  if (loginForm.username.length < 6) {
    return false
  }
  return true
}

// 验证密码
const validatePassword = () => {
  if (loginForm.password.length < 6) {
    return false
  }
  return true
}

// 处理登录
const handleLogin = async () => {
  // 表单验证
  if (!loginFormRef.value) return
  
  try {
    await loginFormRef.value.validate()
  } catch (error) {
    // 表单验证失败
    return
  }
  
  loading.value = true
  loginError.value = ''
  
  try {
    // 使用用户状态管理store进行登录
    const result = await userStore.login(loginForm.username, loginForm.password)
    
    if (result.success) {
      // 显示成功消息
      ElMessage.success('登录成功！')
      
      // 跳转到主页或其他页面
      router.push('/')
    } else {
      // 显示错误消息
      loginError.value = result.message || '登录失败，请检查用户名和密码'
    }
  } catch (error: any) {
    // 处理错误
    loginError.value = '网络错误，请稍后重试'
    console.error('登录错误:', error)
  } finally {
    loading.value = false
  }
}

// 跳转到注册页面
const goToRegister = () => {
  router.push('/register')
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  /* background-color: #f5f7fa; 移除原有背景 */
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 20px;
  /* 依赖全局科幻卡片样式 */
}

.login-title {
  text-align: center;
  margin-bottom: 30px;
  color: var(--scifi-primary-color);
  font-size: 24px;
  font-weight: bold;
  text-shadow: 0 0 10px rgba(0, 243, 255, 0.5);
}

.login-button {
  width: 100%;
  font-weight: bold;
}

.login-error {
  margin-top: 15px;
}

.register-link {
  margin-top: 20px;
  text-align: center;
  font-size: 14px;
  color: var(--scifi-text-muted);
}
</style>