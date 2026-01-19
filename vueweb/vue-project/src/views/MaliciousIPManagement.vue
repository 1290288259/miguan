<template>
  <div class="malicious-ip-container">
    <!-- 页面标题 -->
    <el-card class="page-header">
      <template #header>
        <div class="card-header">
          <span>恶意IP管理</span>
        </div>
      </template>
      
      <!-- 查询条件表单 -->
      <el-form :model="queryForm" :inline="true" class="query-form">
        <el-form-item label="关键字">
          <el-input v-model="queryForm.keyword" placeholder="请输入IP/备注/地区" clearable style="width: 200px"></el-input>
        </el-form-item>
        
        <el-form-item label="封禁状态">
          <el-select v-model="queryForm.is_blocked" placeholder="请选择状态" clearable style="width: 160px">
            <el-option label="全部" value=""></el-option>
            <el-option label="已封禁" value="true"></el-option>
            <el-option label="未封禁" value="false"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="威胁等级">
          <el-select v-model="queryForm.threat_level" placeholder="请选择威胁等级" clearable style="width: 160px">
            <el-option label="全部" value=""></el-option>
            <el-option label="低" value="low"></el-option>
            <el-option label="中" value="medium"></el-option>
            <el-option label="高" value="high"></el-option>
            <el-option label="严重" value="critical"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleQuery" :loading="loading">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="resetQuery">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 数据列表 -->
    <el-card class="table-container">
      <el-table 
        :data="ipList" 
        style="width: 100%" 
        v-loading="loading"
        stripe
        border
      >
        <el-table-column prop="ip_address" label="IP地址" width="140" />
        <el-table-column prop="location" label="地理位置" min-width="120" />
        <el-table-column prop="threat_level" label="威胁等级" width="100">
          <template #default="scope">
            <el-tag :type="getThreatLevelType(scope.row.threat_level)">
              {{ getThreatLevelText(scope.row.threat_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="attack_count" label="攻击次数" width="100" sortable />
        <el-table-column prop="is_blocked" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_blocked ? 'danger' : 'success'">
              {{ scope.row.is_blocked ? '已封禁' : '未封禁' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_seen" label="最后活动时间" width="180" sortable />
        <el-table-column prop="notes" label="备注" min-width="150" show-overflow-tooltip />
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button 
              v-if="!scope.row.is_blocked"
              type="danger" 
              size="small" 
              @click="handleBlock(scope.row)"
            >
              封禁
            </el-button>
            <el-button 
              v-else
              type="success" 
              size="small" 
              @click="handleUnblock(scope.row)"
            >
              解封
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 封禁确认弹窗 -->
    <el-dialog v-model="blockDialogVisible" title="封禁IP" width="30%">
      <el-form :model="blockForm">
        <el-form-item label="封禁原因">
          <el-input v-model="blockForm.reason" placeholder="请输入封禁原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="blockDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmBlock" :loading="actionLoading">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from '../utils/axios'

// 数据定义
const loading = ref(false)
const actionLoading = ref(false)
const ipList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const queryForm = reactive({
  keyword: '',
  is_blocked: '',
  threat_level: ''
})

const blockDialogVisible = ref(false)
const currentIp = ref<any>(null)
const blockForm = reactive({
  reason: ''
})

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      per_page: pageSize.value,
      keyword: queryForm.keyword,
      is_blocked: queryForm.is_blocked,
      threat_level: queryForm.threat_level
    }
    
    const res = await axios.get('/malicious-ips', { params })
    ipList.value = res.data.items
    total.value = res.data.pagination.total
  } catch (error) {
    console.error('获取恶意IP列表失败', error)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

// 辅助函数
const getThreatLevelType = (level: string) => {
  const map: Record<string, string> = {
    'low': 'info',
    'medium': 'warning',
    'high': 'danger',
    'critical': 'danger'
  }
  return map[level] || 'info'
}

const getThreatLevelText = (level: string) => {
  const map: Record<string, string> = {
    'low': '低',
    'medium': '中',
    'high': '高',
    'critical': '严重'
  }
  return map[level] || level
}

// 事件处理
const handleQuery = () => {
  currentPage.value = 1
  fetchData()
}

const resetQuery = () => {
  queryForm.keyword = ''
  queryForm.is_blocked = ''
  queryForm.threat_level = ''
  handleQuery()
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchData()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchData()
}

// 封禁相关
const handleBlock = (row: any) => {
  currentIp.value = row
  blockForm.reason = `因频繁攻击封禁 (${row.attack_count}次)`
  blockDialogVisible.value = true
}

const confirmBlock = async () => {
  if (!currentIp.value) return
  
  actionLoading.value = true
  try {
    await axios.post('/malicious-ips/block', {
      ip_address: currentIp.value.ip_address,
      reason: blockForm.reason
    })
    ElMessage.success('封禁成功')
    blockDialogVisible.value = false
    fetchData()
  } catch (error) {
    console.error('封禁失败', error)
    // 错误处理通常由axios拦截器处理，但这里也可以额外提示
  } finally {
    actionLoading.value = false
  }
}

// 解封相关
const handleUnblock = (row: any) => {
  ElMessageBox.confirm(
    `确定要解封IP ${row.ip_address} 吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        await axios.post('/malicious-ips/unblock', {
          ip_address: row.ip_address
        })
        ElMessage.success('解封成功')
        fetchData()
      } catch (error) {
        console.error('解封失败', error)
      }
    })
    .catch(() => {})
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.malicious-ip-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.query-form .el-form-item {
  margin-bottom: 0;
  margin-right: 18px;
}

.table-container {
  min-height: 500px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>