<template>
  <div class="overview-container">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <span>总攻击数</span>
              <el-tag type="danger">Total</el-tag>
            </div>
          </template>
          <div class="stat-value">{{ summary.total_attacks }}</div>
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
          <div class="stat-value">{{ summary.today_attacks }}</div>
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
          <div class="stat-value">{{ summary.malicious_ips }}</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from '@/utils/axios'

// Summary data
const summary = ref({
  total_attacks: 0,
  today_attacks: 0,
  malicious_ips: 0
})

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

onMounted(() => {
  fetchSummary()
})
</script>

<style scoped>
.overview-container {
  padding: 20px;
}
.stat-value {
  font-size: 36px;
  font-weight: bold;
  text-align: center;
  color: #303133;
  margin-top: 20px;
  margin-bottom: 20px;
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
</style>
