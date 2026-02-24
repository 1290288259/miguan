<template>
  <div class="user-profile-container">
    <div class="profile-card">
      <h2 class="profile-title">个人信息</h2>
      
      <div v-if="userInfo" class="profile-content">
        <el-descriptions :column="1" border class="profile-descriptions">
          <el-descriptions-item label="用户名">
            <span class="username-text">{{ userInfo.username }}</span>
          </el-descriptions-item>
          
          <el-descriptions-item label="角色">
            <el-tag :type="userInfo.role === 1 ? 'danger' : 'success'">
              {{ userInfo.role === 1 ? '管理员' : '普通用户' }}
            </el-tag>
          </el-descriptions-item>
          
          <el-descriptions-item label="权限详情" v-if="userInfo.permissions && userInfo.permissions.length > 0">
            <div class="permission-list">
               <el-tag 
                 v-for="perm in userInfo.permissions" 
                 :key="perm.id" 
                 class="permission-tag"
                 type="info"
                 effect="dark"
                 size="small"
               >
                 {{ perm.description || perm.path }}
               </el-tag>
            </div>
          </el-descriptions-item>
          
          <el-descriptions-item label="手机号">
            {{ userInfo.phone || '未设置' }}
          </el-descriptions-item>
          
          <el-descriptions-item label="邮箱">
            {{ userInfo.email || '未设置' }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div class="profile-actions">
          <el-button type="primary" @click="openEditDialog">编辑</el-button>
        </div>
      </div>
      
      <div v-else class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>
    </div>

    <!-- 编辑个人信息弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="编辑个人信息"
      width="500px"
      :close-on-click-modal="false"
      append-to-body
    >
      <el-form 
        ref="formRef"
        :model="form" 
        :rules="rules" 
        label-width="100px"
      >
        <el-form-item label="用户名">
          <span class="username-text">{{ form.username }}</span>
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>

        <el-divider content-position="center">安全设置（可选）</el-divider>

        <el-form-item 
          label="当前密码" 
          prop="oldPassword"
        >
          <el-input 
            v-model="form.oldPassword" 
            type="password" 
            placeholder="修改密码需要验证当前密码" 
            show-password
          />
        </el-form-item>

        <el-form-item label="新密码" prop="password">
          <el-input 
            v-model="form.password" 
            type="password" 
            placeholder="如果不修改密码请留空" 
            show-password
          />
        </el-form-item>

        <el-form-item 
          label="确认新密码" 
          prop="confirmPassword"
        >
          <el-input 
            v-model="form.confirmPassword" 
            type="password" 
            placeholder="请再次输入新密码" 
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveProfile" :loading="loading">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { getCurrentUser, updateUserInfo } from '../services/auth'

const formRef = ref<FormInstance>()
const loading = ref(false)
const userInfo = ref<any>(null)
const dialogVisible = ref(false)

const form = reactive({
  username: '',
  phone: '',
  email: '',
  password: '',
  confirmPassword: '',
  oldPassword: ''
})

const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (form.password && value !== form.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const validateOldPassword = (rule: any, value: string, callback: any) => {
  if (form.password && !value) {
    callback(new Error('请输入当前密码以确认修改'))
  } else {
    callback()
  }
}

const rules = reactive<FormRules>({
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: ['blur', 'change'] }
  ],
  password: [
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  oldPassword: [
    { validator: validateOldPassword, trigger: 'blur' }
  ]
})

const fetchUserInfo = async () => {
  try {
    const res: any = await getCurrentUser()
    if (res.success) {
      userInfo.value = res.data
    }
  } catch (error) {
    ElMessage.error('获取用户信息失败')
  }
}

const openEditDialog = () => {
  if (userInfo.value) {
    form.username = userInfo.value.username || ''
    form.phone = userInfo.value.phone || ''
    form.email = userInfo.value.email || ''
    form.password = ''
    form.confirmPassword = ''
    form.oldPassword = ''
    dialogVisible.value = true
  }
}

const saveProfile = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid, fields) => {
    if (valid) {
      loading.value = true
      try {
        const res: any = await updateUserInfo(
          form.phone, 
          form.email, 
          form.password || undefined,
          form.oldPassword || undefined
        )
        if (res.success) {
          ElMessage.success('个人信息更新成功')
          dialogVisible.value = false
          await fetchUserInfo() // 刷新数据
        } else {
          ElMessage.error(res.message || '更新失败')
        }
      } catch (error) {
        ElMessage.error('更新失败，请重试')
      } finally {
        loading.value = false
      }
    }
  })
}

const resetForm = () => {
  if (userInfo.value) {
    form.phone = userInfo.value.phone || ''
    form.email = userInfo.value.email || ''
  }
}

onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
.user-profile-container {
  display: flex;
  justify-content: center;
  padding: 40px 20px;
}

.profile-card {
  width: 100%;
  max-width: 800px;
  background-color: var(--scifi-card-bg);
  border: 1px solid var(--scifi-border-color);
  border-radius: 8px;
  padding: 30px;
  box-shadow: var(--scifi-shadow);
  backdrop-filter: var(--scifi-glass);
}

.profile-title {
  color: var(--scifi-primary-color);
  margin-bottom: 30px;
  text-align: center;
  font-size: 24px;
}

.profile-content {
  margin-top: 20px;
}

.profile-actions {
  margin-top: 30px;
  display: flex;
  justify-content: center;
}

:deep(.el-input__wrapper) {
  background-color: transparent;
  border: 1px solid var(--scifi-border-color);
  box-shadow: none;
}

/* 深色模式特定样式 */
:global(html:not(.light-theme)) .profile-card {
  background-color: rgba(13, 25, 40, 0.8);
  box-shadow: 0 0 20px rgba(0, 243, 255, 0.1);
}

:global(html:not(.light-theme)) :deep(.el-descriptions__body) {
  background-color: transparent;
  color: var(--scifi-text-color);
}

:global(html:not(.light-theme)) :deep(.el-descriptions__label) {
  background-color: rgba(0, 243, 255, 0.1);
  color: var(--scifi-primary-color);
}

:global(html:not(.light-theme)) :deep(.el-descriptions__content) {
  color: var(--scifi-text-color);
}

:global(html:not(.light-theme)) :deep(.el-input__wrapper) {
  background-color: rgba(5, 11, 20, 0.5);
}

:deep(.el-input__inner) {
  color: var(--scifi-text-color);
}

:deep(.el-form-item__label) {
  color: var(--scifi-text-color);
}

.permission-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.permission-tag {
  background-color: rgba(0, 243, 255, 0.1);
  border-color: rgba(0, 243, 255, 0.3);
  color: var(--scifi-text-color);
}

.username-text {
  color: var(--scifi-text-color);
  font-weight: bold;
  font-size: 16px;
}

:global(html.light-theme) .username-text {
  color: #000000 !important;
}

/* 浅色模式覆盖 */
:global(html.light-theme) .permission-tag {
  background-color: #ecf5ff;
  border-color: #d9ecff;
  color: #409eff;
}

:global(html.light-theme) :deep(.el-input__inner) {
  color: #303133 !important;
}

:global(html.light-theme) :deep(.el-dialog) {
  background-color: #ffffff;
}

:global(html.light-theme) :deep(.el-descriptions__label) {
  background-color: #f5f7fa;
  color: #606266;
}

:global(html.light-theme) :deep(.el-descriptions__content) {
  color: #303133;
}
</style>