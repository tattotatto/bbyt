<template>
  <view class="products-page">
    <!-- SearchBar at top -->
    <view class="search-wrap">
      <SearchBar
        v-model="keyword"
        placeholder="搜索儿童产品..."
        @search="onSearch"
      />
    </view>

    <!-- Category tabs - horizontal scroll of pill tabs from API -->
    <view class="cat-section">
      <scroll-view scroll-x class="cat-scroll" :show-scrollbar="false">
        <view class="cat-list">
          <view
            v-for="cat in categoryList"
            :key="cat.id"
            :class="['cat-pill', { active: activeCategoryId === cat.id }]"
            @tap="onCategoryChange(cat.id)"
          >
            {{ cat.name }}
          </view>
        </view>
      </scroll-view>
    </view>

    <!-- Filter bar -->
    <view class="filter-bar">
      <view class="filter-item" @tap="cycleAgeFilter">
        <text>{{ ageFilterLabel }}</text>
      </view>
      <view class="filter-item" @tap="cycleSortFilter">
        <text>{{ sortFilterLabel }}</text>
      </view>
      <view class="filter-item" @tap="toggleStockFilter">
        <text>仅看有货</text>
        <text :class="{ check: true, 'check--active': onlyInStock }">
          {{ onlyInStock ? '☑' : '☐' }}
        </text>
      </view>
    </view>

    <!-- Loading state -->
    <PageLoading v-if="loading" type="card" :count="4" />

    <!-- Error state -->
    <view v-else-if="errorMsg" class="error-state">
      <view class="error-circle">
        <text class="error-circle-icon">!</text>
      </view>
      <text class="error-text">{{ errorMsg }}</text>
      <view class="error-retry" @tap="retry">
        <text class="error-retry-text">重新加载</text>
      </view>
    </view>

    <!-- Empty state -->
    <EmptyState
      v-else-if="products.length === 0"
      icon="📦"
      title="暂无商品"
      description="换个分类试试吧"
      :showButton="false"
    />

    <!-- Product grid -->
    <view v-else class="product-grid">
      <ProductCard
        v-for="p in products"
        :key="p.id"
        :product="p"
        class="grid-card"
        @click="goToDetail"
      />
    </view>

    <!-- Load more -->
    <view v-if="!loading && products.length > 0" class="load-more">
      <text v-if="loadingMore" class="load-more-text">加载中...</text>
      <text v-else-if="!hasMore" class="load-more-text load-more-text--end">— 没有更多了 —</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import SearchBar from '../../components/SearchBar.vue'
import ProductCard from '../../components/ProductCard.vue'
import PageLoading from '../../components/PageLoading.vue'
import EmptyState from '../../components/EmptyState.vue'
import { getCategories, getProductList } from '../../api/products'
import type { Product, Category } from '../../api/products'

// ── State ──────────────────────────────────────────────
const loading = ref(true)
const errorMsg = ref('')
const products = ref<Product[]>([])
const page = ref(1)
const loadingMore = ref(false)
const hasMore = ref(true)

// ── Filters ────────────────────────────────────────────
const keyword = ref('')
const activeCategoryId = ref(0)
const categoryList = ref<{ id: string | number; name: string; icon: string }[]>([
  { id: 0, name: '全部', icon: '' }
])

const ageFilterIndex = ref(0) // 0=全部, 1=0-3岁, 2=3-6岁, 3=6-12岁
const ageRanges = ['', '0-3岁', '3-6岁', '6-12岁']

const sortIndex = ref(0) // 0=综合(default), 1=newest, 2=sales_desc, 3=price_asc, 4=price_desc
const sortValues = ['', 'newest', 'sales_desc', 'price_asc', 'price_desc']
const sortLabels = ['综合', '最新', '销量优先', '价格升序', '价格降序']

const onlyInStock = ref(false)

// ── Computed labels ────────────────────────────────────
const ageFilterLabel = computed(() => {
  return ageFilterIndex.value === 0 ? '适龄▾' : ageRanges[ageFilterIndex.value]
})

const sortFilterLabel = computed(() => {
  const base = sortLabels[sortIndex.value]
  return sortIndex.value === 0 ? base + '▾' : base
})

// ── Load categories ────────────────────────────────────
async function loadCategories() {
  try {
    const res = await getCategories()
    const list: { id: string | number; name: string; icon: string }[] = [{ id: 0, name: '全部', icon: '' }]
    if (res.data && res.data.length > 0) {
      res.data.forEach((cat: Category) => {
        list.push({ id: cat.id, name: cat.name, icon: cat.icon ?? '' })
      })
    }
    categoryList.value = list
  } catch {
    // keep default "全部"
  }
}

