/**
 * Axios 全局配置
 * 用于配置和创建全局 Axios 实例
 */
import axios from 'axios'

// 创建 Axios 实例
const instance = axios.create({
  // 基础URL，开发环境使用代理路径，生产环境使用完整URL
  baseURL: import.meta.env.PROD ? 'http://127.0.0.1:5000' : '/api',
  // 请求超时时间
  timeout: 10000,
  // 请求头配置
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
instance.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么，例如添加 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    // 对请求错误做些什么
    return Promise.reject(error)
  }
)

// 响应拦截器
instance.interceptors.response.use(
  (response) => {
    // 对响应数据做点什么
    return response.data
  },
  (error) => {
    // 对响应错误做点什么
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // 如果是登录接口本身的401，不进行跳转，直接返回错误让前端处理
          if (error.config && error.config.url && error.config.url.includes('/user/login')) {
            break
          }
          // 未授权，可以跳转到登录页
          console.error('未授权，请重新登录')
          localStorage.removeItem('token')
          localStorage.removeItem('refreshToken')
          localStorage.removeItem('user')
          window.location.href = '/login'
          break
        case 404:
          console.error('请求的资源不存在')
          break
        case 500:
          console.error('服务器错误')
          break
        default:
          console.error(`请求错误: ${error.response.status}`)
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      console.error('网络错误，请检查网络连接')
    } else {
      // 发送请求时发生了错误
      console.error('请求配置错误', error.message)
    }
    return Promise.reject(error)
  }
)

export default instance