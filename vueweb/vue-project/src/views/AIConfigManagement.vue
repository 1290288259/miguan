<template>
  <div class="ai-config-management">
    <div class="header">
      <h2 class="sci-fi-title">AI模型配置</h2>
      <el-button type="primary" class="sci-fi-button" @click="showAddDialog">
        <el-icon><Plus /></el-icon> 新增配置
      </el-button>
    </div>

    <div class="sci-fi-card">
      <el-table :data="configs" v-loading="loading" style="width: 100%" class="sci-fi-table">
        <el-table-column prop="name" label="配置名称" min-width="120" />
        <el-table-column prop="provider" label="提供商" width="100">
          <template #default="scope">
            <el-tag effect="plain" class="sci-fi-tag">{{ scope.row.provider }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model_name" label="模型名称" min-width="150" />
        <el-table-column prop="api_url" label="API地址" min-width="250" show-overflow-tooltip />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="scope">
            <el-tag v-if="scope.row.is_active" type="success" effect="dark" class="active-tag">使用中</el-tag>
            <el-tag v-else type="info" effect="plain">未激活</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_auto_block" label="自动封禁" width="100">
          <template #default="scope">
            <el-switch
              v-model="scope.row.is_auto_block"
              active-text=""
              inactive-text=""
              :loading="scope.row.switching"
              style="--el-switch-on-color: #f56c6c; --el-switch-off-color: #909399"
              @change="(val) => handleAutoBlockChange(val, scope.row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="scope">
            <el-button 
              v-if="!scope.row.is_active"
              size="small" 
              type="success" 
              class="sci-fi-button is-text"
              @click="handleActivate(scope.row)"
            >
              启用
            </el-button>
            <el-button 
              v-else
              size="small" 
              type="warning" 
              class="sci-fi-button is-text"
              @click="handleDeactivate(scope.row)"
            >
              关闭
            </el-button>
            <el-button 
              size="small" 
              type="primary" 
              class="sci-fi-button is-text"
              @click="handleEdit(scope.row)"
            >
              编辑
            </el-button>
            <el-button 
              size="small" 
              type="info" 
              class="sci-fi-button is-text"
              @click="handleTest(scope.row)"
            >
              测试
            </el-button>
            <el-popconfirm 
              title="确定要删除这个配置吗？" 
              confirm-button-text="删除" 
              cancel-button-text="取消"
              @confirm="handleDelete(scope.row)"
            >
              <template #reference>
                <el-button 
                  size="small" 
                  type="danger" 
                  class="sci-fi-button is-text"
                  :disabled="scope.row.is_active"
                >
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑配置' : '新增配置'"
      width="500px"
      class="sci-fi-dialog"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="form.name" placeholder="给配置起个名字，如 Local Ollama" />
        </el-form-item>
        <el-form-item label="提供商" prop="provider">
          <el-select v-model="form.provider" placeholder="选择提供商">
            <el-option label="Ollama (本地/远程)" value="ollama" />
            <el-option label="OpenAI (兼容)" value="openai" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称" prop="model_name">
          <el-input v-model="form.model_name" placeholder="如 deepseek-r1:7b" />
        </el-form-item>
        <el-form-item label="API地址" prop="api_url">
          <el-input v-model="form.api_url" placeholder="如 http://localhost:11434/api/generate" />
        </el-form-item>
        <el-form-item label="API密钥" prop="api_key">
          <el-input v-model="form.api_key" type="password" placeholder="如果是Ollama通常不需要" show-password />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入配置描述" class="sci-fi-input" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElLoading } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { 
  getAIConfigs, 
  createAIConfig, 
  updateAIConfig, 
  deleteAIConfig, 
  activateAIConfig,
  deactivateAIConfig,
  testAIConfig
} from '../services/aiConfig'
import type { AIConfig } from '../services/aiConfig'

const configs = ref<AIConfig[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  id: 0,
  name: '',
  provider: 'ollama',
  model_name: '',
  api_url: 'http://localhost:11434/api/generate',
  api_key: '',
  description: ''
})

