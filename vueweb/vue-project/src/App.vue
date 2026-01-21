<script setup lang="ts">
import { RouterView } from 'vue-router'
import Layout from './components/Layout.vue'
import AppNav from './components/AppNav.vue'
import { useRoute } from 'vue-router'
import { computed, provide, ref, watch } from 'vue'
import useUserStore from './stores/user'

const route = useRoute()
const userStore = useUserStore()

// 判断是否是登录或注册页面，这些页面不需要使用Layout
const isAuthPage = computed(() => {
  return route.path === '/login' || route.path === '/register'
})

// 用于强制重新渲染AppNav的key
const navKey = ref(0)

// 监听用户状态变化
watch(
  () => userStore.isAuthenticated.value,
  (newVal) => {
    // 用户状态变化时更新key
    console.log('App: User authentication state changed:', newVal)
    navKey.value++
  }
)

// 提供用户状态给子组件
provide('userStore', userStore)
</script>

<template>
  <!-- 所有页面都显示AppNav顶部导航栏，使用key强制重新渲染 -->
  <AppNav :key="navKey" />
  
  <!-- 登录和注册页面不使用Layout -->
  <div v-if="isAuthPage" class="auth-page">
    <RouterView />
  </div>
  
  <!-- 其他页面使用Layout布局 -->
  <Layout v-else>
    <RouterView />
  </Layout>
</template>

<style scoped>
.auth-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  margin-top: 60px; /* 为顶部导航栏留出空间 */
}
</style>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  width: 100%;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  overflow: hidden;
}

#app {
  height: 100%;
  width: 100%;
}

/* 重置Element Plus默认样式 */
.el-container {
  margin: 0 !important;
  padding: 0 !important;
}

.el-aside {
  margin: 0 !important;
  padding: 0 !important;
}

.el-header {
  margin: 0 !important;
  padding: 0 !important;
}

.el-main {
  margin: 0 !important;
  padding: 0 !important;
}
</style>
