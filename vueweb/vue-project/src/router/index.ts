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
          component: () => import('../views/dashboard/DashboardLayout.vue'),
          children: [
            { path: '', redirect: '/overview' },
            { 
              path: 'overview', 
              name: 'dashboard-overview', 
              component: () => import('../views/dashboard/Overview.vue') 
            },
            { 
              path: 'trend', 
              name: 'dashboard-trend', 
              component: () => import('../views/dashboard/Trend.vue') 
            },
            { 
              path: 'types', 
              name: 'dashboard-types', 
              component: () => import('../views/dashboard/Types.vue') 
            },
            { 
              path: 'map', 
              name: 'dashboard-map', 
              component: () => import('../views/dashboard/Map.vue') 
            },
          ]
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
          meta: { permission: '/log-query' }
        },
        {
          path: 'match-rule-management',
          name: 'match-rule-management',
          // 匹配规则管理页面
          component: () => import('../views/MatchRuleManagement.vue'),
          meta: { permission: '/match-rule-management' }
        },
        {
          path: 'honeypot-management',
          name: 'honeypot-management',
          // 蜜罐管理页面
          component: () => import('../views/HoneypotManagement.vue'),
          meta: { permission: '/honeypot-management' }
        },
        {
          path: 'malicious-ip-management',
          name: 'malicious-ip-management',
          // 恶意IP管理页面
          component: () => import('../views/MaliciousIPManagement.vue'),
          meta: { permission: '/malicious-ip-management' }
        },
        {
          path: 'ai-config-management',
          name: 'ai-config-management',
          // AI配置管理页面
          component: () => import('../views/AIConfigManagement.vue'),
          meta: { permission: '/ai-config-management' }
        },
        {
          path: 'user-management',
          name: 'user-management',
          // 用户管理页面
          component: () => import('../views/UserManagement.vue'),
          meta: { permission: '/user-management' }
        },
        {
          path: 'profile',
          name: 'profile',
          // 个人信息页面
          component: () => import('../views/UserProfile.vue'),
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
  
  // 权限检查前，确保用户数据已加载
  // 修复时序 Bug：页面刷新时 Pinia store 是同步从 localStorage 初始化的，
  // 但如果 localStorage 中的 user 数据已过期或被清除，需要重新从后端获取。
  // 若 store 中 user 为空但 token 存在，则先异步拉取用户信息再做权限判断。
  if (isTokenPresent && !userStore.user.value) {
    const result = await userStore.fetchCurrentUser()
    if (!result.success) {
      // 获取用户信息失败（token已过期），清除状态并跳转登录
      next('/login')
      return
    }
  }

  // 权限检查
  const user = userStore.user.value
  if (to.meta.permission && user) {
      // 管理员(role=1)拥有所有权限
      if (user.role === 1) {
          next()
          return
      }

      // 检查权限
      // 同时检查 role-based permissions 和 user-assigned modules
      const permissions = user.permissions || []
      const modules = user.modules || []
      
      const allowedPaths = [
          ...permissions.map((p: any) => p.path),
          ...modules.map((m: any) => m.path)
      ]
      
      // 注意：to.meta.permission 是我们在路由定义中添加的自定义属性
      if (!allowedPaths.includes(to.meta.permission as string)) {
          // 无权限，重定向到首页
          next('/')
          return
      }
  }
  
  // 其他情况，允许访问
  next()
})

export default router
