<template>
  <div class="user-management-container">
    <!-- 顶部筛选区域 -->
    <div class="filter-card scifi-panel">
      <div class="card-header">
        <div class="title-wrapper">
          <el-icon class="header-icon"><User /></el-icon>
          <span class="title">用户管理</span>
        </div>
        <el-button type="primary" @click="handleAddUser" class="add-btn">
          <el-icon><Plus /></el-icon>添加用户
        </el-button>
      </div>
      
      <div class="filter-content">
        <el-form :inline="true" :model="queryForm" @submit.prevent>
          <el-form-item label="关键字">
            <el-input
              v-model="queryForm.keyword"
              placeholder="用户名/手机号/邮箱"
              class="search-input"
              clearable
              @keyup.enter="handleSearch"
              @clear="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item label="用户角色">
            <el-select v-model="queryForm.role" placeholder="请选择角色" clearable style="width: 160px">
              <el-option label="全部" value=""></el-option>
              <el-option label="管理员" :value="1"></el-option>
              <el-option label="普通用户" :value="2"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon>查询
            </el-button>
            <el-button @click="handleReset">
              <el-icon><Refresh /></el-icon>重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 内容列表区域 -->
    <div class="table-card scifi-panel">
      <div class="table-content">
        <el-table 
          :data="userList" 
          style="width: 100%" 
          v-loading="loading" 
          border 
          class="cyber-table"
        >
          <el-table-column prop="id" label="ID" width="80" align="center" />
          <el-table-column prop="username" label="用户名" min-width="120">
            <template #default="scope">
              <span class="user-name-text">{{ scope.row.username }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="role" label="角色" width="120" align="center">
            <template #default="scope">
              <el-tag :type="scope.row.role === 1 ? 'danger' : 'success'" effect="dark">
                {{ scope.row.role === 1 ? '管理员' : '普通用户' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="模块权限" min-width="200">
            <template #default="scope">
              <div v-if="scope.row.modules && scope.row.modules.length > 0" class="module-tags">
                <el-tag 
                  v-for="mod in scope.row.modules" 
                  :key="mod.id" 
                  size="small" 
                  class="mod-tag"
                  type="info"
                  effect="plain"
                >
                  {{ mod.title }}
                </el-tag>
              </div>
              <div v-else>
                <el-tag type="info" size="small" effect="plain">无模块权限</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="phone" label="手机号" width="150" />
          <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
          <el-table-column label="操作" width="200" fixed="right" align="center">
            <template #default="scope">
              <el-button-group>
                <el-button size="small" type="primary" @click="handleEdit(scope.row)">
                  <el-icon><Edit /></el-icon>编辑
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  @click="handleDelete(scope.row)"
                  :disabled="scope.row.id === currentUserId"
                >
                  <el-icon><Delete /></el-icon>删除
                </el-button>
              </el-button-group>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-container">
        <el-pagination
          v-model:current-page="queryForm.page"
          v-model:page-size="queryForm.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
      </div>
    </div>

    <!-- 用户编辑/添加对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? '添加用户' : '编辑用户'"
      width="600px"
    >
      <template #header>
        <div class="dialog-header">
          <el-icon><User /></el-icon>
          <span>{{ dialogType === 'add' ? '添加用户' : '编辑用户' }}</span>
        </div>
      </template>

      <el-form
        ref="userFormRef"
        :model="userForm"
        :rules="userRules"
        label-width="100px"
      >
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="userForm.username" :disabled="dialogType === 'edit'" placeholder="请输入用户名" />
          </el-form-item>
          
          <el-form-item label="角色" prop="role">
            <el-select v-model="userForm.role" placeholder="请选择角色" style="width: 100%">
              <el-option label="管理员" :value="1" />
              <el-option label="普通用户" :value="2" />
            </el-select>
          </el-form-item>
        </div>

        <el-form-item label="登录密码" prop="password">
          <el-input
            v-model="userForm.password"
            type="password"
            :placeholder="dialogType === 'edit' ? '如不修改请留空' : '请输入登录密码'"
            show-password
          />
        </el-form-item>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="userForm.phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="userForm.email" placeholder="请输入电子邮箱" />
          </el-form-item>
        </div>

        <el-form-item label="模块权限" prop="module_ids">
          <div class="module-selection-container">
            <el-checkbox-group v-model="userForm.module_ids">
              <el-checkbox
                v-for="mod in moduleList"
                :key="mod.id"
                :label="mod.id"
                border
                class="mod-checkbox"
              >
                {{ mod.title }}
              </el-checkbox>
            </el-checkbox-group>
          </div>
          <div v-if="userForm.role && rolePermissions[userForm.role]" class="permission-tip">
            <el-icon style="vertical-align: middle; margin-right: 5px;"><InfoFilled /></el-icon>
            <span style="font-size: 12px; opacity: 0.8;">当前角色默认拥有：{{ getRoleDefaultModules(userForm.role).join('、') }}</span>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitUserForm" :loading="submitting">
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Search, Refresh, Plus, User, List, InfoFilled } from '@element-plus/icons-vue'
import axios from '../utils/axios'
import useUserStore from '../stores/user'

const userStore = useUserStore()
const currentUserId = computed(() => userStore.user?.id)

// 列表数据
const userList = ref([])
const moduleList = ref([]) // 所有可用模块
const loading = ref(false)
const queryForm = reactive({
  keyword: '',
  role: '',
  page: 1,
  size: 10
})
const total = ref(0)
const rolePermissions = ref<any>({})

// 获取角色默认模块名称列表
const getRoleDefaultModules = (role: number) => {
  if (role === 1) {
    return moduleList.value.map((m: any) => m.title)
  } else if (role === 2) {
    const defaultPaths = ['/', '/log-query', '/malicious-ip-management']
    return moduleList.value
      .filter((m: any) => defaultPaths.includes(m.path))
      .map((m: any) => m.title)
  }
  return []
}

// 对话框数据
const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const submitting = ref(false)
const userFormRef = ref<FormInstance>()

const userForm = reactive({
  id: undefined as number | undefined,
  username: '',
  password: '',
  role: 2,
  phone: '',
  email: '',
  module_ids: [] as number[]
})

const userRules = reactive<FormRules>({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 4, message: '长度至少 4 个字符', trigger: 'blur' }
  ],
  password: [
    { required: false, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '长度至少 6 个字符', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
})

// 获取所有模块
const fetchModules = async () => {
  try {
    const res: any = await axios.get('/user/modules')
    if (res.success) {
      moduleList.value = res.data
    }
  } catch (error) {
    console.error('获取模块列表失败', error)
  }
}

// 获取用户列表
const fetchUserList = async () => {
  loading.value = true
  try {
    const res: any = await axios.get('/user/list', {
      params: {
        page: queryForm.page,
        size: queryForm.size,
        keyword: queryForm.keyword,
        role: queryForm.role
      }
    })
    if (res.success) {
      userList.value = res.data.items
      total.value = res.data.total
    } else {
      ElMessage.error(res.message || '获取用户列表失败')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  queryForm.page = 1
  fetchUserList()
}

// 重置搜索
const handleReset = () => {
  queryForm.keyword = ''
  queryForm.role = ''
  queryForm.page = 1
  fetchUserList()
}

// 分页
const handleSizeChange = (val: number) => {
  queryForm.size = val
  fetchUserList()
}

const handleCurrentChange = (val: number) => {
  queryForm.page = val
  fetchUserList()
}

const handleAddUser = () => {
  dialogType.value = 'add'
  userForm.id = undefined
  userForm.username = ''
  userForm.password = ''
  userForm.role = 2
  userForm.phone = ''
  userForm.email = ''
  
  // 触发一次默认模块填充 (普通用户)
  const defaultPaths = ['/', '/log-query', '/malicious-ip-management']
  const defaultModules: number[] = []
  moduleList.value.forEach((m: any) => {
    if (defaultPaths.includes(m.path)) {
      defaultModules.push(m.id)
    }
  })
  userForm.module_ids = defaultModules

  dialogVisible.value = true
  
  // 重置校验
  if (userFormRef.value) {
    userFormRef.value.clearValidate()
  }
}

// 监听角色变化
watch(() => userForm.role, (newRole) => {
  // 仅在添加模式下生效，避免编辑时覆盖用户已有设置
  if (dialogType.value === 'add' && moduleList.value.length > 0) {
    const defaultModules: number[] = []
    
    if (newRole === 1) {
      // 管理员：拥有所有模块
      moduleList.value.forEach((m: any) => defaultModules.push(m.id))
    } else if (newRole === 2) {
      // 普通用户：基础模块
      const defaultPaths = ['/', '/log-query', '/malicious-ip-management']
      moduleList.value.forEach((m: any) => {
        if (defaultPaths.includes(m.path)) {
          defaultModules.push(m.id)
        }
      })
    }
    
    userForm.module_ids = defaultModules
  }
})

// 编辑用户
const handleEdit = (row: any) => {
  dialogType.value = 'edit'
  userForm.id = row.id
  userForm.username = row.username
  userForm.password = '' // 编辑时不回显密码
  userForm.role = row.role
  userForm.phone = row.phone || ''
  userForm.email = row.email || ''
  // 映射模块ID
  userForm.module_ids = row.modules ? row.modules.map((m: any) => m.id) : []
  dialogVisible.value = true
  
  if (userFormRef.value) {
    userFormRef.value.clearValidate()
  }
}

// 删除用户
const handleDelete = (row: any) => {
  ElMessageBox.confirm(
    `确定要删除用户 "${row.username}" 吗？`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      const res: any = await axios.delete(`/user/${row.id}`)
      if (res.success) {
        ElMessage.success('删除成功')
        fetchUserList()
      } else {
        ElMessage.error(res.message || '删除失败')
      }
    } catch (error: any) {
      ElMessage.error(error.message || '删除失败')
    }
  })
}

// 提交表单
const submitUserForm = async () => {
  if (!userFormRef.value) return
  
  await userFormRef.value.validate(async (valid, fields) => {
    if (valid) {
      submitting.value = true
      try {
        let res: any
        if (dialogType.value === 'add') {
          // 添加用户
          const data: any = {
            username: userForm.username,
            password: userForm.password,
            role: userForm.role,
            phone: userForm.phone,
            email: userForm.email,
            module_ids: userForm.module_ids
          }
          res = await axios.post('/user/add', data)
        } else {
          // 编辑
          const data: any = {
            role: userForm.role,
            phone: userForm.phone,
            email: userForm.email,
            module_ids: userForm.module_ids
          }
          if (userForm.password) {
            data.password = userForm.password
          }
          res = await axios.put(`/user/${userForm.id}`, data)
        }
        
        if (res.success || res.code === 200) {
          ElMessage.success(dialogType.value === 'add' ? '添加成功' : '更新成功')
          dialogVisible.value = false
          fetchUserList()
        } else {
          ElMessage.error(res.message || '操作失败')
        }
      } catch (error: any) {
        ElMessage.error(error.response?.data?.message || error.message || '操作失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const fetchPermissions = async () => {
  try {
    const res: any = await axios.get('/user/permissions')
    if (res.success) {
      rolePermissions.value = res.data
    }
  } catch (error) {
    console.error('获取权限列表失败', error)
  }
}

onMounted(() => {
  fetchUserList()
  fetchModules()
  fetchPermissions()
})
</script>

<style scoped>
.user-management-container {
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background-color: transparent;
}

/* 科幻面板基础样式 */
.scifi-panel {
  background-color: var(--scifi-card-bg, rgba(16, 33, 65, 0.85));
  border: 1px solid var(--scifi-border-color, rgba(0, 243, 255, 0.3));
  border-radius: 8px;
  backdrop-filter: var(--scifi-glass, blur(10px));
  box-shadow: var(--scifi-shadow, 0 4px 30px rgba(0, 0, 0, 0.5));
  overflow: hidden;
}

/* 卡片头部 */
.card-header {
  padding: 15px 20px;
  border-bottom: 1px solid var(--scifi-border-color, rgba(0, 243, 255, 0.2));
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  font-size: 20px;
  color: var(--scifi-primary-color, #00f3ff);
}

.title {
  font-size: 18px;
  font-weight: bold;
  color: var(--scifi-primary-color, #00f3ff);
  text-shadow: 0 0 10px rgba(0, 243, 255, 0.5);
}

/* 筛选区域内容 */
.filter-content {
  padding: 15px 20px;
}

:deep(.el-form--inline .el-form-item) {
  margin-right: 25px !important;
  margin-bottom: 0;
}

:deep(.el-form-item:last-child) {
  margin-right: 0 !important;
}

.search-input {
  width: 250px;
}

/* 列表区域内容 */
.table-content {
  padding: 20px;
}

.user-name-text {
  color: var(--scifi-primary-color);
  font-weight: bold;
}

.module-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.mod-tag {
  background-color: rgba(0, 243, 255, 0.05) !important;
  border: 1px solid rgba(0, 243, 255, 0.2) !important;
  color: var(--scifi-primary-color, #00f3ff) !important;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 对话框样式 */
.dialog-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: bold;
  color: var(--scifi-primary-color);
}

.module-selection-container {
  background-color: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--scifi-border-color);
  border-radius: 4px;
  padding: 15px;
  width: 100%;
}

.mod-checkbox {
  margin-bottom: 10px;
  margin-right: 10px !important;
  border: 1px solid rgba(0, 243, 255, 0.2) !important;
  background-color: rgba(0, 243, 255, 0.05) !important;
  color: var(--scifi-text-color) !important;
}

.mod-checkbox.is-checked {
  border-color: var(--scifi-primary-color) !important;
  box-shadow: 0 0 5px rgba(0, 243, 255, 0.3);
}

.permission-tip {
  margin-top: 10px;
  color: var(--scifi-primary-color);
  display: flex;
  align-items: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 适配 Element Plus 表单和输入框 */
:deep(.el-form-item__label) {
  color: var(--scifi-text-color) !important;
  font-weight: bold;
}

:deep(.el-input__wrapper) {
  background-color: rgba(0, 243, 255, 0.05) !important;
  box-shadow: 0 0 0 1px var(--scifi-border-color) inset !important;
  border-radius: 4px;
}

:deep(.el-input__inner::placeholder) {
  color: var(--el-text-color-placeholder) !important;
}

:deep(.el-input__inner) {
  color: var(--scifi-text-color) !important;
}

:deep(.el-select .el-input__inner::placeholder) {
  color: var(--el-text-color-placeholder) !important;
}

:deep(.el-select__placeholder) {
  color: var(--el-text-color-placeholder) !important; /* 针对 Element Plus 新版 Select 的占位符 */
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--scifi-primary-color) inset, 0 0 8px rgba(0, 243, 255, 0.3) !important;
}

:deep(.el-select .el-input__wrapper) {
  background-color: rgba(0, 243, 255, 0.05) !important;
}

:deep(.el-input__inner) {
  color: var(--scifi-text-color) !important;
}

:deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.4) !important;
}

/* 按钮样式微调 */
.filter-content .el-button {
  transition: all 0.3s ease;
}

.filter-content .el-button--primary {
  background: linear-gradient(135deg, rgba(0, 243, 255, 0.2) 0%, rgba(0, 243, 255, 0.1) 100%) !important;
  border: 1px solid var(--scifi-primary-color) !important;
}

.filter-content .el-button--primary:hover {
  background: var(--scifi-primary-color) !important;
  box-shadow: 0 0 15px rgba(0, 243, 255, 0.5);
  color: #000 !important;
}

/* 表格适配 */
:deep(.el-table) {
  background-color: transparent !important;
  --el-table-border-color: rgba(0, 243, 255, 0.2);
}

:deep(.el-table th.el-table__cell) {
  background-color: rgba(0, 243, 255, 0.1) !important;
  color: var(--scifi-primary-color, #00f3ff) !important;
  font-weight: bold;
}

:deep(.el-table tr) {
  background-color: transparent !important;
  color: var(--scifi-text-color, #fff) !important;
}

:deep(.el-table--striped .el-table__row--striped td) {
  background-color: rgba(0, 243, 255, 0.03) !important;
}

:deep(.el-table--enable-row-hover .el-table__row:hover > td) {
  background-color: rgba(0, 243, 255, 0.1) !important;
}

/* 权限预览区域 */
.permission-preview {
  margin-top: 10px;
  padding: 10px;
  background-color: rgba(0, 243, 255, 0.05);
  border: 1px solid var(--scifi-border-color, rgba(0, 243, 255, 0.2));
  border-radius: 4px;
}

.permission-preview p {
  margin: 0 0 5px 0;
  font-size: 12px;
  color: var(--scifi-text-muted, #cceeff);
}

/* 分页适配 */
:deep(.el-pagination) {
  --el-pagination-bg-color: transparent;
  --el-pagination-text-color: var(--scifi-text-color);
  --el-pagination-button-bg-color: rgba(0, 243, 255, 0.1);
}

:deep(.el-pagination .btn-next), 
:deep(.el-pagination .btn-prev) {
  background-color: rgba(0, 243, 255, 0.1) !important;
  color: var(--scifi-text-color) !important;
}

:deep(.el-pager li) {
  background-color: rgba(0, 243, 255, 0.1) !important;
  color: var(--scifi-text-color) !important;
}

:deep(.el-pager li.is-active) {
  background-color: var(--scifi-primary-color, #00f3ff) !important;
  color: #000 !important;
  font-weight: bold;
}
</style>