<template>
  <div class="user-profile-container">
    <div class="profile-card">
      <h2 class="profile-title">个人信息</h2>
      
      <el-form 
        v-if="userInfo"
        ref="formRef"
        :model="form" 
        :rules="rules" 
        label-width="100px" 
        class="profile-form"
      >
        <el-form-item label="用户名">
          <el-input v-model="userInfo.username" disabled />
        </el-form-item>
        
        <el-form-item label="角色">
          <el-tag :type="userInfo.role === 1 ? 'danger' : 'success'">
            {{ userInfo.role === 1 ? '管理员' : '普通用户' }}
          </el-tag>
        </el-form-item>
        
        <el-form-item label="权限详情" v-if="userInfo.permissions && userInfo.permissions.length > 0">
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
        </el-form-item>
        
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="saveProfile" :loading="loading">保存修改</el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
      
      <div v-else class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { getCurrentUser, updateUserInfo } from '../services/auth'

const formRef = ref<FormInstance>()
const loading = ref(false)
const userInfo = ref<any>(null)

const form = reactive({
  phone: '',
  email: ''
})

const rules = reactive<FormRules>({
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: ['blur', 'change'] }
  ]
})

const fetchUserInfo = async () => {
  try {
    const res: any = await getCurrentUser()
    if (res.success) {
      userInfo.value = res.data
      form.phone = userInfo.value.phone || ''
      form.email = userInfo.value.email || ''
    }
  } catch (error) {
    ElMessage.error('获取用户信息失败')
  }
}

const saveProfile = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid, fields) => {
    if (valid) {
      loading.value = true
      try {
        const res: any = await updateUserInfo(form.phone, form.email)
        if (res.success) {
          ElMessage.success('个人信息更新成功')
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
  max-width: 600px;
  background-color: rgba(13, 25, 40, 0.8);
  border: 1px solid var(--scifi-border-color);
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 0 20px rgba(0, 243, 255, 0.1);
}

.profile-title {
  color: var(--scifi-primary-color);
  margin-bottom: 30px;
  text-align: center;
  font-size: 24px;
}

.profile-form {
  margin-top: 20px;
}

:deep(.el-input__wrapper) {
  background-color: rgba(5, 11, 20, 0.5);
  border: 1px solid var(--scifi-border-color);
  box-shadow: none;
}

:deep(.el-input__inner) {
  color: var(--scifi-text-color);
}

:deep(.el-form-item__label) {
  color: var(--scifi-text-color);
}

:deep(.el-input.is-disabled .el-input__wrapper) {
  background-color: rgba(30, 30, 30, 0.5);
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
</style>