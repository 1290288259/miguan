<template>
  <div class="chart-view-container">
    <el-card shadow="hover" class="chart-card">
      <template #header>
        <div class="card-header">
          <span>恶意IP来源全球分布与排名</span>
        </div>
      </template>
      <div class="content-wrapper">
        <div ref="worldMapChart" class="map-container"></div>
        <div ref="rankChart" class="rank-container"></div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import axios from '@/utils/axios'
import { useThemeStore } from '@/stores/theme'
import { onAttack, offAttack } from '@/composables/useSocket'

// Theme Store
const themeStore = useThemeStore()

// Chart DOM refs
const worldMapChart = ref<HTMLElement | null>(null)
const rankChart = ref<HTMLElement | null>(null)
let worldMapInstance: echarts.ECharts | null = null
let rankChartInstance: echarts.ECharts | null = null

// 数据缓存
let cachedMapData: any[] = []
let cachedLocations: string[] = []
let cachedCounts: number[] = []

// 活跃脉冲散点（使用 Map 避免 filter 竞态）
const activeScatterMap = new Map<number, any>()

// 图表是否初始化完成
let chartReady = false

// 攻击事件缓冲队列（图表未就绪时暂存）
const pendingAttacks: any[] = []

// ============ 主题样式更新 ============
const updateChartStyles = () => {
  if (!worldMapInstance || !rankChartInstance) return

  const isDark = themeStore.isDark
  const textColor = isDark ? '#e0f7fa' : '#303133'
  const axisColor = isDark ? '#00f3ff' : '#909399'
  const tooltipBg = isDark ? 'rgba(5, 11, 20, 0.9)' : 'rgba(255, 255, 255, 0.9)'
  const tooltipBorder = isDark ? '#00f3ff' : '#dcdfe6'
  const tooltipText = isDark ? '#e0f7fa' : '#303133'
  const splitLineColor = isDark ? 'rgba(0, 243, 255, 0.1)' : '#ebeef5'
  const mapAreaColor = isDark ? '#323c48' : '#f0f2f5'
  const mapBorderColor = isDark ? '#111' : '#dcdfe6'
  const visualMapText = isDark ? '#e0f7fa' : '#606266'
  
  worldMapInstance.setOption({
    tooltip: {
      backgroundColor: tooltipBg,
      borderColor: tooltipBorder,
      textStyle: { color: tooltipText }
    },
    visualMap: {
      textStyle: { color: visualMapText },
      inRange: {
        color: isDark 
          ? ['#e0f7fa', '#00f3ff', '#004a80'] 
          : ['#e1f3d8', '#67c23a', '#2c5f1a']
      }
    },
    geo: {
      itemStyle: {
        areaColor: mapAreaColor,
        borderColor: mapBorderColor
      },
      emphasis: {
        label: { color: isDark ? '#fff' : '#303133' },
        itemStyle: { areaColor: isDark ? '#00f3ff' : '#409eff' }
      }
    }
  })

  rankChartInstance.setOption({
    title: {
      textStyle: { color: isDark ? '#00f3ff' : '#303133' }
    },
    tooltip: { 
      backgroundColor: tooltipBg,
      borderColor: tooltipBorder,
      textStyle: { color: tooltipText }
    },
    xAxis: { 
      axisLabel: { color: axisColor },
      splitLine: { lineStyle: { color: splitLineColor } }
    },
    yAxis: { 
      axisLabel: { color: axisColor },
      axisLine: { lineStyle: { color: isDark ? 'rgba(0, 243, 255, 0.3)' : '#dcdfe6' } }
    },
    series: [{ 
      label: {
        color: isDark ? '#00f3ff' : '#409eff'
      },
      itemStyle: {
        color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
          { offset: 0, color: isDark ? '#83bff6' : '#a0cfff' },
          { offset: 0.5, color: isDark ? '#188df0' : '#409eff' },
          { offset: 1, color: isDark ? '#188df0' : '#409eff' }
        ])
      }
    }]
  })
}

watch(() => themeStore.isDark, () => {
  updateChartStyles()
})

