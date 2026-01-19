/**
 * 用户认证相关的API服务
 * 封装所有与用户认证相关的API请求
 */
import axios from '../utils/axios'

// 用户注册接口
export const registerUser = async (username: string, password: string, role?: number) => {
  try {
    const response = await axios.post('/user/register', {
      username,
      password,
      role
    })
    return response
  } catch (error) {
    console.error('注册请求失败:', error)
    throw error
  }
}

// 用户登录接口
export const loginUser = async (username: string, password: string) => {
  try {
    const response = await axios.post('/user/login', {
      username,
      password
    })
    return response
  } catch (error) {
    console.error('登录请求失败:', error)
    throw error
  }
}

// 获取当前用户信息接口
export const getCurrentUser = async () => {
  try {
    const response = await axios.get('/user/me')
    return response
  } catch (error) {
    console.error('获取用户信息失败:', error)
    throw error
  }
}

// 用户退出登录接口
export const logoutUser = async () => {
  try {
    // 从本地存储中移除令牌
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    
    // 返回成功响应
    return { success: true, message: '退出登录成功' }
  } catch (error) {
    console.error('退出登录失败:', error)
    throw error
  }
}

// 设置请求拦截器，自动添加JWT令牌
axios.interceptors.request.use(
  config => {
    // 从本地存储中获取令牌
    const token = localStorage.getItem('token')
    
    // 如果令牌存在，则添加到请求头中
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 设置响应拦截器，处理令牌过期
axios.interceptors.response.use(
  response => {
    return response
  },
  error => {
    // 如果响应状态码为401，表示令牌过期或无效
    if (error.response && error.response.status === 401) {
      // 从本地存储中移除令牌
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
      
      // 跳转到登录页面
      window.location.href = '/login'
    }
    
    return Promise.reject(error)
  }
)