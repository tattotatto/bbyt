<template>
  <view class="address-page">
    <!-- ================================================================ -->
    <!--  STATE: LOADING -->
    <!-- ================================================================ -->
    <template v-if="pageState === 'loading'">
      <PageLoading type="list" :count="4" />
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
        @buttonClick="loadAddresses"
      />
    </template>

    <!-- ================================================================ -->
    <!--  STATE: NOT LOGGED IN -->
    <!-- ================================================================ -->
    <template v-else-if="!userStore.isLoggedIn">
      <EmptyState
        icon="🔐"
        title="请先登录"
        description="登录后即可管理收货地址"
        :showButton="true"
        buttonText="去登录"
        @buttonClick="goToLogin"
      />
    </template>

    <!-- ================================================================ -->
    <!--  VIEW: LIST -->
    <!-- ================================================================ -->
    <template v-else-if="viewMode === 'list'">
      <!-- EMPTY -->
      <template v-if="addresses.length === 0">
        <EmptyState
          icon="📍"
          title="暂无收货地址"
          description="添加一个收货地址吧"
          :showButton="true"
          buttonText="新增地址"
          @buttonClick="openAddForm"
        />
      </template>

      <!-- ADDRESS LIST -->
      <template v-else>
        <scroll-view
          class="address-scroll"
          :scroll-y="true"
          :style="{ height: scrollHeight + 'px' }"
        >
          <view
            v-for="addr in addresses"
            :key="addr.id"
            class="address-card"
          >
            <!-- Card Header: Name + Phone + Default Badge -->
            <view class="address-card__header">
              <view class="address-card__user">
                <text class="address-card__name">{{ addr.name }}</text>
                <text class="address-card__phone">{{ maskPhone(addr.phone) }}</text>
              </view>
              <view v-if="addr.is_default" class="address-card__badge">
                <text class="address-card__badge-text">默认</text>
              </view>
            </view>

            <!-- Card Body: Full Address -->
            <text class="address-card__region">
              {{ addr.province }}{{ addr.city }}{{ addr.district }} {{ addr.detail }}
            </text>

            <!-- Card Footer: Edit / Delete -->
            <view class="address-card__actions">
              <view
                class="address-card__action address-card__action--edit"
                @tap="openEditForm(addr)"
              >
                <text class="address-card__action-icon">✎</text>
                <text class="address-card__action-text">编辑</text>
              </view>
              <view
                class="address-card__action address-card__action--delete"
                @tap="onDeleteAddress(addr)"
              >
                <text class="address-card__action-icon">🗑</text>
                <text class="address-card__action-text">删除</text>
              </view>
            </view>
          </view>

          <!-- Bottom spacer -->
          <view class="address-list-spacer" />
        </scroll-view>
      </template>

      <!-- Bottom Add Button -->
      <view
        class="address-add-bar"
        :style="{ paddingBottom: safeBottom + 'px' }"
      >
        <view class="address-add-btn" @tap="openAddForm">
          <text class="address-add-btn__icon">+</text>
          <text class="address-add-btn__text">新增地址</text>
        </view>
      </view>
    </template>

    <!-- ================================================================ -->
    <!--  VIEW: FORM (Add / Edit) -->
    <!-- ================================================================ -->
    <template v-else-if="viewMode === 'form'">
      <!-- Form Hint -->
      <view class="form-hint">
        <text class="form-hint-text">{{ editingId ? '修改收货地址' : '新增收货地址' }}</text>
      </view>

      <!-- Form Card -->
      <view class="form-card">
        <!-- Name -->
        <view class="form-item">
          <text class="form-label">收货人 <text class="form-required">*</text></text>
          <input
            class="form-input"
            v-model="form.name"
            placeholder="请输入收货人姓名"
            placeholder-style="color: #c4b5a5"
            maxlength="30"
          />
        </view>

        <!-- Phone -->
        <view class="form-item">
          <text class="form-label">手机号码 <text class="form-required">*</text></text>
          <input
            class="form-input"
            v-model="form.phone"
            type="number"
            placeholder="请输入11位手机号码"
            placeholder-style="color: #c4b5a5"
            maxlength="11"
          />
        </view>

        <!-- Province -->
        <view class="form-item">
          <text class="form-label">省份 <text class="form-required">*</text></text>
          <input
            class="form-input"
            v-model="form.province"
            placeholder="请输入省份"
            placeholder-style="color: #c4b5a5"
            maxlength="20"
          />
        </view>

        <!-- City -->
        <view class="form-item">
          <text class="form-label">城市 <text class="form-required">*</text></text>
          <input
            class="form-input"
            v-model="form.city"
            placeholder="请输入城市"
            placeholder-style="color: #c4b5a5"
            maxlength="20"
          />
        </view>

        <!-- District -->
        <view class="form-item">
          <text class="form-label">区/县 <text class="form-required">*</text></text>
          <input
            class="form-input"
            v-model="form.district"
            placeholder="请输入区/县"
            placeholder-style="color: #c4b5a5"
            maxlength="20"
          />
        </view>

        <!-- Detail -->
        <view class="form-item">
          <text class="form-label">详细地址 <text class="form-required">*</text></text>
          <input
            class="form-input"
            v-model="form.detail"
            placeholder="街道、门牌号等"
            placeholder-style="color: #c4b5a5"
            maxlength="100"
          />
        </view>

        <!-- Default Toggle -->
        <view class="form-item form-item--last form-item--toggle">
          <text class="form-label">设为默认地址</text>
          <switch
            class="form-switch"
            :checked="form.is_default"
            color="#FF7B7B"
            @change="onToggleDefault"
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
        <view class="btn-cancel" @tap="switchToList">
          <text class="btn-cancel-text">取消</text>
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
import {
  getAddressList,
  createAddress,
  updateAddress,
  deleteAddress,
} from '../../../api/address'
import type { Address } from '../../../api/address'
import {
  maskPhone,
  showSuccess,
  showError,
  showLoading,
  hideLoading,
} from '../../../utils'
import { validateAddressForm, buildAddressPayload } from '../../../utils/address'

