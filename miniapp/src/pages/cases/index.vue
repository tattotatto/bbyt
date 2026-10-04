<template>
  <view class="page has-custom-tabbar">
    <!-- ① 品牌头图，紧凑版 + 搜索框（同商品页） -->
    <BrandHero
      title="设计案例"
      :compact="true"
      show-search
      @search="onSearchConfirm"
    />

    <!-- ② 上叠白卡：两层筛选 chips。
         分类行是后端 category_tags（儿童房 / 游戏区 …），风格行是
         style_tags（ins风 / 自然原木 …）—— 两组值在 seed 里就是分开的两列，
         合成一行会互相覆盖。风格行在没有风格标签时整行不渲染。 -->
    <SurfaceCard overlap>
      <view class="chips">
        <view
          v-for="c in categoryChips"
          :key="c.value ?? 'all'"
          class="chips__item"
          :class="{ 'chips__item--active': activeCategoryTag === c.value }"
          @tap="onCategoryTagSelect(c.value)"
        >
          <text class="chips__label" :class="{ 'chips__label--active': activeCategoryTag === c.value }">
            {{ c.label }}
          </text>
        </view>
      </view>

      <view v-if="styleTags.length" class="chips chips--sub">
        <view
          v-for="s in styleChips"
          :key="s.value ?? 'all-style'"
          class="chips__item chips__item--sm"
          :class="{ 'chips__item--active': activeStyleTag === s.value }"
          @tap="onStyleTagSelect(s.value)"
        >
          <text class="chips__label" :class="{ 'chips__label--active': activeStyleTag === s.value }">
            {{ s.label }}
          </text>
        </view>
      </view>
    </SurfaceCard>

    <SectionHeader title="精选案例" />

    <!-- 骨架紧贴筛选区下方，三种状态互斥 —— 排在网格之后会被上面的空网格
         顶出首屏（同商品页）。 -->
    <PageLoading v-if="loading" />

    <EmptyState
      v-else-if="errorMsg"
      :title="errorMsg"
      description="检查网络后点击重试"
      :show-button="true"
      button-text="重新加载"
      @button-click="retry"
    />

    <template v-else>
      <!-- ③ 两列瀑布流 -->
      <view class="grid">
        <CaseCard
          v-for="c in cases"
          :key="c.id"
          class="grid__item"
          :caseData="c"
          @click="goToCase"
        />
      </view>

      <EmptyState
        v-if="cases.length === 0 && !loadingMore"
        illustration="empty-page"
        title="暂无案例"
        description="换个风格或分类试试"
      />

      <view v-if="loadingMore" class="list-foot">加载中…</view>
      <view v-else-if="!hasMore && cases.length" class="list-foot">已经到底了</view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad, onShow, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import BrandHero from '../../components/BrandHero.vue'
import SurfaceCard from '../../components/SurfaceCard.vue'
import SectionHeader from '../../components/SectionHeader.vue'
import CaseCard from '../../components/CaseCard.vue'
import PageLoading from '../../components/PageLoading.vue'
import EmptyState from '../../components/EmptyState.vue'
import { getCaseList, getCaseTags } from '../../api/cases'
import type { DesignCase, CaseListParams } from '../../api/cases'
import { applyFallback } from '../../mock/fallback'
import { DEMO_CASES } from '../../mock/demo-data'
import { PAGE_SIZE } from '../../utils/constants'

// ── State ──────────────────────────────────────────────
const loading = ref(true)
const errorMsg = ref('')
const cases = ref<DesignCase[]>([])
const page = ref(1)
const loadingMore = ref(false)
const hasMore = ref(true)
const keyword = ref('')

// 初值是 undefined，chips 里「全部」那一项也是 undefined —— 两边必须是同一个值，
// 否则 `undefined === ''` 恒假，进页面时「全部」不高亮，看起来像没选中任何筛选。
const activeStyleTag = ref<string | undefined>(undefined)
const activeCategoryTag = ref<string | undefined>(undefined)
const styleTags = ref<string[]>([])
const categoryTags = ref<string[]>([])

