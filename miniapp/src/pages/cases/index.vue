<template>
  <view class="cases-page">
    <!-- Search Bar -->
    <SearchBar v-model="keyword" placeholder="搜索设计案例..." @search="onSearch" />

    <!-- Filter Bar -->
    <view class="filter-bar">
      <view class="filter-item" @tap="toggleStyleDropdown">
        <text>{{ activeStyleTag || '全部风格' }}</text>
        <text>▾</text>
      </view>
      <view class="filter-item" @tap="toggleCategoryDropdown">
        <text>{{ activeCategoryTag || '全部类型' }}</text>
        <text>▾</text>
      </view>
    </view>

    <!-- Style Dropdown -->
    <view v-if="showStyleDropdown" class="dropdown">
      <view
        v-for="tag in allStyleTags"
        :key="tag"
        :class="['tag-pill', { active: activeStyleTag === tag }]"
        @tap="selectStyleTag(tag)"
      >
        {{ tag }}
      </view>
    </view>

    <!-- Category Dropdown -->
    <view v-if="showCategoryDropdown" class="dropdown">
      <view
        v-for="tag in allCategoryTags"
        :key="tag"
        :class="['tag-pill', { active: activeCategoryTag === tag }]"
        @tap="selectCategoryTag(tag)"
      >
        {{ tag }}
      </view>
    </view>

    <!-- Loading State -->
    <PageLoading v-if="loading" type="card" :count="4" />

    <!-- Error State -->
    <view v-else-if="errorMsg" class="error-state">
      <text class="error-icon">😞</text>
      <text class="error-text">{{ errorMsg }}</text>
      <view class="retry-btn" @tap="retry">
        <text>重新加载</text>
      </view>
    </view>

    <!-- Empty State -->
    <EmptyState
      v-else-if="cases.length === 0"
      icon="🎨"
      title="暂无案例"
      description="换个风格试试吧"
    />

    <!-- Case Waterfall Grid -->
    <view v-else class="case-grid">
      <CaseCard v-for="c in cases" :key="c.id" :caseData="c" @click="goToDetail" />
    </view>

    <!-- Load More -->
    <view class="load-more">
      <text v-if="loadingMore">加载中...</text>
      <text v-else-if="!hasMore && cases.length > 0">— 没有更多了 —</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import SearchBar from '../../components/SearchBar.vue'
import CaseCard from '../../components/CaseCard.vue'
import PageLoading from '../../components/PageLoading.vue'
import EmptyState from '../../components/EmptyState.vue'
import { getCaseList, getStyleTags, getCategoryTags } from '../../api/cases'
import type { DesignCase } from '../../api/cases'
import { PAGE_SIZE } from '../../utils/constants'

const loading = ref(true)
const errorMsg = ref('')
const cases = ref<DesignCase[]>([])
const page = ref(1)
const loadingMore = ref(false)
const hasMore = ref(true)
const keyword = ref('')
const activeStyleTag = ref('')
const activeCategoryTag = ref('')
const styleTags = ref<string[]>([])
const categoryTags = ref<string[]>([])
const showStyleDropdown = ref(false)
const showCategoryDropdown = ref(false)

const allStyleTags = computed(() => ['全部风格', ...styleTags.value])
const allCategoryTags = computed(() => ['全部类型', ...categoryTags.value])

async function loadTags() {
  try {
    const [sRes, cRes] = await Promise.all([getStyleTags(), getCategoryTags()])
    styleTags.value = sRes.data || []
    categoryTags.value = cRes.data || []
  } catch {
    // Tags are non-critical; fail silently
  }
}

async function loadCases(isRefresh = false) {
  if (isRefresh) {
    page.value = 1
    loading.value = true
  } else if (page.value === 1) {
    loading.value = true
  } else {
    loadingMore.value = true
  }
  errorMsg.value = ''

  try {
    const params: any = { page: page.value, page_size: 20 }
    if (activeStyleTag.value) params.style_tag = activeStyleTag.value
    if (activeCategoryTag.value) params.category_tag = activeCategoryTag.value
    if (keyword.value.trim()) params.keyword = keyword.value.trim()

    const res = await getCaseList(params)

    if (isRefresh || page.value === 1) {
      cases.value = res.data.list
    } else {
      cases.value = [...cases.value, ...res.data.list]
    }

    hasMore.value = res.data.list.length >= PAGE_SIZE
  } catch (err: any) {
    errorMsg.value = err.message || '加载失败'
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function toggleStyleDropdown() {
  showStyleDropdown.value = !showStyleDropdown.value
  showCategoryDropdown.value = false
}

function toggleCategoryDropdown() {
  showCategoryDropdown.value = !showCategoryDropdown.value
  showStyleDropdown.value = false
}

function selectStyleTag(tag: string) {
  activeStyleTag.value = tag === '全部风格' ? '' : tag
  showStyleDropdown.value = false
  page.value = 1
  loadCases()
}

function selectCategoryTag(tag: string) {
  activeCategoryTag.value = tag === '全部类型' ? '' : tag
  showCategoryDropdown.value = false
  page.value = 1
  loadCases()
}

function onSearch(kw: string) {
  keyword.value = kw
  page.value = 1
  loadCases()
}

function goToDetail(id: string | number) {
  uni.navigateTo({ url: '/pages/cases/detail?id=' + id })
}

function retry() {
  page.value = 1
  loadCases()
}

onLoad(() => {
  loadTags()
  loadCases()
})

onPullDownRefresh(() => {
  loadCases(true).finally(() => {
    uni.stopPullDownRefresh()
  })
})

onReachBottom(() => {
  if (!loadingMore.value && hasMore.value) {
    page.value++
    loadCases()
  }
})
</script>

<style scoped>
.cases-page {
  min-height: 100vh;
  background-color: #FFF8F0;
  padding-bottom: 40rpx;
}

/* Filter bar */
.filter-bar {
  display: flex;
  align-items: center;
  padding: 20rpx 28rpx;
  gap: 20rpx;
  background-color: #FFFFFF;
  border-bottom: 1rpx solid #f0e0d0;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 12rpx 28rpx;
  background-color: #FFF0F0;
  border-radius: 32rpx;
  font-size: 24rpx;
  color: #4a3728;
  border: 1rpx solid #FFA5A5;
}

/* Dropdown */
.dropdown {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  padding: 20rpx 28rpx;
  background-color: #FFFFFF;
  border-bottom: 1rpx solid #f0e0d0;
}

.tag-pill {
  padding: 10rpx 24rpx;
  border-radius: 32rpx;
  font-size: 24rpx;
  color: #7a6a5a;
  background-color: #f5f5f5;
  border: 1rpx solid #f0e0d0;
}

.tag-pill.active {
  color: #FFFFFF;
  background-color: #FF7B7B;
  border-color: #FF7B7B;
}

/* Error state */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 40rpx;
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

/* Case grid */
.case-grid {
  display: flex;
  flex-wrap: wrap;
  padding: 16rpx;
  gap: 16rpx;
}

/* Load more */
.load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32rpx 0;
  font-size: 24rpx;
  color: #b0a090;
}
</style>
