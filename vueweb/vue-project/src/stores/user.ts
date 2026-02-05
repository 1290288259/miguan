/**
 * 用户状态管理
 * 使用Vue 3的响应式API管理用户状态
 */
import { ref, computed } from 'vue'
import { loginUser, logoutUser, getCurrentUser } from '../services/auth'

// 用户状态
const user = ref(null)
const token = ref(localStorage.getItem('token') || '')
const refreshToken = ref(localStorage.getItem('refreshToken') || '')
const isAuthenticated = computed(() => !!token.value)
const userRole = computed(() => user.value?.role || null)
const isAdmin = computed(() => userRole.value === 1)

// 初始化用户状态
const initUserState = () => {
  const savedUser = localStorage.getItem('user')
  if (savedUser) {
    try {
      user.value = JSON.parse(savedUser)
    } catch (error) {
      console.error('解析用户信息失败:', error)
      clearUserState()
    }
  }
}

// 清除用户状态
const clearUserState = () => {
  user.value = null
  token.value = ''
  refreshToken.value = ''
  localStorage.removeItem('token')
  localStorage.removeItem('refreshToken')
  localStorage.removeItem('user')
}

// 设置用户状态
const setUserState = (userData: any, accessToken: string, refreshTokenValue: string) => {
  user.value = userData
  token.value = accessToken
  refreshToken.value = refreshTokenValue
  
  // 保存到本地存储
  localStorage.setItem('token', accessToken)
  localStorage.setItem('refreshToken', refreshTokenValue)
  localStorage.setItem('user', JSON.stringify(userData))
}

// 登录操作
const login = async (username: string, password: string) => {
  try {
    const response: any = await loginUser(username, password)
    
    if (response.code === 200 && response.data) {
      setUserState(
        response.data.user,
        response.data.access_token,
        response.data.refresh_token
      )
      return { success: true, message: response.message }
    } else {
      return { success: false, message: response.message || '登录失败' }
    }
  } catch (error: any) {
    console.error('登录失败:', error)
    return { 
      success: false, 
      message: error.response?.data?.message || '登录失败，请稍后重试' 
    }
  }
}

// 退出登录操作
const logout = async () => {
  try {
    await logoutUser()
  } catch (error) {
    console.error('退出登录请求失败:', error)
  } finally {
    clearUserState()
  }
}

// 获取当前用户信息
const fetchCurrentUser = async () => {
  try {
    const response: any = await getCurrentUser()
    
    if (response.code === 200 && response.data) {
      user.value = response.data
      localStorage.setItem('user', JSON.stringify(response.data))
      return { success: true }
    } else {
      clearUserState()
      return { success: false, message: response.msg || '获取用户信息失败' }
    }
  } catch (error: any) {
    console.error('获取用户信息失败:', error)
    clearUserState()
    return { 
      success: false, 
      message: error.response?.data?.message || '获取用户信息失败' 
    }
  }
}

// 初始化用户状态
initUserState()

// 导出用户状态和方法
export default function useUserStore() {
  return {
    // 状态
    user,
    token,
    refreshToken,
    isAuthenticated,
    userRole,
    isAdmin,
    
    // 方法
    login,
    logout,
    fetchCurrentUser,
    clearUserState
  }
}