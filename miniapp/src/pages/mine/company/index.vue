<template>
  <view class="company-page">
    <!-- ================================================================ -->
    <!--  STATE: LOADING -->
    <!-- ================================================================ -->
    <template v-if="pageState === 'loading'">
      <PageLoading type="full" />
    </template>

    <!-- ================================================================ -->
    <!--  STATE: ERROR -->
    <!-- ================================================================ -->
    <template v-else-if="pageState === 'error'">
      <EmptyState
        icon="⚠️"
        title="加载失败"
        description="网络好像开小差了，请检查网络后重试"
        :showButton="true"
        buttonText="重新加载"
        @buttonClick="loadProfile"
      />
    </template>

    <!-- ================================================================ -->
    <!--  STATE: NOT LOGGED IN -->
    <!-- ================================================================ -->
    <template v-else-if="!userStore.isLoggedIn">
      <EmptyState
        icon="🔐"
        title="请先登录"
        description="登录后即可管理企业信息"
        :showButton="true"
        buttonText="去登录"
        @buttonClick="goToLogin"
      />
    </template>

    <!-- ================================================================ -->
    <!--  STATE: CONTENT — Company Profile Form -->
    <!-- ================================================================ -->
    <template v-else>
      <!-- Hint text -->
      <view class="form-hint">
        <text class="form-hint-text">完善企业信息，享受更优采购服务</text>
      </view>

      <!-- Form Card -->
      <view class="form-card">
        <view class="form-item">
          <text class="form-label">公司名称 <text class="form-required">*</text></text>
          <input
            class="form-input"
            v-model="form.company_name"
            placeholder="请输入公司名称"
            placeholder-style="color: #c4b5a5"
            maxlength="100"
          />
        </view>
        <view class="form-item">
          <text class="form-label">营业执照号</text>
          <input
            class="form-input"
            v-model="form.business_license"
            placeholder="请输入营业执照号"
            placeholder-style="color: #c4b5a5"
            maxlength="50"
          />
        </view>
        <view class="form-item form-item--last">
          <text class="form-label">联系人</text>
          <input
            class="form-input"
            v-model="form.contact_person"
            placeholder="请输入联系人姓名"
            placeholder-style="color: #c4b5a5"
            maxlength="30"
          />
        </view>
      </view>

      <!-- Save Button -->
      <view class="save-section">
        <view
          class="btn-save"
          :class="{ 'btn-save--disabled': !canSave || saving }"
          @tap="handleSave"
        >
          <text class="btn-save-text">{{ saving ? '保存中...' : '保存' }}</text>
        </view>
      </view>

      <!-- Safe Area Bottom -->
      <view class="safe-bottom" :style="{ height: safeBottom + 'px' }" />
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import PageLoading from '../../../components/PageLoading.vue'
import EmptyState from '../../../components/EmptyState.vue'
import { useUserStore } from '../../../stores/user'
import { getUserProfile, updateUserProfile } from '../../../api/auth'
import type { RetailerProfileUpdate } from '../../../api/auth'
import { showSuccess, showError, showLoading, hideLoading } from '../../../utils'

const userStore = useUserStore()

// ── Page State ──────────────────────────────────────────────────────────────────
type PageState = 'loading' | 'error' | 'content'
const pageState = ref<PageState>('loading')

// ── Form State ──────────────────────────────────────────────────────────────────
const form = reactive<RetailerProfileUpdate>({
  company_name: '',
  business_license: '',
  contact_person: '',
})

const saving = ref(false)

// ── Computed ────────────────────────────────────────────────────────────────────
const canSave = computed(() => !!form.company_name?.trim())

const safeBottom = computed(() => {
  try {
    const info = uni.getSystemInfoSync()
    const bottom = info.safeAreaInsets?.bottom || info.safeArea?.bottom || 0
    return Math.max(bottom, 20)
  } catch {
    return 20
  }
})

// ── Data Loading ────────────────────────────────────────────────────────────────
async function loadProfile(): Promise<void> {
  if (!userStore.isLoggedIn) {
    pageState.value = 'content'
    return
  }
  pageState.value = 'loading'
  try {
    const res = await getUserProfile()
    const rp = res.data.retailer_profile
    if (rp) {
      form.company_name = rp.company_name || ''
      form.business_license = rp.business_license || ''
      form.contact_person = rp.contact_person || ''
    }
    pageState.value = 'content'
  } catch {
    pageState.value = 'error'
  }
}

// ── Save ────────────────────────────────────────────────────────────────────────
async function handleSave(): Promise<void> {
  if (!canSave.value || saving.value) return

  saving.value = true
  showLoading('保存中...')

  // Build payload with non-empty fields only (partial update)
  const payload: RetailerProfileUpdate = {}
  const companyName = (form.company_name ?? '').trim()
  const bizLicense = (form.business_license ?? '').trim()
  const contactPerson = (form.contact_person ?? '').trim()
  if (companyName) payload.company_name = companyName
  if (bizLicense) payload.business_license = bizLicense
  if (contactPerson) payload.contact_person = contactPerson

  try {
    await updateUserProfile(payload)
    hideLoading()
    showSuccess('保存成功')
    // Brief delay so the user sees the success toast before navigating back
    setTimeout(() => {
      uni.navigateBack()
    }, 800)
  } catch {
    hideLoading()
    showError('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

// ── Navigation ──────────────────────────────────────────────────────────────────
function goToLogin(): void {
  uni.switchTab({ url: '/pages/mine/index' })
}

// ── Lifecycle ───────────────────────────────────────────────────────────────────
onShow(() => {
  loadProfile()
})
</script>

<style scoped>
.company-page {
  min-height: 100vh;
  background: #FFF8F0;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

/* ========================================================================== */
/*  FORM HINT                                                                 */
/* ========================================================================== */
.form-hint {
  padding: 24rpx 32rpx 8rpx;
}

.form-hint-text {
  font-size: 24rpx;
  color: #7a6a5a;
  line-height: 1.5;
}

/* ========================================================================== */
/*  FORM CARD                                                                 */
/* ========================================================================== */
.form-card {
  background: #ffffff;
  border-radius: 20px;
  margin: 16rpx 24rpx 0;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.form-item {
  padding: 28rpx 32rpx;
  border-bottom: 1px solid #f5f5f5;
}

.form-item--last {
  border-bottom: none;
}

.form-label {
  font-size: 28rpx;
  font-weight: 500;
  color: #4a3728;
  display: block;
  margin-bottom: 16rpx;
}

.form-required {
  color: #FF7B7B;
}

.form-input {
  width: 100%;
  height: 80rpx;
  background: #faf7f2;
  border-radius: 12px;
  padding: 0 24rpx;
  font-size: 28rpx;
  color: #4a3728;
  box-sizing: border-box;
}

/* ========================================================================== */
/*  SAVE BUTTON                                                               */
/* ========================================================================== */
.save-section {
  padding: 48rpx 24rpx 0;
}

.btn-save {
  width: 100%;
  height: 88rpx;
  border-radius: 50px;
  background: linear-gradient(135deg, #FF7B7B, #FF9B9B);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s ease;
  box-shadow: 0 4px 20px rgba(255, 123, 123, 0.3);
}

.btn-save--disabled {
  opacity: 0.5;
}

.btn-save-text {
  font-size: 30rpx;
  font-weight: 600;
  color: #ffffff;
}

/* ========================================================================== */
/*  SAFE AREA BOTTOM                                                          */
/* ========================================================================== */
.safe-bottom {
  width: 100%;
}
</style>
