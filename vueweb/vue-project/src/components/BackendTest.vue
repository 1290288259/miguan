<template>
  <div class="backend-test">
    <h1>后端接口测试</h1>
    <button @click="fetchData" :disabled="loading">
      {{ loading ? '请求中...' : '获取数据' }}
    </button>
    
    <div v-if="data" class="result">
      <h2>返回内容:</h2>
      <pre>{{ data }}</pre>
    </div>
    
    <div v-if="error" class="error">
      <h2>错误信息:</h2>
      <pre>{{ error }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, inject } from 'vue'

// 注入全局Axios实例
const axios = inject('axios') as any

const data = ref<string | null>(null)
const error = ref<string | null>(null)
const loading = ref(false)

// 获取后端数据
const fetchData = async () => {
  loading.value = true
  data.value = null
  error.value = null
  
  try {
    // 使用Axios请求后端接口
    // 由于配置了代理，这里直接使用根路径即可
    const response = await axios.get('/')
    
    // 将返回数据转换为字符串显示
    if (typeof response === 'object') {
      data.value = JSON.stringify(response, null, 2)
    } else {
      data.value = String(response)
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '未知错误'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.backend-test {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

button {
  padding: 10px 20px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  margin-bottom: 20px;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

button:hover:not(:disabled) {
  background-color: #45a049;
}

.result, .error {
  margin-top: 20px;
  padding: 15px;
  border-radius: 6px;
}

.result {
  background-color: #e8f5e9;
  border: 1px solid #c8e6c9;
}

.error {
  background-color: #ffebee;
  border: 1px solid #ffcdd2;
  color: #c62828;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 14px;
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}
</style>