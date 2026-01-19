import './assets/main.css'

import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'

// 导入 Axios 实例
import axios from './utils/axios'

const app = createApp(App)

// 注册Element Plus
app.use(ElementPlus)

// 注册所有Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 全局注册 Axios 实例
app.config.globalProperties.$axios = axios

// 提供 Axios 实例，供组合式 API 使用
app.provide('axios', axios)

app.use(router)

app.mount('#app')