// ============ 图表初始化 ============
const initCharts = async () => {
  if (!worldMapChart.value || !rankChart.value) return
  
  worldMapInstance = echarts.init(worldMapChart.value)
  rankChartInstance = echarts.init(rankChart.value)
  
  // 加载世界地图 JSON
  try {
    const response = await fetch('/world.json')
    const mapJson = await response.json()
    echarts.registerMap('world', mapJson)
  } catch (error) {
    console.error('Failed to load world map json', error)
    return
  }

  // 加载地图数据
  try {
    const res: any = await axios.get('/dashboard/map')
    if (res.code === 200) {
      const data = res.data || []
      data.sort((a: any, b: any) => b.value - a.value)
      
      cachedMapData = data.map((item: any) => ({
        name: item.name,
        value: item.value
      }))
      cachedLocations = data.map((item: any) => item.name || 'Unknown')
      cachedCounts = data.map((item: any) => item.value)

      // 世界地图初始渲染
      worldMapInstance.setOption({
        tooltip: {
          trigger: 'item',
          formatter: function(params: any) {
            if (params.seriesType === 'effectScatter') {
              return `实时攻击检测: ${params.data.name}<br/>类型: ${params.data.attack_type}<br/>来源: ${params.data.source_ip}`
            }
            return `${params.name}: ${params.value || 0} 次攻击`
          }
        },
        visualMap: {
          min: 0,
          max: Math.max(...cachedCounts, 10),
          text: ['High', 'Low'],
          realtime: false,
          calculable: true,
          left: 'left',
          bottom: 'bottom'
        },
        geo: {
          map: 'world',
          roam: true,
          zoom: 1.2,
          scaleLimit: { min: 0.8, max: 5 },
          itemStyle: {
            areaColor: '#f0f2f5',
            borderColor: '#dcdfe6'
          },
          emphasis: {
            itemStyle: { areaColor: '#409eff' },
            label: { show: false }
          }
        },
        series: [
          {
            name: '恶意来源',
            type: 'map',
            geoIndex: 0,
            data: cachedMapData
          },
          {
            name: '实时攻击点',
            type: 'effectScatter',
            coordinateSystem: 'geo',
            data: [],
            symbolSize: 15,
            showEffectOn: 'render',
            rippleEffect: {
              brushType: 'stroke',
              scale: 4
            },
            itemStyle: {
              color: '#f56c6c',
              shadowBlur: 10,
              shadowColor: '#f56c6c'
            },
            zlevel: 1
          }
        ]
      })

      // 排名柱状图
      rankChartInstance.setOption({
        title: {
          text: 'Top 10 来源排名',
          left: 'center'
        },
        tooltip: { 
          trigger: 'axis', 
          axisPointer: { type: 'shadow' }
        },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { type: 'value' },
        yAxis: { 
          type: 'category', 
          data: cachedLocations,
          inverse: true
        },
        series: [{ 
          type: 'bar', 
          data: cachedCounts,
          label: { show: true, position: 'right' }
        }]
      })

      updateChartStyles()
    }
  } catch (error) {
    console.error('Failed to fetch map data', error)
  }

  // 标记图表初始化完成
  chartReady = true

  // 处理缓冲队列中暂存的攻击事件
  while (pendingAttacks.length > 0) {
    const p = pendingAttacks.shift()!
    addScatterPoint(p)
  }
}

// ============ 脉冲散点管理 ============

/**
 * 获取当前所有活跃散点的数组（从 Map 中提取）
 */
function getScatterData(): any[] {
  return Array.from(activeScatterMap.values())
}

/**
 * 更新 ECharts 中 effectScatter 系列的数据
 * 传入完整的系列配置，避免 series index 错配问题
 */
function refreshScatterSeries(): void {
  if (!worldMapInstance) return
  worldMapInstance.setOption({
    series: [
      {
        // index 0: 保持地图系列不变
        name: '恶意来源'
      },
      {
        // index 1: 完整的 effectScatter 配置，防止 series 不存在时创建裸系列
        name: '实时攻击点',
        type: 'effectScatter',
        coordinateSystem: 'geo',
        data: getScatterData(),
        symbolSize: 15,
        showEffectOn: 'render',
        rippleEffect: {
          brushType: 'stroke',
          scale: 4
        },
        itemStyle: {
          color: '#f56c6c',
          shadowBlur: 10,
          shadowColor: '#f56c6c'
        },
        zlevel: 1
      }
    ]
  })
}

/**
 * 添加一个脉冲散点，5秒后自动移除
 */
function addScatterPoint(payload: any): void {
  const logId = payload.log_id
  const newDot = {
    name: payload.source_ip,
    value: [payload.longitude, payload.latitude, 100],
    source_ip: payload.source_ip,
    attack_type: payload.attack_type,
    log_id: logId
  }

  activeScatterMap.set(logId, newDot)
  refreshScatterSeries()

  // 5秒后自动移除
  setTimeout(() => {
    activeScatterMap.delete(logId)
    refreshScatterSeries()
  }, 5000)
}

// ============ WebSocket 事件处理 ============
const handleNewAttack = (payload: any) => {
  // 类型检查：确保经纬度是数字
  if (typeof payload.longitude !== 'number' || typeof payload.latitude !== 'number') {
    return
  }
  // 过滤无法解析的 IP（后端返回 0.0, 0.0 表示 GeoIP 查询失败）
  // (0, 0) 位于大西洋"Null Island"，不是有效攻击位置
  if (payload.longitude === 0 && payload.latitude === 0) {
    console.warn('[Map] Skipping null-island coordinates for IP:', payload.source_ip)
    return
  }

  if (!chartReady) {
    // 图表未就绪，暂存到缓冲队列
    pendingAttacks.push(payload)
    return
  }

  addScatterPoint(payload)
}

// ============ 窗口大小自适应 ============
const resizeChart = () => {
  worldMapInstance?.resize()
  rankChartInstance?.resize()
}

// ============ 生命周期 ============
onMounted(async () => {
  // 先完成图表初始化（await），再订阅事件
  // 修复 Bug #4：确保 worldMapInstance 就绪后才处理事件
  await initCharts()
  window.addEventListener('resize', resizeChart)
  onAttack(handleNewAttack)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeChart)
  offAttack(handleNewAttack)
  worldMapInstance?.dispose()
  rankChartInstance?.dispose()
  worldMapInstance = null
  rankChartInstance = null
  chartReady = false
  activeScatterMap.clear()
})
</script>

<style scoped>
.chart-view-container {
  padding: 20px;
  height: calc(100vh - 140px);
}
.chart-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.content-wrapper {
  display: flex;
  height: 100%;
  width: 100%;
}
.map-container {
  flex: 2;
  height: 100%;
  min-height: 500px;
}
.rank-container {
  flex: 1;
  height: 100%;
  min-height: 500px;
  border-left: 1px solid rgba(0, 243, 255, 0.1);
  padding-left: 20px;
}
:deep(.el-card__body) {
  flex: 1;
  padding: 0;
}
</style>
