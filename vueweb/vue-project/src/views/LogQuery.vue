<template>
  <div class="log-query-container">
    <!-- 页面标题 -->
    <el-card class="page-header">
      <template #header>
        <div class="card-header">
          <span>日志查询</span>
        </div>
      </template>
      
      <!-- 查询条件表单 -->
      <el-form :model="queryForm" :inline="true" class="query-form">
        <el-form-item label="关键字">
          <el-input 
            v-model="queryForm.keyword" 
            placeholder="请输入关键字" 
            clearable 
            style="width: 200px"
            @keyup.enter="handleQuery"
          ></el-input>
        </el-form-item>
        
        <el-form-item label="攻击类型">
          <el-select v-model="queryForm.attack_type" placeholder="请选择攻击类型" clearable style="width: 160px">
            <el-option label="全部" value=""></el-option>
            <el-option label="SQL注入" value="SQL注入"></el-option>
            <el-option label="XSS" value="XSS"></el-option>
            <el-option label="命令注入" value="命令注入"></el-option>
            <el-option label="目录遍历" value="目录遍历"></el-option>
            <el-option label="文件包含" value="文件包含"></el-option>
            <el-option label="CSRF" value="CSRF"></el-option>
            <el-option label="SSRF" value="SSRF"></el-option>
            <el-option label="暴力破解" value="暴力破解"></el-option>
            <el-option label="扫描探测" value="扫描探测"></el-option>
            <el-option label="拒绝服务" value="拒绝服务"></el-option>
            <el-option label="凭证填充" value="凭证填充"></el-option>
            <el-option label="字典攻击" value="字典攻击"></el-option>
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
        
        <el-form-item label="协议类型">
          <el-select v-model="queryForm.protocol" placeholder="请选择协议类型" clearable style="width: 160px">
            <el-option label="全部" value=""></el-option>
            <el-option label="HTTP" value="HTTP"></el-option>
            <el-option label="HTTPS" value="HTTPS"></el-option>
            <el-option label="SSH" value="SSH"></el-option>
            <el-option label="FTP" value="FTP"></el-option>
            <el-option label="TELNET" value="TELNET"></el-option>
            <el-option label="RDP" value="RDP"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="攻击时间范围">
          <el-date-picker
            v-model="queryForm.dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
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
    
    <!-- 日志列表 -->
    <el-card class="log-table-container">
      <template #header>
        <div class="card-header">
          <span>日志列表</span>
          <el-button type="primary" size="small" @click="exportLogs">
            <el-icon><Download /></el-icon>
            导出日志
          </el-button>
        </div>
      </template>
      
      <el-table 
        :data="logList" 
        style="width: 100%" 
        v-loading="loading"
        stripe
        border
      >
        <el-table-column prop="id" label="ID" width="80" />
        
        <el-table-column prop="attack_time" label="攻击时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.attack_time) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="attack_type" label="攻击类型" width="120">
          <template #default="scope">
            <el-tag :type="getAttackTypeTagType(scope.row.attack_type)">
              {{ scope.row.attack_type }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="threat_level" label="威胁等级" width="100">
          <template #default="scope">
            <el-tag :type="getThreatLevelTagType(scope.row.threat_level)">
              {{ getThreatLevelText(scope.row.threat_level) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="source_ip" label="源IP" width="130" />
        
        <el-table-column prop="target_ip" label="目标IP" width="130" />
        
        <el-table-column prop="target_port" label="目标端口" width="100" />
        
        <el-table-column prop="protocol" label="协议" width="80" />
        
        <el-table-column prop="is_malicious" label="恶意IP" width="90">
          <template #default="scope">
            <el-tag :type="scope.row.is_malicious ? 'danger' : 'success'">
              {{ scope.row.is_malicious ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="is_blocked" label="已封禁" width="90">
          <template #default="scope">
            <el-tag :type="scope.row.is_blocked ? 'danger' : 'success'">
              {{ scope.row.is_blocked ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="scope">
            <el-button type="primary" size="small" @click="showLogDetail(scope.row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.perPage"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    
    <!-- 日志详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="日志详情" width="60%">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="日志ID">{{ currentLog.id }}</el-descriptions-item>
        <el-descriptions-item label="攻击时间">{{ formatDateTime(currentLog.attack_time) }}</el-descriptions-item>
        <el-descriptions-item label="攻击类型">{{ currentLog.attack_type }}</el-descriptions-item>
        <el-descriptions-item label="威胁等级">
          <el-tag :type="getThreatLevelTagType(currentLog.threat_level)">
            {{ getThreatLevelText(currentLog.threat_level) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="源IP">{{ currentLog.source_ip }}</el-descriptions-item>
        <el-descriptions-item label="源端口">{{ currentLog.source_port }}</el-descriptions-item>
        <el-descriptions-item label="目标IP">{{ currentLog.target_ip }}</el-descriptions-item>
        <el-descriptions-item label="目标端口">{{ currentLog.target_port }}</el-descriptions-item>
        <el-descriptions-item label="协议">{{ currentLog.protocol }}</el-descriptions-item>
        <el-descriptions-item label="请求路径">{{ currentLog.request_path }}</el-descriptions-item>
        <el-descriptions-item label="攻击描述" :span="2">{{ currentLog.attack_description }}</el-descriptions-item>
        <el-descriptions-item label="载荷" :span="2">{{ currentLog.payload }}</el-descriptions-item>
        <el-descriptions-item label="原始日志" :span="2">
          <pre>{{ currentLog.raw_log }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ currentLog.notes }}</el-descriptions-item>
        <el-descriptions-item label="是否恶意IP">
          <el-tag :type="currentLog.is_malicious ? 'danger' : 'success'">
            {{ currentLog.is_malicious ? '是' : '否' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="是否已封禁">
          <el-tag :type="currentLog.is_blocked ? 'danger' : 'success'">
            {{ currentLog.is_blocked ? '是' : '否' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="封禁时间">{{ formatDateTime(currentLog.blocked_time) || '未封禁' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Download, View } from '@element-plus/icons-vue'
import axios from '../utils/axios'

// 查询表单数据
const queryForm = reactive({
  keyword: '',
  attack_type: '',
  threat_level: '',
  protocol: '',
  dateRange: []
})

// 分页数据
const pagination = reactive({
  page: 1,
  perPage: 10,
  total: 0
})

// 日志列表数据
const logList = ref([])
const loading = ref(false)

// 详情对话框
const detailDialogVisible = ref(false)
const currentLog = ref<any>({})

// 获取日志列表
const getLogList = async () => {
  loading.value = true
  try {
    // 构建查询参数
    const params: any = {
      page: pagination.page,
      per_page: pagination.perPage
    }
    
    // 添加筛选条件
    if (queryForm.keyword) {
      params.keyword = queryForm.keyword
    }
    
    if (queryForm.attack_type) {
      params.attack_type = queryForm.attack_type
    }
    
    if (queryForm.threat_level) {
      params.threat_level = queryForm.threat_level
    }
    
    if (queryForm.protocol) {
      params.protocol = queryForm.protocol
    }
    
    if (queryForm.dateRange && queryForm.dateRange.length === 2) {
      params.start_time = queryForm.dateRange[0]
      params.end_time = queryForm.dateRange[1]
    }
    
    const response: any = await axios.get('/logs', { params })
    
    if (response.code === 200) {
      logList.value = response.data.logs
      pagination.total = response.data.pagination.total
    } else {
      ElMessage.error(response.msg || '获取日志列表失败')
    }
  } catch (error) {
    console.error('获取日志列表出错:', error)
    ElMessage.error('获取日志列表失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 查询按钮点击事件
const handleQuery = () => {
  pagination.page = 1
  getLogList()
}

// 重置查询条件
const resetQuery = () => {
  queryForm.keyword = ''
  queryForm.attack_type = ''
  queryForm.threat_level = ''
  queryForm.protocol = ''
  queryForm.dateRange = []
  pagination.page = 1
  getLogList()
}

// 每页显示数量变化
const handleSizeChange = (val: number) => {
  pagination.perPage = val
  pagination.page = 1
  getLogList()
}

// 当前页变化
const handleCurrentChange = (val: number) => {
  pagination.page = val
  getLogList()
}

// 显示日志详情
const showLogDetail = (row: any) => {
  currentLog.value = { ...row }
  detailDialogVisible.value = true
}

// 导出日志
const exportLogs = () => {
  ElMessage.info('导出功能开发中...')
}

// 格式化日期时间
const formatDateTime = (dateTime: string) => {
  if (!dateTime) return ''
  return new Date(dateTime).toLocaleString('zh-CN')
}

// 获取威胁等级文本
const getThreatLevelText = (level: string) => {
  const levelMap: { [key: string]: string } = {
    'low': '低',
    'medium': '中',
    'high': '高',
    'critical': '严重'
  }
  return levelMap[level] || level
}

// 获取威胁等级标签类型
const getThreatLevelTagType = (level: string) => {
  const typeMap: { [key: string]: string } = {
    'low': 'info',
    'medium': 'warning',
    'high': 'danger',
    'critical': 'danger'
  }
  return typeMap[level] || 'info'
}

// 获取攻击类型标签类型
const getAttackTypeTagType = (type: string) => {
  // 根据攻击类型返回不同的标签类型
  if (['SQL注入', '命令注入', 'XSS'].includes(type)) {
    return 'danger'
  } else if (['暴力破解', '字典攻击', '凭证填充'].includes(type)) {
    return 'warning'
  } else {
    return 'info'
  }
}

// 页面加载时获取日志列表
onMounted(() => {
  getLogList()
})
</script>

<style scoped>
.log-query-container {
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

.query-form {
  margin-top: 10px;
}

.log-table-container {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 200px;
  overflow-y: auto;
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
}
</style>