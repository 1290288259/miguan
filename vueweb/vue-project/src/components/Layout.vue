<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '250px'" class="sidebar">
      <div class="logo-container">
        <h2 class="logo-title" v-show="!isCollapse">安全管理系统</h2>
        <h2 class="logo-title" v-show="isCollapse">安</h2>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        router
        :collapse="isCollapse"
        :collapse-transition="false"
      >
        <el-menu-item index="/">
          <el-icon><House /></el-icon>
          <span>系统首页</span>
        </el-menu-item>
        
        <el-menu-item index="/log-query">
          <el-icon><Document /></el-icon>
          <span>日志查询</span>
        </el-menu-item>

        <el-menu-item index="/match-rule-management">
          <el-icon><Operation /></el-icon>
          <span>匹配规则管理</span>
        </el-menu-item>

        <el-menu-item index="/honeypot-management">
          <el-icon><Monitor /></el-icon>
          <span>蜜罐管理</span>
        </el-menu-item>

        <el-menu-item index="/malicious-ip-management">
          <el-icon><Warning /></el-icon>
          <span>恶意IP管理</span>
        </el-menu-item>

        <el-menu-item index="/ai-config-management">
          <el-icon><Cpu /></el-icon>
          <span>AI模型配置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <!-- 主内容区 -->
    <el-container class="main-layout">
      <!-- 顶部导航栏 -->
      <el-header class="header">
        <div class="header-left">
          <el-icon class="toggle-sidebar" @click="toggleSidebar">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-for="item in breadcrumbItems" :key="item.path" :to="{ path: item.path }">
              {{ item.name }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <!-- 用户下拉菜单 -->
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><Avatar /></el-icon>
              <span>{{ userStore.user.value?.username || '用户' }}</span>
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="settings">系统设置</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <!-- 主要内容区 -->
      <el-main class="main-content">
        <slot></slot>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { House, Fold, Expand, ArrowDown, Avatar, Document, Operation, Monitor, Warning, Cpu } from '@element-plus/icons-vue'
import useUserStore from '../stores/user'

// 路由实例
const route = useRoute()
const router = useRouter()

// 用户状态管理store
const userStore = useUserStore()

// 侧边栏折叠状态
const isCollapse = ref(false)

// 当前激活的菜单项
const activeMenu = computed(() => route.path)

// 面包屑导航项
const breadcrumbItems = computed(() => {
  const items = []
  const pathArray = route.path.split('/').filter(item => item)
  
  // 根据路径生成面包屑
  if (pathArray.length > 0) {
    let currentPath = ''
    pathArray.forEach(path => {
      currentPath += `/${path}`
      
      // 映射路径到名称
      let name = path
      switch (path) {
        case 'login':
          name = '用户登录'
          break
        case 'register':
          name = '用户注册'
          break
        case 'backend-test':
          name = '后端测试'
          break
        case 'log-query':
          name = '日志查询'
          break
        case 'match-rule-management':
          name = '匹配规则管理'
          break
      }
      
      items.push({
        path: currentPath,
        name
      })
    })
  }
  
  return items
})

// 切换侧边栏
const toggleSidebar = () => {
  isCollapse.value = !isCollapse.value
}

// 处理下拉菜单命令
const handleCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      // 跳转到个人中心
      router.push('/profile')
      break
    case 'settings':
      // 跳转到系统设置
      router.push('/settings')
      break
    case 'logout':
      // 退出登录
      await userStore.logout()
      router.push('/login')
      break
  }
}
</script>

<style scoped>
.layout-container {
  height: calc(100vh - 60px); /* 减去顶部导航栏的高度 */
  width: 100%;
  display: flex;
  flex-direction: row;
  margin: 0;
  padding: 0;
  margin-top: 60px; /* 为顶部导航栏留出空间 */
}

.sidebar {
  background-color: rgba(16, 33, 65, 0.5); /* 半透明背景 */
  backdrop-filter: blur(10px);
  border-right: 1px solid var(--scifi-border-color);
  transition: width 0.3s;
  height: 100%;
  overflow: hidden;
  flex-shrink: 0;
  margin: 0 !important;
  padding: 0 !important;
  /* 移除绝对定位 */
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  border-bottom: 1px solid var(--scifi-border-color);
  margin: 0;
  padding: 0;
}

.logo-title {
  color: var(--scifi-primary-color);
  font-size: 18px;
  font-weight: bold;
  text-shadow: 0 0 5px rgba(0, 243, 255, 0.5);
  margin: 0;
  padding: 0;
}

.sidebar-menu {
  border-right: none;
  height: calc(100% - 60px); /* 减去 logo 高度 */
  overflow-y: auto;
  margin: 0;
  padding: 0;
  background-color: transparent !important;
}

.main-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.header {
  background-color: rgba(16, 33, 65, 0.5);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--scifi-border-color);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px;
  width: 100%;
  /* 移除 margin-left */
}

.header-left {
  display: flex;
  align-items: center;
  color: var(--scifi-text-color);
}

.toggle-sidebar {
  font-size: 20px;
  cursor: pointer;
  margin-right: 20px;
  color: var(--scifi-primary-color);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: var(--scifi-text-color);
}

.user-info .el-icon {
  margin: 0 5px;
}

.main-content {
  background-color: transparent; /* 让body的背景透出来 */
  padding: 20px;
  flex: 1; /* 自动填充剩余高度 */
  overflow-y: auto;
  width: 100%;
  /* 移除 margin-left */
}
</style>