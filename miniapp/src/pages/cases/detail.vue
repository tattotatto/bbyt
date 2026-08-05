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

        <!-- Designer Row -->
        <view v-if="caseData.designer_name" class="designer-row">
          <image
            v-if="caseData.designer_avatar"
            :src="caseData.designer_avatar"
            class="designer-avatar"
          />
          <text v-else class="designer-avatar--placeholder">👤</text>
          <text class="designer-name">{{ caseData.designer_name }}</text>
        </view>

        <!-- Stats Row -->
        <view class="stats-row">
          <view class="stat">
            <text class="stat-icon">👁</text>
            <text>{{ caseData.view_count }}</text>
          </view>
          <view class="stat">
            <text class="stat-icon">❤</text>
            <text>{{ caseData.like_count }}</text>
          </view>
        </view>

        <!-- Tags -->
        <view class="tags-section">
          <text v-for="tag in caseData.style_tags" :key="tag" class="tag tag-style">{{ tag }}</text>
          <text v-for="tag in caseData.category_tags" :key="tag" class="tag tag-category">{{ tag }}</text>
        </view>

        <!-- Description -->
        <text class="case-desc">{{ caseData.description }}</text>
      </view>

      <!-- Used Products (horizontal scroll) -->
      <view v-if="caseData.used_products && caseData.used_products.length" class="products-section">
        <text class="section-title">案例中使用的好物</text>
        <scroll-view scroll-x class="products-scroll">
          <view class="products-inner">
            <view
              v-for="p in caseData.used_products"
              :key="p.id"
              class="product-item"
              @tap="goToProduct(p.id)"
            >
              <image :src="p.image" mode="aspectFill" class="product-img" lazy-load />
              <text class="product-name">{{ p.name }}</text>
              <text class="product-price">{{ formatPrice(p.price) }}</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- Bottom Safe Area Spacer -->
      <view class="bottom-spacer" />
    </template>

    <!-- Fixed Bottom Bar -->
    <view v-if="caseData" class="bottom-bar">
      <view class="btn-like" :class="{ liked: isLiked }" @tap="toggleLike">
        <text>{{ isLiked ? '❤️' : '🤍' }}</text>
        <text>{{ isLiked ? '已收藏' : '收藏' }}</text>
      </view>
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
import { getCaseDetail, likeCase } from '../../api/cases'
import type { DesignCase } from '../../api/cases'
import { formatPrice, showSuccess, showError } from '../../utils/index'

const loading = ref(true)
const errorMsg = ref('')
const caseData = ref<DesignCase | null>(null)
const isLiked = ref(false)

async function loadCase(id: number) {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await getCaseDetail(id)
    caseData.value = res.data
    isLiked.value = res.data.is_liked
  } catch (err: any) {
    errorMsg.value = err.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onLoad((options: any) => {
  const id = Number(options?.id)
  if (id) {
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

async function toggleLike() {
  if (!caseData.value) return
  try {
    const res = await likeCase(caseData.value.id)
    isLiked.value = res.data.is_liked
    caseData.value.like_count = res.data.like_count
    showSuccess(isLiked.value ? '已收藏' : '已取消收藏')
  } catch (err: any) {
    showError('操作失败')
  }
}

function goToProduct(id: number) {
  uni.navigateTo({ url: '/pages/products/detail?id=' + id })
}

function handleContact() {
  showSuccess('已通知设计师团队，稍后与您联系')
}

function retry() {
  if (caseData.value?.id) {
    loadCase(caseData.value.id)
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
  background-color: #FF7B7B;
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

/* Designer row */
.designer-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 16rpx;
}

.designer-avatar {
  width: 52rpx;
  height: 52rpx;
  border-radius: 50rpx;
  overflow: hidden;
}

.designer-avatar--placeholder {
  width: 52rpx;
  height: 52rpx;
  border-radius: 50rpx;
  background-color: #FFF0F0;
  font-size: 30rpx;
  line-height: 52rpx;
  text-align: center;
}

.designer-name {
  font-size: 26rpx;
  color: #7a6a5a;
}

/* Stats row */
.stats-row {
  display: flex;
  gap: 32rpx;
  margin-top: 16rpx;
}

.stat {
  display: flex;
  align-items: center;
  gap: 6rpx;
}

.stat-icon {
  font-size: 28rpx;
}

.stat text:last-child {
  font-size: 24rpx;
  color: #7a6a5a;
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
  color: #FF7B7B;
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

/* Products section */
.products-section {
  background-color: #FFFFFF;
  border-radius: 16px;
  margin: 16rpx 24rpx;
  padding: 24rpx 0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #4a3728;
  padding: 0 32rpx 16rpx;
  display: block;
}

.products-scroll {
  white-space: nowrap;
}

.products-inner {
  display: flex;
  gap: 20rpx;
  padding: 0 32rpx;
}

.product-item {
  flex-shrink: 0;
  width: 200rpx;
  display: flex;
  flex-direction: column;
}

.product-img {
  width: 200rpx;
  height: 200rpx;
  border-radius: 12px;
  background-color: #FFF5EE;
}

.product-name {
  font-size: 24rpx;
  color: #4a3728;
  margin-top: 10rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-price {
  font-size: 26rpx;
  font-weight: 600;
  color: #FF7B7B;
  margin-top: 4rpx;
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

.btn-like {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  padding: 16rpx 32rpx;
  border-radius: 50rpx;
  border: 2rpx solid #f0e0d0;
  background-color: #FFFFFF;
  font-size: 26rpx;
  color: #7a6a5a;
  flex-shrink: 0;
}

.btn-like.liked {
  border-color: #FFA5A5;
  color: #FF7B7B;
}

.btn-contact {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 76rpx;
  border-radius: 50rpx;
  background-color: #FF7B7B;
  font-size: 28rpx;
  font-weight: 600;
  color: #FFFFFF;
}
</style>