const rules = reactive<FormRules>({
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  provider: [{ required: true, message: '请选择提供商', trigger: 'change' }],
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  api_url: [{ required: true, message: '请输入API地址', trigger: 'blur' }]
})

const fetchConfigs = async () => {
  loading.value = true
  try {
    const res: any = await getAIConfigs()
    if (res.code === 200) {
      configs.value = res.data
    }
  } catch (error) {
    ElMessage.error('获取配置失败')
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  isEdit.value = false
  form.id = 0
  form.name = ''
  form.provider = 'ollama'
  form.model_name = 'deepseek-r1:7b'
  form.api_url = 'http://localhost:11434/api/generate'
  form.api_key = ''
  form.description = ''
  dialogVisible.value = true
}

const handleEdit = (row: AIConfig) => {
  isEdit.value = true
  form.id = row.id
  form.name = row.name
  form.provider = row.provider
  form.model_name = row.model_name
  form.api_url = row.api_url
  form.api_key = row.api_key || ''
  form.description = row.description || ''
  dialogVisible.value = true
}

const handleDelete = async (row: AIConfig) => {
  try {
    const res: any = await deleteAIConfig(row.id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      fetchConfigs()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const handleActivate = async (row: AIConfig) => {
  try {
    const res: any = await activateAIConfig(row.id)
    if (res.code === 200) {
      ElMessage.success('启用成功')
      fetchConfigs()
    } else {
      ElMessage.error(res.message || '启用失败')
    }
  } catch (error) {
    ElMessage.error('启用失败')
  }
}

const handleDeactivate = async (row: AIConfig) => {
  try {
    const res: any = await deactivateAIConfig(row.id)
    if (res.code === 200) {
      ElMessage.success('关闭成功')
      fetchConfigs()
    } else {
      ElMessage.error(res.message || '关闭失败')
    }
  } catch (error: any) {
    console.error(error)
    ElMessage.error('关闭失败: ' + (error.message || '未知错误'))
  }
}

const handleTest = async (row: AIConfig) => {
  const loading = ElLoading.service({
    lock: true,
    text: '正在测试连接...',
    background: 'rgba(0, 0, 0, 0.7)',
  })
  
  try {
    const res: any = await testAIConfig(row.id)
    loading.close()
    
    if (res.code === 200) {
      const { latency, response } = res.data
      ElMessage.success({
        message: `连接成功! 延迟: ${latency}ms`,
        duration: 5000
      })
      
      // 可以选择显示响应内容
      console.log('Test response:', response)
    } else {
      ElMessage.error(res.message || '连接测试失败')
    }
  } catch (error: any) {
    loading.close()
    console.error(error)
    ElMessage.error('测试失败: ' + (error.message || '未知错误'))
  }
}

const handleAutoBlockChange = async (val: boolean, row: any) => {
  row.switching = true
  try {
    const res: any = await updateAIConfig(row.id, { is_auto_block: val })
    if (res.code === 200) {
      ElMessage.success(val ? '自动封禁已开启' : '自动封禁已关闭')
    } else {
      ElMessage.error(res.message || '操作失败')
      // 恢复状态
      row.is_auto_block = !val
    }
  } catch (error) {
    ElMessage.error('操作失败')
    // 恢复状态
    row.is_auto_block = !val
  } finally {
    row.switching = false
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const data = {
          name: form.name,
          provider: form.provider,
          model_name: form.model_name,
          api_url: form.api_url,
          api_key: form.api_key,
          description: form.description
        }
        
        let res: any
        if (isEdit.value) {
          res = await updateAIConfig(form.id, data)
        } else {
          res = await createAIConfig(data)
        }
        
        if (res.code === 200) {
          ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
          dialogVisible.value = false
          fetchConfigs()
        } else {
          ElMessage.error(res.message || '操作失败')
        }
      } catch (error) {
        ElMessage.error('操作失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

onMounted(() => {
  fetchConfigs()
})
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.active-tag {
  box-shadow: 0 0 10px rgba(103, 194, 58, 0.5);
}
</style>
