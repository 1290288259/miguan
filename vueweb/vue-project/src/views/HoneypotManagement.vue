<template>
  <div class="honeypot-management-container">
    <el-card class="page-header">
      <template #header>
        <div class="card-header">
          <span>蜜罐管理</span>
          <div class="header-actions">
            <el-button @click="refreshAllStatus" :loading="refreshingAll">
              刷新真实状态
            </el-button>
            <el-button type="primary" size="small" @click="handleCreate">
              <el-icon><Plus /></el-icon>
              新建蜜罐
            </el-button>
          </div>
        </div>
      </template>

      <el-form :inline="true" :model="queryForm" class="demo-form-inline">
        <el-form-item label="名称">
          <el-input v-model="queryForm.keyword" placeholder="请输入蜜罐名称" clearable />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="queryForm.type" placeholder="请选择类型" clearable style="width: 160px">
            <el-option label="SSH" value="SSH" />
            <el-option label="HTTP" value="HTTP" />
            <el-option label="FTP" value="FTP" />
            <el-option label="REDIS" value="REDIS" />
            <el-option label="MYSQL" value="MYSQL" />
            <el-option label="ELASTICSEARCH" value="ELASTICSEARCH" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" placeholder="请选择状态" clearable style="width: 160px">
            <el-option label="运行中" value="running" />
            <el-option label="已停止" value="stopped" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
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
        <el-table-column prop="status" label="状态" width="110">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'running' ? 'success' : 'info'">
              {{ scope.row.status === 'running' ? '运行中' : '已停止' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="健康检查" width="150">
          <template #default="scope">
            <div class="health-cell">
              <el-tag :type="getHealthTagType(scope.row)">
                {{ getHealthText(scope.row) }}
              </el-tag>
              <span v-if="scope.row.health_reason" class="health-reason">
                {{ formatHealthReason(scope.row.health_reason) }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="pid" label="PID" width="100" />
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
        <el-table-column label="操作" width="340" fixed="right">
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
            <el-button
              size="small"
              :loading="healthLoading[scope.row.id]"
              @click="handleHealthCheck(scope.row)"
            >
              校验状态
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
            <el-option label="REDIS" value="REDIS" />
            <el-option label="MYSQL" value="MYSQL" />
            <el-option label="ELASTICSEARCH" value="ELASTICSEARCH" />
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
          <el-input v-model="form.config" type="textarea" placeholder="JSON 格式配置" />
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
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import axios from '@/utils/axios'

interface HoneypotItem {
  id: number
  name: string
  type: string
  port: number
  ip_address: string
  status: 'running' | 'stopped'
  description?: string
  config?: string
  pid?: number | null
  healthy?: boolean
  health_reason?: string
}

const honeypotList = ref<HoneypotItem[]>([])
const loading = ref(false)
const refreshingAll = ref(false)
const actionLoading = ref<Record<number, boolean>>({})
const healthLoading = ref<Record<number, boolean>>({})
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const queryForm = reactive({
  keyword: '',
  type: '',
  status: ''
})

const dialogVisible = ref(false)
const dialogType = ref<'create' | 'edit'>('create')
const form = reactive({
  id: null as number | null,
  name: '',
  type: 'SSH',
  port: 2222,
  ip_address: '0.0.0.0',
  description: '',
  config: ''
})

const mergeHealthState = (items: HoneypotItem[]) => {
  honeypotList.value = items.map((item) => ({
    ...item,
    healthy: item.status === 'running' ? item.healthy ?? true : false,
    health_reason: item.health_reason ?? (item.status === 'running' ? 'ok' : 'stopped')
  }))
}

const fetchHoneypots = async () => {
  loading.value = true
  try {
    const response: any = await axios.get('/honeypots', {
      params: {
        page: currentPage.value,
        per_page: pageSize.value,
        keyword: queryForm.keyword,
        type: queryForm.type,
        status: queryForm.status
      }
    })

    if (response?.code === 200 && response.data?.honeypots) {
      mergeHealthState(response.data.honeypots)
      total.value = response.data.pagination?.total || 0
    } else {
      honeypotList.value = []
      total.value = 0
      ElMessage.error(response?.message || '获取蜜罐列表失败')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '网络错误，无法获取蜜罐列表')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchHoneypots()
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchHoneypots()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchHoneypots()
}

const updateRowHealth = (id: number, payload: any) => {
  const target = honeypotList.value.find((item) => item.id === id)
  if (!target) return
  target.status = payload.status
  target.pid = payload.pid
  target.healthy = payload.healthy
  target.health_reason = payload.reason
}

const handleHealthCheck = async (row: HoneypotItem, silent = false) => {
  healthLoading.value[row.id] = true
  try {
    const response: any = await axios.get(`/honeypots/${row.id}/health`)
    if (response.code === 200) {
      updateRowHealth(row.id, response.data)
      if (!silent) {
        ElMessage.success(`蜜罐 ${row.name} 状态已同步`)
      }
    } else if (!silent) {
      ElMessage.error(response.message || '状态校验失败')
    }
  } catch (error) {
    if (!silent) {
      ElMessage.error('状态校验失败')
    }
  } finally {
    healthLoading.value[row.id] = false
  }
}

const refreshAllStatus = async () => {
  refreshingAll.value = true
  try {
    await fetchHoneypots()
    ElMessage.success('已刷新所有蜜罐真实状态')
  } finally {
    refreshingAll.value = false
  }
}

const handleStart = async (row: HoneypotItem) => {
  actionLoading.value[row.id] = true
  try {
    const response: any = await axios.post(`/honeypots/${row.id}/start`)
    if (response.code === 200) {
      ElMessage.success(response.data?.message || '启动成功')
      await handleHealthCheck(row, true)
      await fetchHoneypots()
    } else {
      ElMessage.error(response.message || '启动失败')
    }
  } catch (error) {
    ElMessage.error('启动失败')
  } finally {
    actionLoading.value[row.id] = false
  }
}

const handleStop = async (row: HoneypotItem) => {
  actionLoading.value[row.id] = true
  try {
    const response: any = await axios.post(`/honeypots/${row.id}/stop`)
    if (response.code === 200) {
      ElMessage.success(response.data?.message || '停止成功')
      await handleHealthCheck(row, true)
      await fetchHoneypots()
    } else {
      ElMessage.error(response.message || '停止失败')
    }
  } catch (error) {
    ElMessage.error('停止失败')
  } finally {
    actionLoading.value[row.id] = false
  }
}

const handleDelete = (row: HoneypotItem) => {
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

const handleEdit = (row: HoneypotItem) => {
  dialogType.value = 'edit'
  form.id = row.id
  form.name = row.name
  form.type = row.type
  form.port = row.port
  form.ip_address = row.ip_address
  form.description = row.description || ''
  form.config = row.config || ''
  dialogVisible.value = true
}

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

const getHealthText = (row: HoneypotItem) => {
  if (row.status !== 'running') {
    return '未运行'
  }
  return row.healthy ? '健康' : '异常'
}

const getHealthTagType = (row: HoneypotItem) => {
  if (row.status !== 'running') {
    return 'info'
  }
  return row.healthy ? 'success' : 'warning'
}

const formatHealthReason = (reason?: string) => {
  const reasonMap: Record<string, string> = {
    ok: '进程和端口正常',
    stopped: '蜜罐未运行',
    pid_not_found: '未找到进程',
    process_mismatch: 'PID 与蜜罐进程不匹配',
    port_not_listening: '端口未监听',
    process_unavailable: '进程不可访问'
  }
  return reason ? reasonMap[reason] || reason : ''
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

.header-actions {
  display: flex;
  gap: 8px;
}

.table-container {
  margin-top: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.health-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.health-reason {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}
</style>
