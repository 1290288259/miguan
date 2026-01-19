<template>
  <div class="test-auth">
    <h1>用户认证测试</h1>
    
    <div class="test-section">
      <h2>注册测试</h2>
      <button @click="testRegister" :disabled="loading">
        {{ loading ? '测试中...' : '测试注册功能' }}
      </button>
      
      <div v-if="registerResult" class="result">
        <h3>注册结果:</h3>
        <pre>{{ JSON.stringify(registerResult, null, 2) }}</pre>
      </div>
    </div>
    
    <div class="test-section">
      <h2>登录测试</h2>
      <button @click="testLogin" :disabled="loading">
        {{ loading ? '测试中...' : '测试登录功能' }}
      </button>
      
      <div v-if="loginResult" class="result">
        <h3>登录结果:</h3>
        <pre>{{ JSON.stringify(loginResult, null, 2) }}</pre>
      </div>
    </div>
    
    <div class="test-section">
      <h2>快速导航</h2>
      <router-link to="/register">前往注册页面</router-link>
      <br>
      <router-link to="/login">前往登录页面</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { registerUser, loginUser } from '../services/auth'

const loading = ref(false)
const registerResult = ref(null)
const loginResult = ref(null)

// 测试注册功能
const testRegister = async () => {
  loading.value = true
  registerResult.value = null
  
  try {
    // 生成随机用户名，避免重复
    const randomUsername = `testuser_${Date.now()}`
    const password = '123456'
    
    console.log(`测试注册: 用户名=${randomUsername}, 密码=${password}`)
    
    // 调用注册API
    const response = await registerUser(randomUsername, password)
    
    // 保存注册结果
    registerResult.value = {
      success: true,
      data: response,
      message: '注册成功'
    }
    
    // 自动测试登录
    console.log('注册成功，自动测试登录...')
    setTimeout(() => {
      testLoginWithCredentials(randomUsername, password)
    }, 1000)
    
  } catch (error: any) {
    registerResult.value = {
      success: false,
      error: error.message,
      details: error.response ? error.response.data : null
    }
  } finally {
    loading.value = false
  }
}

// 测试登录功能
const testLogin = async () => {
  loading.value = true
  loginResult.value = null
  
  try {
    // 使用测试账号登录
    const username = 'testuser'
    const password = '123456'
    
    console.log(`测试登录: 用户名=${username}, 密码=${password}`)
    
    // 调用登录API
    const response = await loginUser(username, password)
    
    // 保存登录结果
    loginResult.value = {
      success: true,
      data: response,
      message: '登录成功'
    }
    
  } catch (error: any) {
    loginResult.value = {
      success: false,
      error: error.message,
      details: error.response ? error.response.data : null
    }
  } finally {
    loading.value = false
  }
}

// 使用指定凭据测试登录
const testLoginWithCredentials = async (username: string, password: string) => {
  try {
    console.log(`使用注册的账号测试登录: 用户名=${username}, 密码=${password}`)
    
    // 调用登录API
    const response = await loginUser(username, password)
    
    // 保存登录结果
    loginResult.value = {
      success: true,
      data: response,
      message: '登录成功'
    }
    
  } catch (error: any) {
    loginResult.value = {
      success: false,
      error: error.message,
      details: error.response ? error.response.data : null
    }
  }
}
</script>

<style scoped>
.test-auth {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

.test-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 6px;
}

button {
  padding: 10px 20px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  margin-bottom: 20px;
}

button:disabled {
  background-color: #a0cfff;
  cursor: not-allowed;
}

button:hover:not(:disabled) {
  background-color: #66b1ff;
}

.result {
  margin-top: 20px;
  padding: 15px;
  border-radius: 6px;
  background-color: #f5f5f5;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 14px;
  background-color: #f0f0f0;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}

a {
  color: #409eff;
  text-decoration: none;
  margin-right: 15px;
}

a:hover {
  text-decoration: underline;
}
</style>