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
        
        <!-- AI 分析结果部分 -->
        <el-descriptions-item label="AI分析结果" :span="2" class-name="ai-analysis-section">
          <div v-if="currentLog.ai_attack_type" class="ai-analysis-content">
            <div class="ai-header">
              <el-tag :type="currentLog.ai_attack_type === 'Normal' ? 'success' : 'danger'" effect="dark">
                AI判定: {{ currentLog.ai_attack_type }}
              </el-tag>
              <el-tag type="info" effect="plain" class="ml-2">
                置信度: {{ (currentLog.ai_confidence * 100).toFixed(1) }}%
              </el-tag>
            </div>
            <div class="ai-detail">
              <p><strong>分析详情：</strong></p>
              <p>{{ currentLog.ai_analysis_result }}</p>
            </div>
          </div>
          <div v-else>
            <el-tag type="info">AI分析中或未进行分析</el-tag>
          </div>
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
    
    <!-- 导出日志对话框 -->
    <el-dialog v-model="exportDialogVisible" title="导出日志" width="500px">
      <el-form :model="exportForm" label-width="100px">
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="exportForm.dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
          <div class="form-tip" style="color: #909399; font-size: 12px; margin-top: 5px;">
            注意：导出时间范围不能超过一年
          </div>
        </el-form-item>
        
        <el-form-item label="攻击类型">
          <el-select v-model="exportForm.attack_type" placeholder="请选择攻击类型" clearable style="width: 100%">
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
          <el-select v-model="exportForm.threat_level" placeholder="请选择威胁等级" clearable style="width: 100%">
            <el-option label="全部" value=""></el-option>
            <el-option label="低" value="low"></el-option>
            <el-option label="中" value="medium"></el-option>
            <el-option label="高" value="high"></el-option>
            <el-option label="严重" value="critical"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="协议类型">
          <el-select v-model="exportForm.protocol" placeholder="请选择协议类型" clearable style="width: 100%">
            <el-option label="全部" value=""></el-option>
            <el-option label="HTTP" value="HTTP"></el-option>
            <el-option label="HTTPS" value="HTTPS"></el-option>
            <el-option label="SSH" value="SSH"></el-option>
            <el-option label="FTP" value="FTP"></el-option>
            <el-option label="TELNET" value="TELNET"></el-option>
            <el-option label="RDP" value="RDP"></el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="源IP">
          <el-input v-model="exportForm.source_ip" placeholder="请输入源IP" clearable></el-input>
        </el-form-item>

        <el-form-item label="目标IP">
          <el-input v-model="exportForm.target_ip" placeholder="请输入目标IP" clearable></el-input>
        </el-form-item>

        <el-form-item label="目标端口">
          <el-input v-model="exportForm.target_port" placeholder="请输入目标端口" clearable type="number"></el-input>
        </el-form-item>

        <el-form-item label="是否恶意">
          <el-select v-model="exportForm.is_malicious" placeholder="请选择" clearable style="width: 100%">
            <el-option label="全部" value=""></el-option>
            <el-option label="是" value="true"></el-option>
            <el-option label="否" value="false"></el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="是否封禁">
          <el-select v-model="exportForm.is_blocked" placeholder="请选择" clearable style="width: 100%">
            <el-option label="全部" value=""></el-option>
            <el-option label="是" value="true"></el-option>
            <el-option label="否" value="false"></el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="exportDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmExport" :loading="exportLoading">确认导出</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Download, View } from '@element-plus/icons-vue'
import axios from '../utils/axios'
import rawAxios from 'axios'

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

// 导出日志相关数据
const exportDialogVisible = ref(false)
const exportLoading = ref(false)
const exportForm = reactive({
  dateRange: [] as any[],
  attack_type: '',
  threat_level: '',
  source_ip: '',
  target_ip: '',
  target_port: '',
  protocol: '',
  is_malicious: '',
  is_blocked: ''
})

// 导出日志
const exportLogs = () => {
  exportDialogVisible.value = true
}

// 确认导出
const confirmExport = async () => {
  if (exportForm.dateRange && exportForm.dateRange.length === 2) {
    const startTime = new Date(exportForm.dateRange[0])
    const endTime = new Date(exportForm.dateRange[1])
    const diffTime = Math.abs(endTime.getTime() - startTime.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays > 365) {
      ElMessage.warning('导出时间范围不能超过一年')
      return
    }
  }

  exportLoading.value = true
  try {
    const params: any = {}
    
    if (exportForm.attack_type) {
      params.attack_type = exportForm.attack_type
    }
    
    if (exportForm.threat_level) {
      params.threat_level = exportForm.threat_level
    }
    
    if (exportForm.source_ip) {
      params.source_ip = exportForm.source_ip
    }
    
    if (exportForm.target_ip) {
      params.target_ip = exportForm.target_ip
    }
    
    if (exportForm.target_port) {
      params.target_port = exportForm.target_port
    }
    
    if (exportForm.protocol) {
      params.protocol = exportForm.protocol
    }
    
    if (exportForm.is_malicious) {
      params.is_malicious = exportForm.is_malicious
    }
    
    if (exportForm.is_blocked) {
      params.is_blocked = exportForm.is_blocked
    }
    
    if (exportForm.dateRange && exportForm.dateRange.length === 2) {
      params.start_time = exportForm.dateRange[0]
      params.end_time = exportForm.dateRange[1]
    }
    
    // 获取token
    const token = localStorage.getItem('token')
    
    // 使用原生axios请求以获取Blob数据
    const response = await rawAxios.get('/api/logs/export', {
      params,
      responseType: 'blob',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    
    // 获取文件名
    let filename = 'logs_export.csv'
    const contentDisposition = response.headers['content-disposition']
    if (contentDisposition) {
      const fileNameMatch = contentDisposition.match(/filename=(.+)/)
      if (fileNameMatch.length === 2) {
        filename = fileNameMatch[1]
      }
    }
    
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    
    // 清理
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
    exportDialogVisible.value = false
    
  } catch (error) {
    console.error('导出日志出错:', error)
    ElMessage.error('导出失败，请稍后重试')
  } finally {
    exportLoading.value = false
  }
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

.ai-analysis-content {
  background: rgba(0, 243, 255, 0.05);
  padding: 10px;
  border-radius: 4px;
  border: 1px solid rgba(0, 243, 255, 0.2);
}

.ai-header {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
}

.ml-2 {
  margin-left: 10px;
}

.ai-detail p {
  margin: 5px 0;
  line-height: 1.5;
  color: var(--scifi-text-color);
}
</style>