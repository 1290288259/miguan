<template>
  <div class="chart-view-container">
    <el-card shadow="hover" class="chart-card">
      <template #header>
        <div class="card-header">
          <span>攻击类型分布</span>
        </div>
      </template>
      <div ref="typeChart" class="chart-container"></div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import axios from '@/utils/axios'

// Theme Colors (Light/Pastel)
const lightColors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc']

// Chart refs
const typeChart = ref<HTMLElement | null>(null)
let typeChartInstance: echarts.ECharts | null = null

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
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          borderColor: '#e4e7ed',
          textStyle: { color: '#303133' }
        },
        legend: { 
          top: '5%', 
          left: 'center',
          textStyle: { color: '#606266', fontSize: 14 }
        },
        series: [{
          name: '攻击类型',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: true,
            position: 'outside',
            formatter: '{b}: {d}%',
            color: '#606266',
            fontSize: 14,
            fontWeight: 'normal'
          },
          emphasis: {
            label: { show: true, fontSize: 16, fontWeight: 'bold', color: '#303133' },
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.1)'
            }
          },
          data: data,
          color: lightColors
        }]
      })
    }
  } catch (error) {
    console.error('Failed to fetch type data', error)
  }
}

const resizeChart = () => {
  typeChartInstance?.resize()
}

onMounted(() => {
  nextTick(() => {
    initTypeChart()
    window.addEventListener('resize', resizeChart)
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeChart)
  typeChartInstance?.dispose()
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
.chart-container {
  height: 500px;
  width: 100%;
}
:deep(.el-card__body) {
  flex: 1;
}
</style>
