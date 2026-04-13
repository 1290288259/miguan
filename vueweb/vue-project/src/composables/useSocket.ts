/**
 * WebSocket 攻击事件总线（全量重写）
 *
 * 设计要点：
 * 1. 全局单例 Socket，由 DashboardLayout 统一管理生命周期
 * 2. pending 队列：连接建立前订阅的回调暂存，connect 后补注册
 * 3. 重连恢复：reconnect 后自动重新绑定所有活跃回调
 * 4. 移除引用计数机制，消除路由切换导致的断连问题
 */

import { ref } from 'vue'
import { io, Socket } from 'socket.io-client'

// 全局单例 Socket 实例
let socket: Socket | null = null

// 响应式连接状态
export const isConnected = ref(false)

// 所有活跃的回调函数集合（用于重连后自动恢复）
const activeCallbacks = new Set<(payload: any) => void>()

// 连接建立前暂存的回调队列
const pendingCallbacks: Array<(payload: any) => void> = []

/**
 * 创建并连接 Socket（幂等，只会创建一次）
 */
export function connectSocket(): void {
  if (socket) return

  const baseUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'
  const socketUrl = baseUrl.replace('/api', '')

  socket = io(`${socketUrl}/ws`, {
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: Infinity,  // 无限重连
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000
  })

  socket.on('connect', () => {
    isConnected.value = true
    console.log('[AttackBus] WebSocket connected, sid:', socket?.id)

    // 连接建立后，把 pending 队列中的回调移入 active 集合
    while (pendingCallbacks.length > 0) {
      const cb = pendingCallbacks.shift()!
      activeCallbacks.add(cb)
    }

    // 先清除所有 new_attack 监听器，再统一重新绑定
    // 避免重连时累积重复 handler（socket.io 的 on() 是累加式的）
    socket!.off('new_attack')
    activeCallbacks.forEach(cb => {
      socket!.on('new_attack', cb)
    })
  })

  socket.on('disconnect', (reason) => {
    isConnected.value = false
    console.log('[AttackBus] WebSocket disconnected:', reason)
  })

  socket.on('connect_error', (error) => {
    console.error('[AttackBus] WebSocket connection error:', error.message)
  })
}

/**
 * 断开 Socket 连接（仅在 DashboardLayout 卸载时调用）
 */
export function disconnectSocket(): void {
  if (socket) {
    socket.removeAllListeners()
    socket.disconnect()
    socket = null
    isConnected.value = false
    activeCallbacks.clear()
    pendingCallbacks.length = 0
    console.log('[AttackBus] WebSocket fully disconnected and cleaned up')
  }
}

/**
 * 订阅 new_attack 事件
 * 如果 socket 尚未连接，回调会被暂存到 pending 队列中，
 * 等 connect 事件触发后自动补注册。
 */
export function onAttack(callback: (payload: any) => void): void {
  if (!socket) {
    // socket 还没创建，先入 pending 队列
    if (!pendingCallbacks.includes(callback)) {
      pendingCallbacks.push(callback)
    }
    return
  }

  if (socket.connected) {
    // 已连接，直接注册
    activeCallbacks.add(callback)
    socket.on('new_attack', callback)
  } else {
    // 正在连接中，入 pending 队列
    if (!pendingCallbacks.includes(callback)) {
      pendingCallbacks.push(callback)
    }
  }
}

/**
 * 取消订阅 new_attack 事件
 */
export function offAttack(callback: (payload: any) => void): void {
  activeCallbacks.delete(callback)
  const idx = pendingCallbacks.indexOf(callback)
  if (idx !== -1) pendingCallbacks.splice(idx, 1)
  socket?.off('new_attack', callback)
}

/**
 * 组合式 API 封装（兼容旧调用方式）
 * 不再管理生命周期，生命周期由 DashboardLayout 统一管理
 */
export function useSocket() {
  return {
    isConnected,
    onAttack,
    offAttack
  }
}