const userStore = useUserStore()

// ── Page State ──────────────────────────────────────────────────────────────────
type PageState = 'loading' | 'error' | 'content'
const pageState = ref<PageState>('loading')

type ViewMode = 'list' | 'form'
const viewMode = ref<ViewMode>('list')

// ── Address List ────────────────────────────────────────────────────────────────
const addresses = ref<Address[]>([])

// ── Form State ──────────────────────────────────────────────────────────────────
const editingId = ref<string | null>(null)

const emptyForm = (): Partial<Address> => ({
  name: '',
  phone: '',
  province: '',
  city: '',
  district: '',
  detail: '',
  is_default: false,
})

const form = reactive<Partial<Address>>(emptyForm())
const saving = ref(false)

// ── Layout ──────────────────────────────────────────────────────────────────────
const safeBottom = computed(() => {
  try {
    const info = uni.getSystemInfoSync()
    const bottom = info.safeAreaInsets?.bottom || info.safeArea?.bottom || 0
    return Math.max(bottom, 20)
  } catch {
    return 20
  }
})

// Cache pixel ratio once (based on 750rpx design width)
const CACHED_PIXEL_RATIO = (() => {
  try {
    const info = uni.getSystemInfoSync()
    return 750 / (info.screenWidth || 375)
  } catch {
    return 2
  }
})()

// Fixed elements height (add bar ≈ 140rpx)
const FIXED_HEIGHT_RPX = 140
const scrollHeight = computed(() => {
  const windowHeight = (() => {
    try {
      const info = uni.getSystemInfoSync()
      return info.windowHeight || 667
    } catch {
      return 667
    }
  })()
  const fixedPx = FIXED_HEIGHT_RPX / CACHED_PIXEL_RATIO
  return windowHeight - fixedPx
})

// ── Form Validation ─────────────────────────────────────────────────────────────
const canSave = computed(() => {
  return validateAddressForm(form).ok
})

// ── Data Loading ────────────────────────────────────────────────────────────────
async function loadAddresses(): Promise<void> {
  if (!userStore.isLoggedIn) {
    pageState.value = 'content'
    return
  }
  pageState.value = 'loading'
  try {
    const res = await getAddressList()
    addresses.value = Array.isArray(res.data) ? res.data : []
    pageState.value = 'content'
  } catch {
    pageState.value = 'error'
  }
}

// ── View Switching ──────────────────────────────────────────────────────────────
function switchToList(): void {
  viewMode.value = 'list'
  editingId.value = null
  Object.assign(form, emptyForm())
}

function openAddForm(): void {
  editingId.value = null
  Object.assign(form, emptyForm())
  viewMode.value = 'form'
}

function openEditForm(addr: Address): void {
  editingId.value = addr.id
  Object.assign(form, {
    name: addr.name,
    phone: addr.phone,
    province: addr.province,
    city: addr.city,
    district: addr.district,
    detail: addr.detail,
    is_default: addr.is_default,
  })
  viewMode.value = 'form'
}

// ── Toggle Default ──────────────────────────────────────────────────────────────
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function onToggleDefault(e: any): void {
  form.is_default = e.detail.value
}

