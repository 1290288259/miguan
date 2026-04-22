<template>
  <div class="login-wrapper">
    <!-- 左侧品牌区域 -->
    <div class="login-side">
      <div class="brand-content">
        <div class="logo-area">
          <div class="logo-icon">
            <el-icon><Shield /></el-icon>
          </div>
          <h1>恶意流量识别与防御系统</h1>
        </div>
        <p class="subtitle">基于低交互蜜罐的高级安全防护平台</p>
        <ul class="features-list">
          <li>
            <el-icon><Aim /></el-icon>
            <span>实时流量监控与分析</span>
          </li>
          <li>
            <el-icon><Lock /></el-icon>
            <span>自动化的恶意IP封禁</span>
          </li>
          <li>
            <el-icon><DataLine /></el-icon>
            <span>可视化的安全态势感知</span>
          </li>
        </ul>
      </div>
      <!-- 装饰背景圆 -->
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
    </div>
    
    <!-- 右侧表单区域 -->
    <div class="form-side">
      <div class="form-container">
        <div class="form-header">
          <h2>欢迎登录</h2>
          <p>请输入您的账号和密码以继续</p>
        </div>
        
        <el-form 
          ref="loginFormRef"
          :model="loginForm"
          :rules="formRules"
          class="login-form"
          size="large"
          @submit.prevent="handleLogin"
        >
          <!-- 用户名输入框 -->
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              prefix-icon="User"
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          
          <!-- 密码输入框 -->
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          
          <!-- 登录按钮 -->
          <el-form-item>
            <el-button 
              type="primary" 
              class="submit-btn" 
              native-type="submit"
              :loading="loading"
              @click="handleLogin"
            >
              {{ loading ? '登录中...' : '立即登录' }}
            </el-button>
          </el-form-item>
          
          <!-- 底部链接 -->
          <div class="form-footer">
            <span>还没有账号？</span>
            <el-link type="primary" :underline="false" @click="goToRegister">立即注册</el-link>
          </div>
        </el-form>
        
        <!-- 错误提示 -->
        <transition name="el-fade-in-linear">
          <el-alert
            v-if="loginError"
            :title="loginError"
            type="error"
            show-icon
            :closable="false"
            class="login-error-alert"
          />
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
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

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  try {
    await loginFormRef.value.validate()
  } catch (error) {
    return
  }
  
  loading.value = true
  loginError.value = ''
  
  try {
    const result = await userStore.login(loginForm.username, loginForm.password)
    
    if (result.success) {
      ElMessage.success('登录成功！')
      router.push('/')
    } else {
      loginError.value = result.message || '登录失败，请检查用户名和密码'
    }
  } catch (error: any) {
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
.login-wrapper {
  display: flex;
  height: 100%;
  width: 100%;
  background-color: #ffffff;
  overflow: hidden;
  position: relative;
  z-index: 1; /* Ensure it covers body background */
}

/* 左侧品牌区域 */
.login-side {
  flex: 1;
  background: linear-gradient(135deg, #102a50 0%, #0d1b3e 100%);
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 0 80px;
  color: #ffffff;
  overflow: hidden;
}

.brand-content {
  position: relative;
  z-index: 2;
  max-width: 600px;
}

.logo-area {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
  color: #409eff;
}

.brand-content h1 {
  font-size: 32px;
  font-weight: 600;
  margin: 0;
  letter-spacing: 1px;
}

.subtitle {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 48px;
  font-weight: 300;
}

.features-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.features-list li {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.9);
}

.features-list li .el-icon {
  margin-right: 12px;
  font-size: 20px;
  color: #409eff;
  background: rgba(64, 158, 255, 0.15);
  padding: 8px;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  box-sizing: border-box;
}

/* 背景装饰 */
.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.03);
}

.circle-1 {
  width: 600px;
  height: 600px;
  top: -200px;
  right: -200px;
}

.circle-2 {
  width: 400px;
  height: 400px;
  bottom: -100px;
  left: -100px;
}

/* 右侧表单区域 */
.form-side {
  width: 480px;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: -10px 0 30px rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 3;
}

.form-container {
  width: 100%;
  max-width: 360px;
  padding: 40px;
}

.form-header {
  text-align: center;
  margin-bottom: 40px;
}

.form-header h2 {
  font-size: 28px;
  color: #303133;
  margin-bottom: 12px;
  font-weight: 600;
}

.form-header p {
  color: #909399;
  font-size: 14px;
}

.login-form :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #dcdfe6 inset;
  padding: 8px 12px;
}

.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c0c4cc inset;
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #409eff inset !important;
}

.submit-btn {
  width: 100%;
  padding: 22px 0;
  font-size: 16px;
  font-weight: 600; /* 加粗文字 */
  color: #ffffff !important; /* 强制白色，防止主题干扰 */
  letter-spacing: 2px;
  margin-top: 10px;
  background: linear-gradient(90deg, #409eff 0%, #3a8ee6 100%);
  border: none;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1); /* 添加微弱阴影增强对比度 */
}

.submit-btn:hover {
  background: linear-gradient(90deg, #66b1ff 0%, #409eff 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.form-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 14px;
  color: #606266;
}

.login-error-alert {
  margin-top: 20px;
}

/* 响应式适配 */
@media (max-width: 992px) {
  .login-side {
    display: none;
  }
  
  .form-side {
    width: 100%;
    box-shadow: none;
  }
}
</style>