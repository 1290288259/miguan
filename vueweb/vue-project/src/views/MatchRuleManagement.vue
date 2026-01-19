<template>
  <div class="match-rule-container">
    <!-- 页面标题 -->
    <el-card class="page-header">
      <template #header>
        <div class="card-header">
          <span>匹配规则管理</span>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            新增规则
          </el-button>
        </div>
      </template>
      
      <!-- 查询条件表单 -->
      <el-form :model="queryForm" :inline="true" class="query-form">
        <el-form-item label="关键字">
          <el-input v-model="queryForm.keyword" placeholder="请输入关键字" clearable style="width: 200px"></el-input>
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
        
        <el-form-item label="状态">
          <el-select v-model="queryForm.is_enabled" placeholder="请选择状态" clearable style="width: 160px">
            <el-option label="全部" value=""></el-option>
            <el-option label="启用" :value="true"></el-option>
            <el-option label="禁用" :value="false"></el-option>
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
    
    <!-- 规则列表 -->
    <el-card class="rule-table-container">
      <template #header>
        <div class="card-header">
          <span>规则列表</span>
        </div>
      </template>
      
      <el-table 
        :data="ruleList" 
        style="width: 100%" 
        v-loading="loading"
        stripe
        border
      >
        <el-table-column prop="id" label="ID" width="80" />
        
        <el-table-column prop="name" label="规则名称" width="150" />
        
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
        
        <el-table-column prop="regex_pattern" label="正则表达式" width="200" show-overflow-tooltip />
        
        <el-table-column prop="match_field" label="匹配字段" width="120" />
        
        <el-table-column prop="priority" label="优先级" width="100" sortable />
        
        <el-table-column prop="match_count" label="匹配次数" width="100" />
        
        <el-table-column prop="is_enabled" label="状态" width="100">
          <template #default="scope">
            <el-switch
              v-model="scope.row.is_enabled"
              @change="toggleRuleStatus(scope.row)"
            />
          </template>
        </el-table-column>
        
        <el-table-column prop="auto_block" label="自动封禁" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.auto_block ? 'danger' : 'success'">
              {{ scope.row.auto_block ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button type="primary" size="small" @click="showEditDialog(scope.row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button type="danger" size="small" @click="deleteRule(scope.row)">
              <el-icon><Delete /></el-icon>
              删除
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
    
    <!-- 创建/编辑规则对话框 -->
    <el-dialog v-model="ruleDialogVisible" :title="dialogTitle" width="60%">
      <el-form :model="ruleForm" :rules="ruleFormRules" ref="ruleFormRef" label-width="120px">
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="ruleForm.name" placeholder="请输入规则名称" />
        </el-form-item>
        
        <el-form-item label="攻击类型" prop="attack_type">
          <el-select v-model="ruleForm.attack_type" placeholder="请选择攻击类型">
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
        
        <el-form-item label="威胁等级" prop="threat_level">
          <el-select v-model="ruleForm.threat_level" placeholder="请选择威胁等级">
            <el-option label="低" value="low"></el-option>
            <el-option label="中" value="medium"></el-option>
            <el-option label="高" value="high"></el-option>
            <el-option label="严重" value="critical"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="正则表达式" prop="regex_pattern">
          <el-input 
            v-model="ruleForm.regex_pattern" 
            type="textarea" 
            :rows="4"
            placeholder="请输入正则表达式"
          />
        </el-form-item>
        
        <el-form-item label="匹配字段" prop="match_field">
          <el-select v-model="ruleForm.match_field" placeholder="请选择匹配字段">
            <el-option label="原始日志" value="raw_log"></el-option>
            <el-option label="请求路径" value="request_path"></el-option>
            <el-option label="载荷" value="payload"></el-option>
            <el-option label="用户代理" value="user_agent"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="规则描述">
          <el-input 
            v-model="ruleForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入规则描述"
          />
        </el-form-item>
        
        <el-form-item label="优先级" prop="priority">
          <el-input-number v-model="ruleForm.priority" :min="1" :max="999" />
        </el-form-item>
        
        <el-form-item label="是否启用">
          <el-switch v-model="ruleForm.is_enabled" />
        </el-form-item>
        
        <el-form-item label="自动封禁">
          <el-switch v-model="ruleForm.auto_block" />
        </el-form-item>
        
        <el-form-item label="封禁时长（小时）">
          <el-input-number v-model="ruleForm.block_duration" :min="0" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="ruleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRuleForm" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Edit, Delete } from '@element-plus/icons-vue'
import axios from '../utils/axios'

// 查询表单数据
const queryForm = reactive({
  keyword: '',
  attack_type: '',
  threat_level: '',
  is_enabled: ''
})

// 分页数据
const pagination = reactive({
  page: 1,
  perPage: 10,
  total: 0
})

// 规则列表数据
const ruleList = ref([])
const loading = ref(false)

// 规则对话框
const ruleDialogVisible = ref(false)
const dialogTitle = computed(() => {
  return ruleForm.id ? '编辑规则' : '新增规则'
})
const submitting = ref(false)
const ruleFormRef = ref()

// 规则表单数据
const ruleForm = reactive({
  id: null,
  name: '',
  attack_type: '',
  regex_pattern: '',
  threat_level: 'medium',
  description: '',
  match_field: 'raw_log',
  is_enabled: true,
  priority: 100,
  auto_block: false,
  block_duration: 0
})

// 表单验证规则
const ruleFormRules = {
  name: [
    { required: true, message: '请输入规则名称', trigger: 'blur' }
  ],
  attack_type: [
    { required: true, message: '请选择攻击类型', trigger: 'change' }
  ],
  regex_pattern: [
    { required: true, message: '请输入正则表达式', trigger: 'blur' }
  ],
  threat_level: [
    { required: true, message: '请选择威胁等级', trigger: 'change' }
  ],
  match_field: [
    { required: true, message: '请选择匹配字段', trigger: 'change' }
  ],
  priority: [
    { required: true, message: '请输入优先级', trigger: 'blur' }
  ]
}

// 获取规则列表
const getRuleList = async () => {
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
    
    if (queryForm.is_enabled !== '') {
      params.is_enabled = queryForm.is_enabled
    }
    
    const response = await axios.get('/match-rules', { params })
    
    if (response.success) {
      ruleList.value = response.data.rules
      pagination.total = response.data.pagination.total
    } else {
      ElMessage.error(response.message || '获取规则列表失败')
    }
  } catch (error) {
    console.error('获取规则列表出错:', error)
    ElMessage.error('获取规则列表失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 查询按钮点击事件
const handleQuery = () => {
  pagination.page = 1
  getRuleList()
}

// 重置查询条件
const resetQuery = () => {
  queryForm.keyword = ''
  queryForm.attack_type = ''
  queryForm.threat_level = ''
  queryForm.is_enabled = ''
  pagination.page = 1
  getRuleList()
}

// 每页显示数量变化
const handleSizeChange = (val: number) => {
  pagination.perPage = val
  pagination.page = 1
  getRuleList()
}

// 当前页变化
const handleCurrentChange = (val: number) => {
  pagination.page = val
  getRuleList()
}

// 显示创建对话框
const showCreateDialog = () => {
  // 重置表单
  Object.assign(ruleForm, {
    id: null,
    name: '',
    attack_type: '',
    regex_pattern: '',
    threat_level: 'medium',
    description: '',
    match_field: 'raw_log',
    is_enabled: true,
    priority: 100,
    auto_block: false,
    block_duration: 0
  })
  ruleDialogVisible.value = true
}

// 显示编辑对话框
const showEditDialog = (row: any) => {
  // 填充表单数据
  Object.assign(ruleForm, {
    id: row.id,
    name: row.name,
    attack_type: row.attack_type,
    regex_pattern: row.regex_pattern,
    threat_level: row.threat_level,
    description: row.description,
    match_field: row.match_field,
    is_enabled: row.is_enabled,
    priority: row.priority,
    auto_block: row.auto_block,
    block_duration: row.block_duration
  })
  ruleDialogVisible.value = true
}

// 提交规则表单
const submitRuleForm = async () => {
  try {
    // 验证表单
    await ruleFormRef.value.validate()
    
    submitting.value = true
    
    let response
    if (ruleForm.id) {
      // 更新规则
      response = await axios.put(`/match-rules/${ruleForm.id}`, ruleForm)
    } else {
      // 创建规则
      response = await axios.post('/match-rules', ruleForm)
    }
    
    if (response.success) {
      ElMessage.success(ruleForm.id ? '规则更新成功' : '规则创建成功')
      ruleDialogVisible.value = false
      // 刷新规则列表
      getRuleList()
    } else {
      ElMessage.error(response.message || '操作失败')
    }
  } catch (error) {
    console.error('提交规则表单出错:', error)
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

// 删除规则
const deleteRule = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除规则"${row.name}"吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    // 调用删除规则接口
    const response = await axios.delete(`/match-rules/${row.id}`)
    
    if (response.success) {
      ElMessage.success('规则删除成功')
      // 刷新规则列表
      getRuleList()
    } else {
      ElMessage.error(response.message || '规则删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除规则出错:', error)
      ElMessage.error('规则删除失败，请稍后重试')
    }
  }
}

// 切换规则状态
const toggleRuleStatus = async (row: any) => {
  try {
    // 调用切换规则状态接口
    const response = await axios.put(`/match-rules/${row.id}/toggle`)
    
    if (response.success) {
      ElMessage.success(`规则已${row.is_enabled ? '启用' : '禁用'}`)
      // 刷新规则列表
      getRuleList()
    } else {
      ElMessage.error(response.message || '状态切换失败')
      // 恢复状态
      row.is_enabled = !row.is_enabled
    }
  } catch (error) {
    console.error('切换规则状态出错:', error)
    ElMessage.error('状态切换失败，请稍后重试')
    // 恢复状态
    row.is_enabled = !row.is_enabled
  }
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

// 页面加载时获取规则列表
onMounted(() => {
  getRuleList()
})
</script>

<style scoped>
.match-rule-container {
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

.rule-table-container {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
