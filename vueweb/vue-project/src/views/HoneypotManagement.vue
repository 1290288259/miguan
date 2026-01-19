<template>
  <div class="honeypot-management-container">
    <el-card class="page-header">
      <template #header>
        <div class="card-header">
          <span>蜜罐管理</span>
          <el-button type="primary" size="small" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新建蜜罐
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="queryForm" class="demo-form-inline">
        <el-form-item label="名称">
          <el-input v-model="queryForm.keyword" placeholder="请输入蜜罐名称" clearable />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="queryForm.type" placeholder="请选择类型" clearable style="width: 160px">
            <el-option label="SSH" value="SSH" />
            <el-option label="HTTP" value="HTTP" />
            <el-option label="FTP" value="FTP" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" placeholder="请选择状态" clearable style="width: 160px">
            <el-option label="运行中" value="running" />
            <el-option label="已停止" value="stopped" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchHoneypots">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-container">
      <el-table :data="honeypotList" style="width: 100%" v-loading="loading" border stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="名称" width="150" />
        <el-table-column prop="type" label="类型" width="100" />
        <el-table-column prop="port" label="端口" width="100" />
        <el-table-column prop="ip_address" label="绑定IP" width="140" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'running' ? 'success' : 'danger'">
              {{ scope.row.status === 'running' ? '运行中' : '已停止' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" />
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="scope">
            <el-button 
              v-if="scope.row.status !== 'running'"
              type="success" 
              size="small" 
              :loading="actionLoading[scope.row.id]"
              @click="handleStart(scope.row)"
            >
              启动
            </el-button>
            <el-button 
              v-else
              type="danger" 
              size="small" 
              :loading="actionLoading[scope.row.id]"
              @click="handleStop(scope.row)"
            >
              停止
            </el-button>
            <el-button type="primary" size="small" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

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

    <!-- 编辑/新建对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'create' ? '新建蜜罐' : '编辑蜜罐'"
      width="500px"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="form.type" placeholder="请选择类型">
            <el-option label="SSH" value="SSH" />
            <el-option label="HTTP" value="HTTP" />
            <el-option label="FTP" value="FTP" />
          </el-select>
        </el-form-item>
        <el-form-item label="端口" required>
          <el-input-number v-model="form.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="绑定IP">
          <el-input v-model="form.ip_address" placeholder="0.0.0.0" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="配置">
          <el-input v-model="form.config" type="textarea" placeholder="JSON格式配置" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import axios from '@/utils/axios'

// 列表数据
const honeypotList = ref([])
const loading = ref(false)
const actionLoading = ref<Record<number, boolean>>({}) // 按钮加载状态
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 查询表单
const queryForm = reactive({
  keyword: '',
  type: '',
  status: ''
})

// 对话框控制
const dialogVisible = ref(false)
const dialogType = ref('create') // 'create' or 'edit'
const form = reactive({
  id: null,
  name: '',
  type: 'SSH',
  port: 2222,
  ip_address: '0.0.0.0',
  description: '',
  config: ''
})

// 获取列表
const fetchHoneypots = async () => {
  loading.value = true
  try {
    console.log('Fetching honeypots...')
    // axios 实例已配置 baseURL='/api' 和自动添加 token
    const response: any = await axios.get('/honeypots', {
      params: {
        page: currentPage.value,
        per_page: pageSize.value,
        keyword: queryForm.keyword,
        type: queryForm.type,
        status: queryForm.status
      }
    })
    
    console.log('Honeypot response:', response)

    if (response && response.code === 200) {
      if (response.data && Array.isArray(response.data.honeypots)) {
        honeypotList.value = response.data.honeypots
        total.value = response.data.pagination?.total || 0
      } else {
        console.error('Invalid data structure:', response.data)
        honeypotList.value = []
        total.value = 0
        ElMessage.warning('获取到的数据格式不正确')
      }
    } else {
      ElMessage.error(response?.message || '获取列表失败')
    }
  } catch (error: any) {
    console.error('Fetch error:', error)
    ElMessage.error(error.message || '网络错误，无法获取蜜罐列表')
  } finally {
    loading.value = false
  }
}

// 分页处理
const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchHoneypots()
}
const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchHoneypots()
}

// 启动蜜罐
const handleStart = async (row: any) => {
  actionLoading.value[row.id] = true
  try {
    const response: any = await axios.post(`/honeypots/${row.id}/start`)
    if (response.code === 200) {
      ElMessage.success('启动成功')
      fetchHoneypots()
    } else {
      ElMessage.error(response.message || '启动失败')
    }
  } catch (error) {
    ElMessage.error('启动失败')
  } finally {
    actionLoading.value[row.id] = false
  }
}

// 停止蜜罐
const handleStop = async (row: any) => {
  actionLoading.value[row.id] = true
  try {
    const response: any = await axios.post(`/honeypots/${row.id}/stop`)
    if (response.code === 200) {
      ElMessage.success('停止成功')
      fetchHoneypots()
    } else {
      ElMessage.error(response.message || '停止失败')
    }
  } catch (error) {
    ElMessage.error('停止失败')
  } finally {
    actionLoading.value[row.id] = false
  }
}

// 删除蜜罐
const handleDelete = (row: any) => {
  ElMessageBox.confirm('确定要删除该蜜罐吗？', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const response: any = await axios.delete(`/honeypots/${row.id}`)
      if (response.code === 200) {
        ElMessage.success('删除成功')
        fetchHoneypots()
      } else {
        ElMessage.error(response.message || '删除失败')
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

// 打开新建对话框
const handleCreate = () => {
  dialogType.value = 'create'
  form.id = null
  form.name = ''
  form.type = 'SSH'
  form.port = 2222
  form.ip_address = '0.0.0.0'
  form.description = ''
  form.config = ''
  dialogVisible.value = true
}

// 打开编辑对话框
const handleEdit = (row: any) => {
  dialogType.value = 'edit'
  form.id = row.id
  form.name = row.name
  form.type = row.type
  form.port = row.port
  form.ip_address = row.ip_address
  form.description = row.description
  form.config = row.config
  dialogVisible.value = true
}

// 提交表单
const submitForm = async () => {
  if (!form.name || !form.port) {
    ElMessage.warning('请填写必要信息')
    return
  }
  
  try {
    const url = dialogType.value === 'create' ? '/honeypots' : `/honeypots/${form.id}`
    const method = dialogType.value === 'create' ? 'post' : 'put'
    
    const response: any = await axios[method](url, form)
    
    if (response.code === 200) {
      ElMessage.success(dialogType.value === 'create' ? '创建成功' : '更新成功')
      dialogVisible.value = false
      fetchHoneypots()
    } else {
      ElMessage.error(response.message || '操作失败')
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

onMounted(() => {
  fetchHoneypots()
})
</script>

<style scoped>
.honeypot-management-container {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.table-container {
  margin-top: 20px;
}
.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
