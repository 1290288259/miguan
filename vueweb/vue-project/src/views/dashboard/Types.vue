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

// Theme Colors
const scifiColors = ['#00f3ff', '#bc13fe', '#00ff9d', '#ff0055', '#ffe600']

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
          backgroundColor: 'rgba(5, 11, 20, 0.9)',
          borderColor: '#00f3ff',
          textStyle: { color: '#e0f7fa' }
        },
        legend: { 
          top: '5%', 
          left: 'center',
          textStyle: { color: '#00f3ff', fontSize: 14 }
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
            color: '#00f3ff',
            fontSize: 14,
            fontWeight: 'bold'
          },
          emphasis: {
            label: { show: true, fontSize: 20, fontWeight: 'bold', color: '#fff' },
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          },
          data: data,
          color: scifiColors
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
