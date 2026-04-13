<template>
  <div class="dashboard-layout">
    <!-- 高危攻击横幅 -->
    <transition name="banner-slide">
      <div v-if="showBanner" class="danger-banner" @click="showBanner = false">
        <el-icon class="banner-icon"><WarningFilled /></el-icon>
        <span class="banner-text">{{ bannerText }}</span>
        <el-icon class="banner-close"><Close /></el-icon>
      </div>
    </transition>

    <el-menu
      :default-active="activeMenu"
      mode="horizontal"
      router
      class="dashboard-menu"
      :ellipsis="false"
    >
      <el-menu-item index="/overview">
        <el-icon><Odometer /></el-icon>
        <span>总览</span>
      </el-menu-item>
      <el-menu-item index="/trend">
        <el-icon><TrendCharts /></el-icon>
        <span>攻击趋势</span>
      </el-menu-item>
      <el-menu-item index="/types">
        <el-icon><PieChart /></el-icon>
        <span>攻击分布</span>
      </el-menu-item>
      <el-menu-item index="/map">
        <el-icon><MapLocation /></el-icon>
        <span>来源排名</span>
      </el-menu-item>

      <!-- WebSocket 连接状态指示灯 -->
      <div class="ws-status-indicator">
        <span :class="['status-dot', isConnected ? 'connected' : 'disconnected']"></span>
        <span class="status-label">{{ isConnected ? '实时连接' : '连接断开' }}</span>
      </div>
    </el-menu>
    
    <div class="dashboard-content">
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElNotification } from 'element-plus'
import { Odometer, TrendCharts, PieChart, MapLocation, WarningFilled, Close } from '@element-plus/icons-vue'
import { connectSocket, disconnectSocket, onAttack, offAttack, isConnected } from '@/composables/useSocket'

const route = useRoute()
const activeMenu = computed(() => route.path)

// 高危横幅状态
const showBanner = ref(false)
const bannerText = ref('')
let bannerTimer: ReturnType<typeof setTimeout> | null = null

// 限流：同一攻击类型 5 秒内不重复弹横幅
const recentBannerTypes = new Map<string, number>()

/**
 * 处理实时攻击事件
 */
const handleAttack = (payload: any) => {
  const { attack_type, source_ip, threat_level, protocol } = payload

  // 所有恶意攻击都弹 ElNotification
  ElNotification({
    title: '发现恶意攻击',
    message: `[${attack_type}] 来自 ${source_ip} (${protocol})`,
    type: threat_level === 'high' || threat_level === 'critical' ? 'error' : 'warning',
    duration: 4000,
    position: 'top-right'
  })

  // 高危攻击额外显示横幅
  if (threat_level === 'high' || threat_level === 'critical') {
    const now = Date.now()
    const lastTime = recentBannerTypes.get(attack_type)

    // 5秒内同类型不重复弹横幅
    if (!lastTime || now - lastTime > 5000) {
      recentBannerTypes.set(attack_type, now)
      bannerText.value = `[发现高危攻击] ${attack_type} - 来源: ${source_ip}`
      showBanner.value = true

      // 清除旧定时器
      if (bannerTimer) clearTimeout(bannerTimer)
      bannerTimer = setTimeout(() => {
        showBanner.value = false
      }, 5000)
    }
  }
}

onMounted(() => {
  // DashboardLayout 负责管理 WebSocket 连接生命周期
  connectSocket()
  onAttack(handleAttack)
})

onUnmounted(() => {
  offAttack(handleAttack)
  disconnectSocket()
  if (bannerTimer) clearTimeout(bannerTimer)
})
</script>

<style scoped>
.dashboard-layout {
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* === 高危横幅 === */
.danger-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 12px 20px;
  background: linear-gradient(90deg, #f56c6c, #e6191a, #f56c6c);
  background-size: 200% 100%;
  animation: banner-glow 2s ease-in-out infinite;
  color: #fff;
  font-weight: bold;
  font-size: 15px;
  cursor: pointer;
  box-shadow: 0 2px 12px rgba(245, 108, 108, 0.6);
}

.banner-icon {
  font-size: 20px;
  animation: pulse-icon 1s ease-in-out infinite;
}

.banner-close {
  position: absolute;
  right: 20px;
  font-size: 16px;
  opacity: 0.8;
}

.banner-close:hover {
  opacity: 1;
}

@keyframes banner-glow {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

@keyframes pulse-icon {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.3); }
}

/* 横幅滑入/滑出动画 */
.banner-slide-enter-active {
  transition: all 0.4s ease-out;
}
.banner-slide-leave-active {
  transition: all 0.3s ease-in;
}
.banner-slide-enter-from {
  transform: translateY(-100%);
  opacity: 0;
}
.banner-slide-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}

/* === 菜单栏 === */
.dashboard-menu {
  margin-bottom: 20px;
  border-bottom: solid 1px var(--el-menu-border-color);
  position: relative;
}

/* === WebSocket 状态指示灯 === */
.ws-status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  padding: 0 20px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.status-dot.connected {
  background-color: #67c23a;
  box-shadow: 0 0 6px rgba(103, 194, 58, 0.6);
  animation: dot-pulse 2s ease-in-out infinite;
}

.status-dot.disconnected {
  background-color: #f56c6c;
  box-shadow: 0 0 6px rgba(245, 108, 108, 0.6);
}

@keyframes dot-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.status-label {
  white-space: nowrap;
}

/* === 内容区 === */
.dashboard-content {
  flex: 1;
  overflow: auto;
}
</style>
