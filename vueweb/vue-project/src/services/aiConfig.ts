/**
 * AI配置相关的API服务
 */
import axios from '../utils/axios'

export interface AIConfig {
  id: number
  name: string
  api_url: string
  model_name: string
  api_key?: string
  provider: string
  is_active: boolean
  description?: string
  created_at?: string
  updated_at?: string
}

// 获取所有配置
export const getAIConfigs = async () => {
  try {
    const response = await axios.get('/ai-config/')
    return response
  } catch (error) {
    console.error('获取AI配置失败:', error)
    throw error
  }
}

// 创建配置
export const createAIConfig = async (data: Partial<AIConfig>) => {
  try {
    const response = await axios.post('/ai-config/', data)
    return response
  } catch (error) {
    console.error('创建AI配置失败:', error)
    throw error
  }
}

// 更新配置
export const updateAIConfig = async (id: number, data: Partial<AIConfig>) => {
  try {
    const response = await axios.put(`/ai-config/${id}`, data)
    return response
  } catch (error) {
    console.error('更新AI配置失败:', error)
    throw error
  }
}

// 删除配置
export const deleteAIConfig = async (id: number) => {
  try {
    const response = await axios.delete(`/ai-config/${id}`)
    return response
  } catch (error) {
    console.error('删除AI配置失败:', error)
    throw error
  }
}

// 激活配置
export const activateAIConfig = async (id: number) => {
  try {
    const response = await axios.post(`/ai-config/${id}/activate`)
    return response
  } catch (error) {
    console.error('激活AI配置失败:', error)
    throw error
  }
}
