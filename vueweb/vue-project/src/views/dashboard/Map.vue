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
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import axios from '@/utils/axios'

// Chart refs
const worldMapChart = ref<HTMLElement | null>(null)
const rankChart = ref<HTMLElement | null>(null)
let worldMapInstance: echarts.ECharts | null = null
let rankChartInstance: echarts.ECharts | null = null

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
      
      // Data for Rank Chart (Bar)
      const locations = data.map((item: any) => item.name || 'Unknown')
      const counts = data.map((item: any) => item.value)
      
      // Data for Map Chart
      // Map data needs to match ECharts world map names. 
      // Assuming backend returns standard English names or we might need mapping.
      const mapData = data.map((item: any) => ({
        name: item.name,
        value: item.value
      }))

      // Render World Map
      worldMapInstance.setOption({
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(5, 11, 20, 0.9)',
          borderColor: '#00f3ff',
          textStyle: { color: '#e0f7fa' },
          formatter: '{b}: {c} 次攻击'
        },
        visualMap: {
          min: 0,
          max: Math.max(...counts, 10), // Dynamic max
          text: ['High', 'Low'],
          realtime: false,
          calculable: true,
          inRange: {
            color: ['#e0f7fa', '#00f3ff', '#004a80'] // Light to Dark Cyan
          },
          textStyle: { color: '#e0f7fa' },
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
            scaleLimit: {
              min: 0.8,
              max: 5
            },
            emphasis: {
              label: { show: true, color: '#fff' },
              itemStyle: { areaColor: '#00f3ff' }
            },
            itemStyle: {
              areaColor: '#323c48',
              borderColor: '#111'
            },
            data: mapData
          }
        ]
      })

      // Render Rank Chart
      rankChartInstance.setOption({
        title: {
          text: 'Top 10 来源排名',
          textStyle: { color: '#00f3ff', fontSize: 16 },
          left: 'center'
        },
        tooltip: { 
          trigger: 'axis', 
          axisPointer: { type: 'shadow' },
          backgroundColor: 'rgba(5, 11, 20, 0.9)',
          borderColor: '#00f3ff',
          textStyle: { color: '#e0f7fa' }
        },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { 
          type: 'value',
          axisLabel: { color: '#00f3ff' },
          splitLine: { lineStyle: { color: 'rgba(0, 243, 255, 0.1)' } }
        },
        yAxis: { 
          type: 'category', 
          data: locations,
          axisLabel: { color: '#00f3ff', fontWeight: 'bold' },
          axisLine: { lineStyle: { color: 'rgba(0, 243, 255, 0.3)' } },
          inverse: true // Rank from top to bottom
        },
        series: [{ 
          type: 'bar', 
          data: counts,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
              { offset: 0, color: '#83bff6' },
              { offset: 0.5, color: '#188df0' },
              { offset: 1, color: '#188df0' }
            ])
          },
          label: {
            show: true,
            position: 'right',
            color: '#00f3ff'
          }
        }]
      })
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
