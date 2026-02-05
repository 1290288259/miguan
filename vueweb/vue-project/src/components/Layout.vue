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
        <el-menu-item 
          v-for="item in visibleMenuItems" 
          :key="item.path" 
          :index="item.path"
        >
          <el-icon>
            <component :is="item.icon" />
          </el-icon>
          <span>{{ item.title }}</span>
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
const userStore = useUserStore()

// 菜单配置
const menuItems = [
  { path: '/', title: '系统首页', icon: House },
  { path: '/log-query', title: '日志查询', icon: Document },
  { path: '/match-rule-management', title: '匹配规则管理', icon: Operation },
  { path: '/honeypot-management', title: '蜜罐管理', icon: Monitor },
  { path: '/malicious-ip-management', title: '恶意IP管理', icon: Warning },
  { path: '/ai-config-management', title: 'AI模型配置', icon: Cpu }
]

// 计算可见的菜单项
const visibleMenuItems = computed(() => {
  const user = userStore.user.value
  
  // 如果没有用户信息，默认只显示首页（或者不显示，视需求而定，这里假设至少显示首页）
  if (!user) return menuItems.filter(item => item.path === '/')
  
  // 管理员(role=1)拥有所有权限，但为了统一逻辑，最好也基于permissions判断
  // 如果初始化脚本已经为管理员添加了所有权限，那么下面的逻辑对管理员也适用
  // 如果想要硬编码管理员权限作为兜底，可以这样：
  if (user.role === 1) return menuItems
  
  // 获取用户拥有的权限路径列表
  const permissions = user.permissions || []
  const allowedPaths = permissions.map((p: any) => p.path)
  
  // 过滤出用户有权限访问的菜单项
  return menuItems.filter(item => allowedPaths.includes(item.path))
})

// 侧边栏折叠状态
const isCollapse = ref(false)

// 当前激活的菜单项
const activeMenu = computed(() => {
  const path = route.path
  // 如果是仪表盘子页面，保持系统首页高亮
  if (['/overview', '/trend', '/types', '/map'].some(p => path.startsWith(p))) {
    return '/'
  }
  return path
})

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