<template>
  <div class="dashboard-container">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>总攻击数</span>
              <el-tag type="danger">Total</el-tag>
            </div>
          </template>
          <div class="stat-value">{{ summary.total_attacks }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>今日攻击</span>
              <el-tag type="warning">Today</el-tag>
            </div>
          </template>
          <div class="stat-value">{{ summary.today_attacks }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>恶意IP数</span>
              <el-tag type="info">Malicious IPs</el-tag>
            </div>
          </template>
          <div class="stat-value">{{ summary.malicious_ips }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>攻击趋势 (近7天)</template>
          <div ref="trendChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>攻击类型分布</template>
          <div ref="typeChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="chart-row">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>恶意IP来源排名 (Top Locations)</template>
          <div ref="mapChart" class="chart-container map-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Debug Info -->
    <!-- Removed Debug Info -->
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import axios from '@/utils/axios'

// Summary data
const summary = ref({
  total_attacks: 0,
  today_attacks: 0,
  malicious_ips: 0
})

// Sci-Fi Theme Colors
const scifiColors = ['#00f3ff', '#bc13fe', '#00ff9d', '#ff0055', '#ffe600']
const textColor = '#e0f7fa'
const axisColor = 'rgba(0, 243, 255, 0.3)'

// Chart refs
const trendChart = ref<HTMLElement | null>(null)
const typeChart = ref<HTMLElement | null>(null)
const mapChart = ref<HTMLElement | null>(null)

let trendChartInstance: echarts.ECharts | null = null
let typeChartInstance: echarts.ECharts | null = null
let mapChartInstance: echarts.ECharts | null = null

// Fetch data functions
const fetchSummary = async () => {
  try {
    const res: any = await axios.get('/dashboard/summary')
    if (res.code === 200) {
      summary.value = res.data
    }
  } catch (error: any) {
    console.error('Failed to fetch summary', error)
  }
}

const initTrendChart = async () => {
  if (!trendChart.value) return
  trendChartInstance = echarts.init(trendChart.value)
  
  try {
    const res: any = await axios.get('/dashboard/trend?days=7')
    if (res.code === 200) {
      const data = res.data
      const dates = data.map((item: any) => item.date)
      const counts = data.map((item: any) => item.count)
      
      trendChartInstance.setOption({
        tooltip: { 
          trigger: 'axis',
          backgroundColor: 'rgba(5, 11, 20, 0.9)',
          borderColor: '#00f3ff',
          textStyle: { color: '#e0f7fa' }
        },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { 
          type: 'category', 
          data: dates,
          axisLine: { lineStyle: { color: axisColor } },
          axisLabel: { color: textColor }
        },
        yAxis: { 
          type: 'value',
          splitLine: { lineStyle: { color: 'rgba(0, 243, 255, 0.1)' } },
          axisLabel: { color: textColor }
        },
        series: [{ 
          data: counts, 
          type: 'line', 
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          areaStyle: {
             color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(0, 243, 255, 0.5)' },
              { offset: 1, color: 'rgba(0, 243, 255, 0.0)' }
            ])
          },
          itemStyle: { 
            color: '#00f3ff',
            shadowColor: '#00f3ff',
            shadowBlur: 10
          }
        }]
      })
    }
  } catch (error: any) {
    console.error('Failed to fetch trend data', error)
  }
}

const initTypeChart = async () => {
  if (!typeChart.value) return
  typeChartInstance = echarts.init(typeChart.value)
  
  try {
    const res: any = await axios.get('/dashboard/types')
    if (res.code === 200) {
      const data = res.data || []
      
      typeChartInstance.setOption({
        tooltip: { 
          trigger: 'item',
          backgroundColor: 'rgba(5, 11, 20, 0.9)',
          borderColor: '#00f3ff',
          textStyle: { color: '#e0f7fa' }
        },
        legend: { 
          top: '5%', 
          left: 'center',
          textStyle: { color: textColor }
        },
        series: [{
          name: '攻击类型',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#050b14',
            borderWidth: 2
          },
          label: {
            show: true,
            position: 'outside',
            formatter: '{b}: {d}%',
            color: textColor
          },
          emphasis: {
            label: { show: true, fontSize: 20, fontWeight: 'bold', color: '#00f3ff' },
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          },
          labelLine: { show: true, lineStyle: { color: axisColor } },
          data: data,
          color: scifiColors
        }]
      })
    }
  } catch (error) {
    console.error('Failed to fetch type data', error)
  }
}

const initMapChart = async () => {
  if (!mapChart.value) return
  mapChartInstance = echarts.init(mapChart.value)
  
  try {
    const res: any = await axios.get('/dashboard/map')
    if (res.code === 200) {
      const data = res.data || []
      // transform for bar chart
      const locations = data.map((item: any) => item.name || 'Unknown')
      const counts = data.map((item: any) => item.value)
      
      mapChartInstance.setOption({
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
          axisLabel: { color: textColor },
          splitLine: { lineStyle: { color: 'rgba(0, 243, 255, 0.1)' } }
        },
        yAxis: { 
          type: 'category', 
          data: locations,
          axisLabel: { color: textColor },
          axisLine: { lineStyle: { color: axisColor } }
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
          }
        }]
      })
    }
  } catch (error) {
    console.error('Failed to fetch map data', error)
  }
}

const resizeCharts = () => {
  trendChartInstance?.resize()
  typeChartInstance?.resize()
  mapChartInstance?.resize()
}

onMounted(() => {
  fetchSummary()
  nextTick(() => {
    initTrendChart()
    initTypeChart()
    initMapChart()
    window.addEventListener('resize', resizeCharts)
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
  trendChartInstance?.dispose()
  typeChartInstance?.dispose()
  mapChartInstance?.dispose()
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}
.stat-value {
  font-size: 28px;
  font-weight: bold;
  text-align: center;
  color: #303133;
  margin-top: 10px;
}
.chart-row {
  margin-top: 20px;
}
.chart-container {
  height: 350px;
}
.map-container {
  height: 400px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