// ── Save ────────────────────────────────────────────────────────────────────────
async function handleSave(): Promise<void> {
  if (saving.value) return

  // Full validation (required fields + phone format)
  const validation = validateAddressForm(form)
  if (!validation.ok) {
    const firstError = Object.values(validation.errors)[0]
    if (firstError) showError(firstError)
    return
  }

  saving.value = true
  showLoading('保存中...')

  const payload = buildAddressPayload(form)

  try {
    if (editingId.value) {
      await updateAddress(editingId.value, payload)
    } else {
      await createAddress(payload)
    }
    hideLoading()
    showSuccess(editingId.value ? '修改成功' : '添加成功')
    setTimeout(() => {
      switchToList()
      loadAddresses()
    }, 800)
  } catch {
    hideLoading()
    showError('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

// ── Delete ──────────────────────────────────────────────────────────────────────
function onDeleteAddress(addr: Address): void {
  uni.showModal({
    title: '确认删除',
    content: `确定要删除「${addr.name}」的收货地址吗？`,
    confirmText: '删除',
    confirmColor: '#FF7B7B',
    success: (res) => {
      if (res.confirm) {
        performDelete(addr.id)
      }
    },
  })
}

async function performDelete(id: string): Promise<void> {
  showLoading('删除中...')
  try {
    await deleteAddress(id)
    hideLoading()
    showSuccess('已删除')
    await loadAddresses()
  } catch {
    hideLoading()
    showError('删除失败，请重试')
  }
}

// ── Navigation ──────────────────────────────────────────────────────────────────
function goToLogin(): void {
  uni.switchTab({ url: '/pages/mine/index' })
}

// ── Lifecycle ───────────────────────────────────────────────────────────────────
onShow(() => {
  if (viewMode.value === 'list') {
    loadAddresses()
  }
})
</script>

<style scoped>
.address-page {
  min-height: 100vh;
  background: #FFF8F0;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

/* ========================================================================== */
/*  ADDRESS LIST SCROLL                                                       */
/* ========================================================================== */
.address-scroll {
  padding: 20rpx 20rpx 0;
}

.address-list-spacer {
  height: 20rpx;
}

/* ========================================================================== */
/*  ADDRESS CARD                                                              */
/* ========================================================================== */
.address-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 28rpx 24rpx;
  margin-bottom: 16rpx;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

/* Header: user info + default badge */
.address-card__header {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.address-card__user {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 20rpx;
}

.address-card__name {
  font-size: 30rpx;
  font-weight: 600;
  color: #4a3728;
}

.address-card__phone {
  font-size: 26rpx;
  color: #7a6a5a;
}

/* Default badge */
.address-card__badge {
  background: #FFF0F0;
  border: 1px solid #FF7B7B;
  border-radius: 8rpx;
  padding: 4rpx 16rpx;
  flex-shrink: 0;
}

.address-card__badge-text {
  font-size: 20rpx;
  color: #FF7B7B;
  font-weight: 500;
}

/* Body: region + detail */
.address-card__region {
  font-size: 26rpx;
  color: #4a3728;
  line-height: 1.5;
  display: block;
  margin-bottom: 20rpx;
}

/* Footer: actions */
.address-card__actions {
  display: flex;
  flex-direction: row;
  justify-content: flex-end;
  gap: 32rpx;
  border-top: 1px solid #f5f5f5;
  padding-top: 20rpx;
}

.address-card__action {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8rpx;
  padding: 4rpx 8rpx;
}

.address-card__action-icon {
  font-size: 26rpx;
  line-height: 1;
}

.address-card__action-text {
  font-size: 24rpx;
  color: #7a6a5a;
}

.address-card__action--edit .address-card__action-text {
  color: #FF7B7B;
}

/* ========================================================================== */
/*  BOTTOM ADD BAR                                                            */
/* ========================================================================== */
.address-add-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #FFF8F0;
  padding: 20rpx 24rpx;
  z-index: 100;
}

.address-add-btn {
  width: 100%;
  height: 88rpx;
  border-radius: 50px;
  background: linear-gradient(135deg, #FF7B7B, #FF9B9B);
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  box-shadow: 0 4px 20px rgba(255, 123, 123, 0.3);
  transition: opacity 0.2s ease;
}

.address-add-btn__icon {
  font-size: 36rpx;
  color: #ffffff;
  font-weight: 300;
  line-height: 1;
}

.address-add-btn__text {
  font-size: 30rpx;
  font-weight: 600;
  color: #ffffff;
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

.form-item--toggle {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
}

.form-item--toggle .form-label {
  margin-bottom: 0;
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

.btn-cancel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx 0;
}

.btn-cancel-text {
  font-size: 28rpx;
  color: #7a6a5a;
}

/* ========================================================================== */
/*  SAFE AREA BOTTOM                                                          */
/* ========================================================================== */
.safe-bottom {
  width: 100%;
}
</style>
