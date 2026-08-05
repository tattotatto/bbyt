<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="login-title">HX Mall 管理后台</h1>
      <p class="login-subtitle">儿童产品 B2B 批发商城</p>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="phone">
          <el-input
            v-model="form.phone"
            placeholder="请输入手机号"
            :maxlength="11"
            size="large"
          >
            <template #prefix>
              <el-icon><Phone /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
            size="large"
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Phone, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  phone: '',
  password: '',
})

const rules: FormRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' },
  ],
}

async function handleLogin() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login(form.phone, form.password)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (error: any) {
    const msg = error?.response?.data?.message || error?.message || '登录失败，请重试'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 100vh;
  background: linear-gradient(135deg, var(--color-bg) 0%, #ffe8e0 100%);
}

.login-card {
  width: 420px;
  padding: 48px 40px 40px;
  background: #fff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.login-title {
  text-align: center;
  font-size: 26px;
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: 8px;
}

.login-subtitle {
  text-align: center;
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: 36px;
}

.login-form {
  .el-form-item {
    margin-bottom: 22px;
  }
}

.login-btn {
  width: 100%;
  border-radius: 50px;
  font-size: 18px;
  letter-spacing: 8px;
  height: 46px;
}
</style>