// ── Tags ───────────────────────────────────────────────
const categoryChips = computed(() => [
  { value: undefined as string | undefined, label: '全部' },
  ...categoryTags.value.map((t) => ({ value: t as string | undefined, label: t })),
])

const styleChips = computed(() => [
  { value: undefined as string | undefined, label: '全部风格' },
  ...styleTags.value.map((t) => ({ value: t as string | undefined, label: t })),
])

async function loadTags() {
  try {
    const res = await getCaseTags()
    styleTags.value = res.data?.style_tags || []
    categoryTags.value = res.data?.category_tags || []
  } catch {
    // 标签是非关键路径。接口失败或后端仍是旧版本时，保持两个数组为空 ——
    // 筛选器只剩「全部」，页面照常可用。
  }
}

// ── Filter selection ───────────────────────────────────
// 原样透传：把 undefined 折成空串会让「全部」这一格再也点不亮（见上面的注释）。
function onCategoryTagSelect(value: string | undefined) {
  activeCategoryTag.value = value
  loadCases(true)
}

function onStyleTagSelect(value: string | undefined) {
  activeStyleTag.value = value
  loadCases(true)
}

function onSearchConfirm(kw: string) {
  keyword.value = kw
  loadCases(true)
}

// ── Load cases ─────────────────────────────────────────
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
    const params: CaseListParams = { page: page.value, page_size: PAGE_SIZE }
    if (activeStyleTag.value) params.style = activeStyleTag.value
    if (activeCategoryTag.value) params.category_tag = activeCategoryTag.value
    if (keyword.value.trim()) params.keyword = keyword.value.trim()

    const res = await getCaseList(params)
    const list = res.data.items || []

    if (isRefresh || page.value === 1) {
      // 只有第一页兜底。分页追加时若也兜底，「加载更多」会无限重复
      // 同一批演示案例 —— 空结果会被替换成完整列表而不是追加 0 条。
      cases.value = applyFallback(list, DEMO_CASES)
    } else {
      cases.value = [...cases.value, ...list]
    }

    hasMore.value = list.length >= PAGE_SIZE
  } catch (err: any) {
    errorMsg.value = err.message || err.msg || '加载失败'
    if (page.value > 1) page.value--
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function retry() {
  loadCases(true)
}

function goToCase(id: string | number) {
  uni.navigateTo({ url: `/pages/cases/detail?id=${id}` })
}

// ── Lifecycle ──────────────────────────────────────────
// 自定义 tabBar 是每个页面各自渲染的一份实例，状态不共享。这里写下本页在
// tabs 数组里的下标（案例 = 1）。组件优先按页面栈推断选中项。
onShow(() => {
  uni.setStorageSync('tabbar_selected', 1)
})

onLoad(() => {
  loadTags()
  loadCases(true)
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
.page {
  min-height: 100vh;
  background: var(--bg-primary);
}

/* ── 筛选 chips ───────────────────────────────────────── */
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.chips--sub {
  margin-top: var(--space-md);
}

.chips__item {
  padding: 12rpx 28rpx;
  border-radius: var(--radius-pill);
  background: var(--bg-secondary);
}

.chips__item--sm {
  padding: 8rpx 22rpx;
}

.chips__item--active {
  background: var(--color-primary);
}

.chips__label {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.chips__label--active {
  color: var(--text-white);
  font-weight: var(--font-weight-semibold);
}

/* ── 案例网格 ─────────────────────────────────────────── */
.grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  padding: 0 var(--space-lg);
}

.grid__item {
  width: calc((100% - var(--space-md)) / 2);
}

.list-foot {
  text-align: center;
  padding: var(--space-lg);
  font-size: var(--font-sm);
  color: var(--text-muted);
}
</style>
