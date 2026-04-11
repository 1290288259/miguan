<template>
  <div class="chart-view-container">
    <el-card shadow="hover" class="chart-card">
      <template #header>
        <div class="card-header">
          <span>攻击趋势 ({{ dateRangeLabel }})</span>
          <el-radio-group v-model="currentDays" size="small" @change="handleRangeChange">
            <el-radio-button :label="7">7天</el-radio-button>
            <el-radio-button :label="30">30天</el-radio-button>
            <el-radio-button :label="90">季度</el-radio-button>
            <el-radio-button :label="180">半年</el-radio-button>
            <el-radio-button :label="360">一年</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div ref="trendChart" class="chart-container"></div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import axios from '@/utils/axios'

// Light Theme Colors
const textColor = '#606266'
const axisColor = '#dcdfe6'

// Chart refs
const trendChart = ref<HTMLElement | null>(null)
let trendChartInstance: echarts.ECharts | null = null

// Date range selection
const currentDays = ref(7)

const dateRangeLabel = computed(() => {
  const map: Record<number, string> = {
    7: '近7天',
    30: '近30天',
    90: '近季度',
    180: '近半年',
    360: '近一年'
  }
  return map[currentDays.value] || ''
})

const handleRangeChange = () => {
  initTrendChart()
}

const initTrendChart = async () => {
  if (!trendChart.value) return
  
  // If instance exists, we reuse it, otherwise init
  if (!trendChartInstance) {
    trendChartInstance = echarts.init(trendChart.value)
  } else {
    trendChartInstance.showLoading({
        text: '加载中...',
        color: '#409eff',
        textColor: '#606266',
        maskColor: 'rgba(255, 255, 255, 0.8)',
  }
  
  try {
    const granularity = currentDays.value > 90 ? 'month' : 'day'
    const res: any = await axios.get(`/dashboard/trend?days=${currentDays.value}&granularity=${granularity}`)
    
    trendChartInstance.hideLoading()
    
    if (res.code === 200) {
      const data = res.data
      const dates = data.map((item: any) => item.date)
      const counts = data.map((item: any) => item.count)
      
      trendChartInstance.setOption({
        tooltip: { 
          trigger: 'axis',
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          borderColor: '#e4e7ed',
          textStyle: { color: '#303133' }
        },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { 
          type: 'category', 
          data: dates,
          axisLine: { lineStyle: { color: axisColor } },
          axisLabel: { color: '#606266', fontSize: 12, fontWeight: 'normal' }
        },
        yAxis: { 
          type: 'value',
          splitLine: { lineStyle: { color: '#ebeef5' } },
          axisLabel: { color: '#606266' }
        },
        series: [{ 
          data: counts, 
          type: 'line', 
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          areaStyle: {
             color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(64, 158, 255, 0.5)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.0)' }
            ])
          },
          itemStyle: { 
            color: '#409eff',
            shadowColor: '#409eff',
            shadowBlur: 5
          }
        }]
      })
    }
  } catch (error: any) {
    console.error('Failed to fetch trend data', error)
    trendChartInstance?.hideLoading()
  }
}

const resizeChart = () => {
  trendChartInstance?.resize()
}

onMounted(() => {
  nextTick(() => {
    initTrendChart()
    window.addEventListener('resize', resizeChart)
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeChart)
  trendChartInstance?.dispose()
})
</script>

<style scoped>
.chart-view-container {
  padding: 20px;
  height: calc(100vh - 140px); /* Adjust for headers */
}
.chart-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.chart-container {
  height: 500px;
  width: 100%;
}
:deep(.el-card__body) {
  flex: 1;
}
</style>
