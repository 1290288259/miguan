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
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import axios from '@/utils/axios'
import { useThemeStore } from '@/stores/theme'

// Theme Store
const themeStore = useThemeStore()

// Chart refs
const worldMapChart = ref<HTMLElement | null>(null)
const rankChart = ref<HTMLElement | null>(null)
let worldMapInstance: echarts.ECharts | null = null
let rankChartInstance: echarts.ECharts | null = null

// Data cache
let cachedMapData: any[] = []
let cachedLocations: string[] = []
let cachedCounts: number[] = []

// Update chart styles based on theme
const updateChartStyles = () => {
  if (!worldMapInstance || !rankChartInstance) return

  const isDark = themeStore.isDark
  
  // Colors based on theme
  const textColor = isDark ? '#e0f7fa' : '#303133'
  const axisColor = isDark ? '#00f3ff' : '#909399'
  const tooltipBg = isDark ? 'rgba(5, 11, 20, 0.9)' : 'rgba(255, 255, 255, 0.9)'
  const tooltipBorder = isDark ? '#00f3ff' : '#dcdfe6'
  const tooltipText = isDark ? '#e0f7fa' : '#303133'
  const splitLineColor = isDark ? 'rgba(0, 243, 255, 0.1)' : '#ebeef5'
  const mapAreaColor = isDark ? '#323c48' : '#f0f2f5'
  const mapBorderColor = isDark ? '#111' : '#dcdfe6'
  const visualMapText = isDark ? '#e0f7fa' : '#606266'
  
  // Update World Map
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
          : ['#e1f3d8', '#67c23a', '#2c5f1a'] // Light theme: Greenish
      }
    },
    series: [
      {
        itemStyle: {
          areaColor: mapAreaColor,
          borderColor: mapBorderColor
        },
        emphasis: {
          label: { color: isDark ? '#fff' : '#303133' },
          itemStyle: { areaColor: isDark ? '#00f3ff' : '#409eff' }
        }
      }
    ]
  })

  // Update Rank Chart
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

// Watch for theme changes
watch(() => themeStore.isDark, () => {
  updateChartStyles()
})

const initCharts = async () => {
  if (!worldMapChart.value || !rankChart.value) return
  
  worldMapInstance = echarts.init(worldMapChart.value)
  rankChartInstance = echarts.init(rankChart.value)
  
  // Load Map Data
  try {
    // Use fetch to bypass baseURL prefix from axios instance
    const response = await fetch('/world.json')
    const mapJson = await response.json()
    echarts.registerMap('world', mapJson)
  } catch (error) {
    console.error('Failed to load world map json', error)
    return
  }

  try {
    const res: any = await axios.get('/dashboard/map')
    if (res.code === 200) {
      const data = res.data || []
      
      // Sort data by value descending for ranking
      data.sort((a: any, b: any) => b.value - a.value)
      
      // Cache data for updates
      cachedMapData = data.map((item: any) => ({
        name: item.name,
        value: item.value
      }))
      cachedLocations = data.map((item: any) => item.name || 'Unknown')
      cachedCounts = data.map((item: any) => item.value)

      // Initial Render with basic options (colors will be updated by updateChartStyles)
      worldMapInstance.setOption({
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c} 次攻击'
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
        series: [
          {
            name: '恶意来源',
            type: 'map',
            map: 'world',
            roam: true,
            zoom: 1.2,
            scaleLimit: { min: 0.8, max: 5 },
            data: cachedMapData
          }
        ]
      })

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

      // Apply theme styles
      updateChartStyles()
    }
  } catch (error) {
    console.error('Failed to fetch map data', error)
  }
}

const resizeChart = () => {
  worldMapInstance?.resize()
  rankChartInstance?.resize()
}

onMounted(() => {
  nextTick(() => {
    initCharts()
    window.addEventListener('resize', resizeChart)
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeChart)
  worldMapInstance?.dispose()
  rankChartInstance?.dispose()
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
  flex: 2; /* 2/3 width */
  height: 100%;
  min-height: 500px;
}
.rank-container {
  flex: 1; /* 1/3 width */
  height: 100%;
  min-height: 500px;
  border-left: 1px solid rgba(0, 243, 255, 0.1);
  padding-left: 20px;
}
:deep(.el-card__body) {
  flex: 1;
  padding: 0; /* Remove default padding to let charts fill */
}
</style>
