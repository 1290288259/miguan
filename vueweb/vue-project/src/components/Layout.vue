<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="250px" class="sidebar">
      <div class="logo-container">
        <h2 class="logo-title">安全管理系统</h2>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        router
      >
        <el-menu-item index="/">
          <el-icon><House /></el-icon>
          <span>系统首页</span>
        </el-menu-item>
        
        <el-sub-menu index="user">
          <template #title>
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </template>
          <el-menu-item index="/login">用户登录</el-menu-item>
          <el-menu-item index="/register">用户注册</el-menu-item>
        </el-sub-menu>
        
        <el-menu-item index="/backend-test">
          <el-icon><Connection /></el-icon>
          <span>后端测试</span>
        </el-menu-item>
        
        <el-sub-menu index="security">
          <template #title>
            <el-icon><Shield /></el-icon>
            <span>安全管理</span>
          </template>
          <el-menu-item index="/log-query">日志查询</el-menu-item>
          <el-menu-item index="/match-rule-management">匹配规则管理</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>
    
    <!-- 主内容区 -->
    <el-container>
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
              <span>{{ userStore.user?.username || '用户' }}</span>
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
  }
}
</script>

<style scoped>
.layout-container {
  height: calc(100vh - 60px); /* 减去顶部导航栏的高度 */
  width: 100vw;
  display: flex;
  flex-direction: row;
  margin: 0;
  padding: 0;
  margin-top: 60px; /* 为顶部导航栏留出空间 */
}

.sidebar {
  background-color: #304156;
  box-shadow: 2px 0 6px rgba(0, 21, 41, 0.08);
  transition: width 0.3s;
  height: 100vh;
  overflow: hidden;
  flex-shrink: 0;
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
  position: absolute;
  left: 0;
  top: 0;
  z-index: 1000;
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #2b2f3a;
  margin: 0;
  padding: 0;
}

.logo-title {
  color: #fff;
  font-size: 18px;
  margin: 0;
  padding: 0;
}

.sidebar-menu {
  border-right: none;
  height: calc(100vh - 60px);
  overflow-y: auto;
  margin: 0;
  padding: 0;
}

.header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px;
  margin-left: 250px;
}

.header-left {
  display: flex;
  align-items: center;
}

.toggle-sidebar {
  font-size: 20px;
  cursor: pointer;
  margin-right: 20px;
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
  color: #606266;
}

.user-info .el-icon {
  margin: 0 5px;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  height: calc(100vh - 120px); /* 减去顶部导航栏和header的高度 */
  overflow-y: auto;
  margin-left: 250px;
}
</style>