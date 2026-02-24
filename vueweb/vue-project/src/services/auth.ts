/**
 * 用户认证相关的API服务
 * 封装所有与用户认证相关的API请求
 */
import axios from '../utils/axios'

// 用户注册接口
export const registerUser = async (username: string, password: string, role?: number, phone?: string, email?: string) => {
  try {
    const response = await axios.post('/user/register', {
      username,
      password,
      role,
      phone,
      email
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

// 更新当前用户信息接口
export const updateUserInfo = async (phone?: string, email?: string, password?: string, old_password?: string) => {
  try {
    const response = await axios.put('/user/me', {
      phone,
      email,
      password,
      old_password
    })
    return response
  } catch (error) {
    console.error('更新用户信息失败:', error)
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