// ── Load products ──────────────────────────────────────
async function loadProducts(isRefresh = false) {
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
    const sortValue = sortValues[sortIndex.value]
    interface LoadParams {
      page: number
      page_size: number
      category_id?: string
      keyword?: string
      age_range?: string
      sort?: 'newest' | 'sales_desc' | 'price_asc' | 'price_desc'
    }
    const params: LoadParams = {
      page: page.value,
      page_size: 20,
    }
    if (activeCategoryId.value > 0) {
      params.category_id = String(activeCategoryId.value)
    }
    if (keyword.value.trim()) {
      params.keyword = keyword.value.trim()
    }
    if (ageFilterIndex.value > 0) {
      params.age_range = ageRanges[ageFilterIndex.value]
    }
    if (sortValue) {
      params.sort = sortValue as LoadParams['sort']
    }

    const res = await getProductList(params)
    let list = res.data.items || []

    // Client-side stock filter
    if (onlyInStock.value) {
      list = list.filter((p: Product) => (p.stock ?? 0) > 0)
    }

    if (isRefresh || page.value === 1) {
      products.value = list
    } else {
      products.value = [...products.value, ...list]
    }

    hasMore.value = list.length >= 20
  } catch (err: any) {
    errorMsg.value = err.message || err.msg || '加载失败'
    if (page.value > 1) page.value--
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// ── Filter cyclers ─────────────────────────────────────
function cycleAgeFilter() {
  ageFilterIndex.value = (ageFilterIndex.value + 1) % 4
}

function cycleSortFilter() {
  sortIndex.value = (sortIndex.value + 1) % 5
}

function toggleStockFilter() {
  onlyInStock.value = !onlyInStock.value
}

// ── Watch filters to reload ────────────────────────────
watch([ageFilterIndex, sortIndex, onlyInStock], () => {
  page.value = 1
  loadProducts(true)
})

// ── Event handlers ─────────────────────────────────────
function onCategoryChange(catId: string | number) {
  if (activeCategoryId.value === catId) return
  activeCategoryId.value = Number(catId) || 0
  page.value = 1
  loadProducts(true)
}

function onSearch(kw: string) {
  keyword.value = kw
  page.value = 1
  loadProducts(true)
}

function goToDetail(id: string | number) {
  uni.navigateTo({ url: '/pages/products/detail?id=' + id })
}

function retry() {
  loadProducts(true)
}

// ── Lifecycle ──────────────────────────────────────────
onLoad((options: any) => {
  if (options?.category_id) {
    activeCategoryId.value = Number(options.category_id)
  }
  if (options?.keyword) {
    keyword.value = options.keyword
  }
  if (options?.age_range) {
    const idx = ageRanges.indexOf(options.age_range)
    if (idx > 0) ageFilterIndex.value = idx
  }

  loadCategories()
  loadProducts(true)
})

onPullDownRefresh(() => {
  loadProducts(true).finally(() => {
    uni.stopPullDownRefresh()
  })
})

onReachBottom(() => {
  if (!loadingMore.value && hasMore.value) {
    page.value++
    loadProducts()
  }
})
</script>

<style scoped>
.products-page {
  min-height: 100vh;
  background: #FFF8F0;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

/* ── Search ──────────────────────────────────────────── */
.search-wrap {
  padding: 20rpx 24rpx;
  background: #FFFFFF;
}

/* ── Category tabs ───────────────────────────────────── */
.cat-section {
  background: #FFFFFF;
  padding-bottom: 16rpx;
  border-bottom: 1px solid #f0e0d0;
}

.cat-scroll {
  white-space: nowrap;
}

.cat-list {
  display: flex;
  flex-direction: row;
  padding: 0 24rpx;
  gap: 12rpx;
}

.cat-pill {
  flex-shrink: 0;
  display: inline-block;
  padding: 8rpx 24rpx;
  font-size: 26rpx;
  color: #7a6a5a;
  white-space: nowrap;
  position: relative;
}

.cat-pill.active {
  color: #FF7B7B;
  font-weight: 600;
}

.cat-pill.active::after {
  content: '';
  position: absolute;
  bottom: -2rpx;
  left: 50%;
  transform: translateX(-50%);
  width: 40rpx;
  height: 4rpx;
  border-radius: 2px;
  background: #FF7B7B;
}

/* ── Filter bar ──────────────────────────────────────── */
.filter-bar {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-around;
  background: #FFFFFF;
  padding: 16rpx 24rpx;
  border-bottom: 1px solid #f0e0d0;
}

.filter-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 6rpx;
  font-size: 26rpx;
  color: #7a6a5a;
  padding: 4rpx 8rpx;
}

.check {
  font-size: 26rpx;
  color: #b0a090;
}

.check--active {
  color: #FF7B7B;
  font-weight: 600;
}

/* ── Error state ─────────────────────────────────────── */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 40rpx;
}

.error-circle {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background: #FF7B7B;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24rpx;
}

.error-circle-icon {
  font-size: 40rpx;
  font-weight: 700;
  color: #FFFFFF;
}

.error-text {
  font-size: 28rpx;
  color: #7a6a5a;
  text-align: center;
  margin-bottom: 32rpx;
  line-height: 1.5;
}

.error-retry {
  background: #FF7B7B;
  border-radius: 50px;
  padding: 14px 48px;
}

.error-retry-text {
  font-size: 28rpx;
  color: #FFFFFF;
  font-weight: 500;
}

/* ── Product grid ────────────────────────────────────── */
.product-grid {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  padding: 20rpx;
  gap: 20rpx;
}

.grid-card {
  width: calc(50% - 10rpx);
}

/* ── Load more ───────────────────────────────────────── */
.load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30rpx 0 40rpx;
}

.load-more-text {
  font-size: 26rpx;
  color: #7a6a5a;
}

.load-more-text--end {
  color: #b0a090;
}
</style>
