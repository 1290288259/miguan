import { createRouter, createWebHistory, RouterView } from 'vue-router'
import useUserStore from '../stores/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: RouterView, // 添加这一行，让父路由渲染一个 router-view
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          // 可视化大屏页面
          component: () => import('../views/Dashboard.vue'),
        },
        {
          path: 'test-auth',
          name: 'test-auth',
          // 用户认证测试页面
          component: () => import('../components/TestAuth.vue'),
        },
        {
          path: 'backend-test',
          name: 'backend-test',
          // 后端连接测试页面
          component: () => import('../components/BackendTest.vue'),
        },
        {
          path: 'log-query',
          name: 'log-query',
          // 日志查询页面
          component: () => import('../views/LogQuery.vue'),
        },
        {
          path: 'match-rule-management',
          name: 'match-rule-management',
          // 匹配规则管理页面
          component: () => import('../views/MatchRuleManagement.vue'),
        },
        {
          path: 'honeypot-management',
          name: 'honeypot-management',
          // 蜜罐管理页面
          component: () => import('../views/HoneypotManagement.vue'),
        },
        {
          path: 'malicious-ip-management',
          name: 'malicious-ip-management',
          // 恶意IP管理页面
          component: () => import('../views/MaliciousIPManagement.vue'),
        },
        {
          path: 'ai-config-management',
          name: 'ai-config-management',
          // AI配置管理页面
          component: () => import('../views/AIConfigManagement.vue'),
        },
      ]
    },
    {
      path: '/login',
      name: 'login',
      // 登录页面
      component: () => import('../components/Login.vue'),
      meta: { requiresGuest: true },
    },
    {
      path: '/register',
      name: 'register',
      // 注册页面
      component: () => import('../components/Register.vue'),
      meta: { requiresGuest: true },
    },
  ],
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  // 检查本地存储中是否有token，如果有则认为已认证
  const token = localStorage.getItem('token')
  const isTokenPresent = !!token
  
  // 检查路由是否需要身份验证
  if (to.meta.requiresAuth && !isTokenPresent) {
    // 如果需要身份验证但用户未登录，则重定向到登录页面
    next('/login')
    return
  }
  
  // 检查路由是否需要游客状态（未登录）
  if (to.meta.requiresGuest && isTokenPresent) {
    // 如果需要游客状态但用户已登录，则重定向到首页
    next('/')
    return
  }
  
  // 其他情况，允许访问
  next()
})

export default router
