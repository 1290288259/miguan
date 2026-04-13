<template>
  <div class="overview-container">
    <!-- 统计卡片区 -->
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <span>总攻击数</span>
              <el-tag type="danger">Total</el-tag>
            </div>
          </template>
          <div :class="['stat-value', { 'bounce': totalFlash }]">
            {{ summary.total_attacks }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <span>今日攻击</span>
              <el-tag type="warning">Today</el-tag>
            </div>
          </template>
          <div :class="['stat-value', { 'bounce': todayFlash }]">
            {{ summary.today_attacks }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <span>恶意IP数</span>
              <el-tag type="info">Malicious IPs</el-tag>
            </div>
          </template>
          <div :class="['stat-value', { 'bounce': ipFlash }]">
            {{ summary.malicious_ips }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 实时告警列表 -->
    <el-card shadow="hover" class="alert-card">
      <template #header>
        <div class="card-header">
          <span>实时攻击告警</span>
          <el-tag type="danger" effect="dark" size="small">
            LIVE
            <span class="live-dot"></span>
          </el-tag>
        </div>
      </template>
      <div class="alert-list-wrapper">
        <div v-if="alertList.length === 0" class="empty-alert">
          暂无实时告警，等待攻击事件...
        </div>
        <transition-group name="alert-slide" tag="div" class="alert-list">
          <div
            v-for="item in alertList"
            :key="item.log_id"
            class="alert-item"
            :class="'level-' + item.threat_level"
          >
            <div class="alert-left">
              <el-tag
                :type="getThreatTagType(item.threat_level)"
                size="small"
                effect="dark"
                class="threat-tag"
              >
                {{ item.threat_level?.toUpperCase() }}
              </el-tag>
              <span class="alert-type">{{ item.attack_type }}</span>
            </div>
            <div class="alert-center">
              <span class="alert-ip">{{ item.source_ip }}</span>
              <span class="alert-protocol">{{ item.protocol }}</span>
            </div>
            <div class="alert-right">
              <span class="alert-time">{{ formatTime(item.attack_time) }}</span>
            </div>
          </div>
        </transition-group>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import axios from '@/utils/axios'
import { onAttack, offAttack } from '@/composables/useSocket'

// ============ 数据 ============
interface AlertItem {
  log_id: number
  source_ip: string
  attack_type: string
  threat_level: string
  protocol: string
  attack_time: string
}

const summary = ref({
  total_attacks: 0,
  today_attacks: 0,
  malicious_ips: 0
})

// 实时告警列表，最多保留 10 条
const alertList = ref<AlertItem[]>([])
const MAX_ALERTS = 10

// 数字跳动闪烁控制
const totalFlash = ref(false)
const todayFlash = ref(false)
const ipFlash = ref(false)

// 已知 IP 集合（用于判断是否新增恶意IP）
const knownIps = new Set<string>()

// ============ API 拉取 ============
const fetchSummary = async () => {
  try {
    const res: any = await axios.get('/dashboard/summary')
    if (res.code === 200) {
      summary.value = res.data

      // 标记已知 IP 不再重复计数（从实际API拉取的已有恶意IP数量）
      // 这里只初始化数字，不需要逐个追踪旧IP
    }
  } catch (error: any) {
    console.error('Failed to fetch summary', error)
  }
}

// ============ 闪烁动画触发 ============
function triggerFlash(flashRef: typeof totalFlash) {
  flashRef.value = true
  setTimeout(() => { flashRef.value = false }, 400)
}

// ============ 威胁等级标签样式 ============
function getThreatTagType(level: string): string {
  switch (level) {
    case 'high':
    case 'critical':
      return 'danger'
    case 'medium':
      return 'warning'
    default:
      return 'info'
  }
}

// ============ 时间格式化 ============
function formatTime(timeStr: string): string {
  if (!timeStr) return ''
  try {
    const d = new Date(timeStr)
    const h = String(d.getHours()).padStart(2, '0')
    const m = String(d.getMinutes()).padStart(2, '0')
    const s = String(d.getSeconds()).padStart(2, '0')
    return `${h}:${m}:${s}`
  } catch {
    return timeStr
  }
}

// ============ WebSocket 事件处理 ============
const handleAttack = (payload: any) => {
  // 1. 数字递增 + 跳动
  summary.value.total_attacks++
  triggerFlash(totalFlash)

  summary.value.today_attacks++
  triggerFlash(todayFlash)

  // 如果是新的恶意IP，恶意IP数也递增
  if (payload.source_ip && !knownIps.has(payload.source_ip)) {
    knownIps.add(payload.source_ip)
    summary.value.malicious_ips++
    triggerFlash(ipFlash)
  }

  // 2. 实时告警列表 — 新条目从顶部插入
  const newAlert: AlertItem = {
    log_id: payload.log_id,
    source_ip: payload.source_ip,
    attack_type: payload.attack_type,
    threat_level: payload.threat_level,
    protocol: payload.protocol,
    attack_time: payload.attack_time
  }
  alertList.value.unshift(newAlert)

  // 超过 MAX_ALERTS 则移除最旧的
  if (alertList.value.length > MAX_ALERTS) {
    alertList.value = alertList.value.slice(0, MAX_ALERTS)
  }
}

onMounted(() => {
  fetchSummary()
  onAttack(handleAttack)
})

onUnmounted(() => {
  offAttack(handleAttack)
})
</script>

<style scoped>
.overview-container {
  padding: 20px;
}

/* === 统计卡片 === */
.stat-value {
  font-size: 42px;
  font-weight: bold;
  text-align: center;
  color: var(--el-text-color-primary);
  margin-top: 20px;
  margin-bottom: 20px;
  transition: color 0.2s, transform 0.2s;
}

.stat-value.bounce {
  animation: number-bounce 0.4s ease-out;
  color: #f56c6c;
}

@keyframes number-bounce {
  0% { transform: scale(1); }
  30% { transform: scale(1.25); }
  60% { transform: scale(0.95); }
  100% { transform: scale(1); }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-card {
  height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

/* === 实时告警卡片 === */
.alert-card {
  margin-top: 20px;
}

.live-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #fff;
  margin-left: 6px;
  animation: live-pulse 1.5s ease-in-out infinite;
  vertical-align: middle;
}

@keyframes live-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}

.alert-list-wrapper {
  max-height: 400px;
  overflow-y: auto;
}

.empty-alert {
  text-align: center;
  padding: 40px 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.alert-list {
  position: relative;
}

.alert-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-radius: 6px;
  margin-bottom: 6px;
  background: var(--el-fill-color-lighter);
  border-left: 4px solid var(--el-border-color);
  transition: background 0.2s;
}

.alert-item:hover {
  background: var(--el-fill-color);
}

.alert-item.level-high,
.alert-item.level-critical {
  border-left-color: #f56c6c;
  background: rgba(245, 108, 108, 0.05);
}

.alert-item.level-medium {
  border-left-color: #e6a23c;
  background: rgba(230, 162, 60, 0.05);
}

.alert-item.level-low {
  border-left-color: #909399;
}

.alert-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 200px;
}

.threat-tag {
  min-width: 60px;
  text-align: center;
}

.alert-type {
  font-weight: 600;
  font-size: 14px;
}

.alert-center {
  display: flex;
  align-items: center;
  gap: 12px;
}

.alert-ip {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.alert-protocol {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color);
  padding: 2px 8px;
  border-radius: 4px;
}

.alert-right {
  min-width: 80px;
  text-align: right;
}

.alert-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-family: 'Courier New', monospace;
}

/* === 列表滑入动画 === */
.alert-slide-enter-active {
  transition: all 0.4s ease-out;
}
.alert-slide-leave-active {
  transition: all 0.3s ease-in;
  position: absolute;
  width: 100%;
}
.alert-slide-enter-from {
  transform: translateX(-30px);
  opacity: 0;
}
.alert-slide-leave-to {
  transform: translateX(30px);
  opacity: 0;
}
.alert-slide-move {
  transition: transform 0.3s ease;
}
</style>
