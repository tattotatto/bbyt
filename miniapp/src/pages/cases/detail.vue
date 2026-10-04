<template>
  <view class="case-detail">
    <!-- Loading State -->
    <PageLoading v-if="loading" type="detail" />

    <!-- Error State -->
    <view v-else-if="errorMsg" class="error-state">
      <text class="error-icon">😞</text>
      <text class="error-text">{{ errorMsg }}</text>
      <view class="retry-btn" @tap="retry">
        <text>重新加载</text>
      </view>
    </view>

    <!-- Empty / Not Found State -->
    <EmptyState v-else-if="!caseData" icon="🎨" title="案例不存在" />

    <!-- Content -->
    <template v-else>
      <!-- Full-screen Image Swiper -->
      <swiper class="image-swiper" indicator-dots circular>
        <swiper-item v-for="(img, i) in caseData.images" :key="i" @tap="previewImage(i)">
          <image :src="img" mode="aspectFill" lazy-load class="swiper-img" />
        </swiper-item>
      </swiper>

      <!-- Info Card -->
      <view class="info-card">
        <text class="case-title">{{ caseData.title }}</text>

        <!-- Tags -->
        <view class="tags-section">
          <text v-for="tag in caseData.style_tags" :key="tag" class="tag tag-style">{{ tag }}</text>
          <text v-for="tag in caseData.category_tags" :key="tag" class="tag tag-category">{{ tag }}</text>
        </view>

        <!-- Description -->
        <text class="case-desc">{{ caseData.description }}</text>
      </view>

      <!-- Bottom Safe Area Spacer -->
      <view class="bottom-spacer" />
    </template>

    <!-- Fixed Bottom Bar -->
    <view v-if="caseData" class="bottom-bar">
      <view class="btn-contact" @tap="handleContact">
        <text>咨询店面设计</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import PageLoading from '../../components/PageLoading.vue'
import EmptyState from '../../components/EmptyState.vue'
import { getCaseDetail } from '../../api/cases'
import type { DesignCase } from '../../api/cases'
import { showSuccess } from '../../utils/index'

const loading = ref(true)
const errorMsg = ref('')
const caseData = ref<DesignCase | null>(null)
const caseId = ref('')

async function loadCase(id: string) {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await getCaseDetail(id)
    caseData.value = res.data
  } catch (err: any) {
    errorMsg.value = err.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onLoad((options: any) => {
  const id = options?.id
  if (id) {
    caseId.value = id
    loadCase(id)
  } else {
    errorMsg.value = '案例ID无效'
  }
})

function previewImage(index: number) {
  if (!caseData.value?.images.length) return
  uni.previewImage({
    current: index,
    urls: caseData.value.images,
  })
}

function handleContact() {
  showSuccess('已通知设计师团队，稍后与您联系')
}

function retry() {
  // 用 onLoad 存下来的 id，不能用 caseData.value?.id：
  // 加载失败时 caseData 是 null，那个前置条件恰好让错误态的按钮变成死按钮。
  if (caseId.value) {
    loadCase(caseId.value)
  }
}
</script>

<style scoped>
.case-detail {
  min-height: 100vh;
  background-color: #FFF8F0;
}

/* Error state */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 160rpx 40rpx;
}

.error-icon {
  font-size: 80rpx;
  margin-bottom: 24rpx;
}

.error-text {
  font-size: 26rpx;
  color: #7a6a5a;
  margin-bottom: 32rpx;
  text-align: center;
}

.retry-btn {
  padding: 16rpx 48rpx;
  background-color: #e16531;
  border-radius: 32rpx;
  font-size: 26rpx;
  color: #FFFFFF;
}

/* Image swiper */
.image-swiper {
  width: 100%;
  height: 750rpx;
}

.swiper-img {
  width: 100%;
  height: 100%;
}

/* Info card */
.info-card {
  background-color: #FFFFFF;
  border-radius: 16px;
  margin: 0 24rpx 16rpx;
  padding: 28rpx 32rpx;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.case-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #4a3728;
  line-height: 1.4;
  display: block;
}

/* Tags */
.tags-section {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 16rpx;
}

.tag {
  padding: 6rpx 18rpx;
  border-radius: 8px;
  font-size: 22rpx;
  font-weight: 500;
}

.tag-style {
  background-color: #FFF0F0;
  color: #e16531;
}

.tag-category {
  background-color: #F0F8FB;
  color: #7EC8E3;
}

/* Description */
.case-desc {
  display: block;
  margin-top: 24rpx;
  font-size: 26rpx;
  color: #7a6a5a;
  line-height: 1.8;
}

/* Bottom spacer */
.bottom-spacer {
  height: 120rpx;
}

/* Bottom bar - fixed with safe area */
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  gap: 20rpx;
  padding: 20rpx 32rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  background-color: #FFFFFF;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.04);
  z-index: 100;
}

.btn-contact {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 76rpx;
  border-radius: 50rpx;
  background-color: #e16531;
  font-size: 28rpx;
  font-weight: 600;
  color: #FFFFFF;
}
</style>
