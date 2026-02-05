<template>
  <nav class="app-nav">
    <div class="nav-container">
      <div class="nav-brand">
        <h1>基于低交互蜜罐的恶意流量识别和防御系统</h1>
      </div>
      
      <div class="nav-links">
        <!-- 未登录状态显示登录和注册按钮 -->
        <template v-if="!isLoggedIn">
          <router-link to="/login" class="nav-link">登录</router-link>
          <router-link to="/register" class="nav-link">注册</router-link>
        </template>
        
        <!-- 已登录状态显示退出登录按钮 -->
        <template v-else>
          <el-button type="primary" size="small" @click="router.push('/profile')" style="margin-right: 10px;">
            <el-icon><User /></el-icon>
            个人中心
          </el-button>
          <el-button type="danger" size="small" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            退出登录
          </el-button>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed, ref, inject, watchEffect } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { SwitchButton, User } from '@element-plus/icons-vue'
import useUserStore from '../stores/user'

// 路由实例
const router = useRouter()

// 直接使用 useUserStore，确保获取到的是全局单例状态
// inject 可能会因为类型或提供方式导致困惑，且此处直接使用并无不妥
const userStore = useUserStore()

// 创建一个立即响应的状态变量
const isLoggingOut = ref(false)

// Debug
watchEffect(() => {
  console.log('AppNav: isAuthenticated =', userStore.isAuthenticated.value)
})

// 判断用户是否已登录
const isLoggedIn = computed(() => {
  return userStore.isAuthenticated.value && !isLoggingOut.value
})

// 处理退出登录
const handleLogout = async () => {
  try {
    // 立即设置状态，隐藏退出按钮
    isLoggingOut.value = true
    
    await userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch (error) {
    console.error('退出登录失败:', error)
    ElMessage.error('退出登录失败')
    // 如果失败，恢复状态
    isLoggingOut.value = false
  }
}
</script>

<style scoped>
.app-nav {
  background-color: rgba(5, 11, 20, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--scifi-border-color);
  color: var(--scifi-text-color);
  padding: 0 20px;
  box-shadow: 0 2px 10px rgba(0, 243, 255, 0.1);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
}

.nav-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 0 20px;
  height: 60px;
}

.nav-brand h1 {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
  color: var(--scifi-primary-color);
  text-shadow: 0 0 10px rgba(0, 243, 255, 0.5);
  letter-spacing: 2px;
}

.nav-links {
  display: flex;
  gap: 20px;
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 4px;
  transition: background-color 0.3s;
  font-weight: 500;
}

.nav-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.nav-link.router-link-active {
  background-color: rgba(255, 255, 255, 0.2);
}
</style>