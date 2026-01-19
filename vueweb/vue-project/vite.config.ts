import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueJsx(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  // 服务器配置
  server: {
    port: 8080, // 设置开发服务器端口为8080
    host: true, // 允许外部访问
    // 代理配置，解决跨域问题
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000', // 后端服务器地址
        changeOrigin: true, // 开启代理并允许跨域
        // 不重写路径，保持/api前缀
      }
    }
  },
})
