<template>
  <div class="register-wrapper">
    <!-- 左侧品牌区域 -->
    <div class="register-side">
      <div class="brand-content">
        <div class="logo-area">
          <div class="logo-icon">
            <el-icon><Shield /></el-icon>
          </div>
          <h1>恶意流量识别与防御系统</h1>
        </div>
        <p class="subtitle">创建您的账号以开始使用</p>
        <ul class="features-list">
          <li>
            <el-icon><Check /></el-icon>
            <span>免费注册，立即体验</span>
          </li>
          <li>
            <el-icon><UserFilled /></el-icon>
            <span>个性化安全配置</span>
          </li>
          <li>
            <el-icon><Platform /></el-icon>
            <span>多平台支持与管理</span>
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
          <h2>创建账号</h2>
          <p>请填写以下信息完成注册</p>
        </div>
        
        <el-form 
          ref="registerFormRef"
          :model="registerForm"
          :rules="formRules"
          class="register-form"
          size="large"
          @submit.prevent="handleRegister"
          label-position="top"
        >
          <!-- 用户名输入框 -->
          <el-form-item prop="username" label="用户名">
            <el-input
              v-model="registerForm.username"
              placeholder="请输入用户名（至少6位）"
              prefix-icon="User"
            />
          </el-form-item>
          
          <!-- 手机号输入框 -->
          <el-form-item prop="phone" label="手机号">
            <el-input
              v-model="registerForm.phone"
              placeholder="请输入手机号"
              prefix-icon="Iphone"
            />
          </el-form-item>
          
          <!-- 邮箱输入框 -->
          <el-form-item prop="email" label="邮箱">
            <el-input
              v-model="registerForm.email"
              placeholder="请输入邮箱地址"
              prefix-icon="Message"
            />
          </el-form-item>
          
          <!-- 密码输入框 -->
          <el-form-item prop="password" label="密码">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="请输入密码（至少6位）"
              prefix-icon="Lock"
              show-password
            />
          </el-form-item>
          
          <!-- 确认密码输入框 -->
          <el-form-item prop="confirmPassword" label="确认密码">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              prefix-icon="Lock"
              show-password
            />
          </el-form-item>
          
          <!-- 注册按钮 -->
          <el-form-item style="margin-top: 30px;">
            <el-button 
              type="primary" 
              class="submit-btn" 
              :loading="loading"
              @click="handleRegister"
            >
              {{ loading ? '注册中...' : '立即注册' }}
            </el-button>
          </el-form-item>
          
          <!-- 底部链接 -->
          <div class="form-footer">
            <span>已有账号？</span>
            <el-link type="primary" :underline="false" @click="goToLogin">立即登录</el-link>
          </div>
        </el-form>
        
        <!-- 错误提示 -->
        <transition name="el-fade-in-linear">
          <el-alert
            v-if="registerError"
            :title="registerError"
            type="error"
            show-icon
            :closable="false"
            class="register-error-alert"
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
import type { FormInstance, FormRules } from 'element-plus'
import { registerUser } from '../services/auth'

// 路由实例
const router = useRouter()

// 表单引用
const registerFormRef = ref<FormInstance>()

// 注册表单数据
const registerForm = reactive({
  username: '',
  phone: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 验证确认密码
const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// 表单验证规则
const formRules = reactive<FormRules>({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 6, message: '用户名不能少于6位', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ]
})

// 注册状态
const loading = ref(false)
const registerError = ref('')

// 处理注册
const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  try {
    await registerFormRef.value.validate()
  } catch (error) {
    return
  }
  
  loading.value = true
  registerError.value = ''
  
  try {
    // 调用注册API
    const result: any = await registerUser(
      registerForm.username,
      registerForm.password,
      undefined, // role
      registerForm.phone,
      registerForm.email
    )
    
    if (result.code === 200 || result.code === 201 || result.success) {
      ElMessage.success('注册成功请登录')
      // 延迟跳转，提升体验
      setTimeout(() => {
        router.push('/login')
      }, 1500)
    } else {
      registerError.value = result.message || result.msg || '注册失败，请稍后重试'
    }
  } catch (error: any) {
    registerError.value = '网络错误，请稍后重试'
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
.register-wrapper {
  display: flex;
  height: 100%;
  width: 100%;
  background-color: #ffffff;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

/* 左侧品牌区域 */
.register-side {
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
  width: 520px; /* 稍微宽一点以容纳更多字段 */
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: -10px 0 30px rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 3;
  overflow-y: auto; /* 允许小屏幕滚动 */
}

.form-container {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  margin: auto 0; /* 垂直居中 */
}

.form-header {
  text-align: center;
  margin-bottom: 30px;
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

.register-form :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #dcdfe6 inset;
  padding: 8px 12px;
}

.register-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c0c4cc inset;
}

.register-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #409eff inset !important;
}

.register-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

.submit-btn {
  width: 100%;
  padding: 22px 0;
  font-size: 16px;
  letter-spacing: 2px;
  background: linear-gradient(90deg, #116bc5 0%, #3a8ee6 100%);
  border: none;
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

.register-error-alert {
  margin-top: 20px;
}

/* 响应式适配 */
@media (max-width: 992px) {
  .register-side {
    display: none;
  }
  
  .form-side {
    width: 100%;
    box-shadow: none;
  }
}
</style>