<template>
  <view class="brand-hero" :class="{ 'brand-hero--compact': compact }" :style="{ paddingTop: heroPaddingTop }">
    <view class="brand-hero__row">
      <view class="brand-hero__brand">
        <view class="brand-hero__mark">
          <AppIcon name="bag-fill" :size="40" tone="primary" />
        </view>
        <view class="brand-hero__text">
          <text class="brand-hero__title">{{ title }}</text>
          <text v-if="slogan" class="brand-hero__slogan">{{ slogan }}</text>
        </view>
      </view>
      <view v-if="showLogin" class="brand-hero__login" @tap="$emit('login')">
        <text class="brand-hero__login-text">登录 / 注册</text>
      </view>
    </view>

    <view v-if="showSearch" class="brand-hero__search">
      <SearchBar
        v-model="keyword"
        variant="inline"
        placeholder="搜索商品 / 案例"
        :show-voice="true"
        @search="$emit('search', $event)"
        @voice="$emit('search', keyword)"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import AppIcon from './AppIcon.vue'
import SearchBar from './SearchBar.vue'
import { useAppStore } from '../stores/app'
import { heroPaddingTop as calcHeroPaddingTop } from '../utils'

/**
 * 品牌色头图区。
 *
 * 搜索框用 SearchBar 的 inline 变体嵌在头图里（白胶囊），而不是悬在
 * 头图下沿 —— 素材里搜索框是头图的一部分（spec §4.2）。复用它而不是
 * 在这里另写一个 input：SearchBar 已经有 v-model、清除、语音全套逻辑，
 * 重写一遍就是两处要维护。
 *
 * 品牌标用 AppIcon 而不是 emoji：旧版首页是 🧸，跨机型字形差异明显。
 */
const props = withDefaults(defineProps<{
  title: string
  slogan?: string
  showSearch?: boolean
  showLogin?: boolean
  compact?: boolean
}>(), {
  slogan: '',
  showSearch: false,
  showLogin: false,
  compact: false,
})

defineEmits<{
  search: [keyword: string]
  login: []
}>()

/**
 * 让开状态栏和右上角的微信胶囊按钮。
 *
 * 头图是全站第一个元素，所以它必须自己扛顶部留白 —— 用了这个组件的
 * 页面都在 pages.json 里设了 `navigationStyle: "custom"`（见 Task 8），
 * 没有系统导航栏帮忙撑开顶部。若哪天有页面忘了设 custom，这里会多出
 * 一块空白而不是顶到状态栏下面，是安全的那种失败。
 *
 * 让位量交给 utils 的 heroPaddingTop：右上角摆了「登录 / 注册」白胶囊时
 * 要整条让开导航栏（否则和微信自己的胶囊按钮叠在一起），左侧只有品牌块
 * 时不用。算式与实测依据都在那个函数的注释里。
 *
 * statusBarHeight 来自 stores/app（单位 px，是设备度量，不要转 rpx）。
 */
const appStore = useAppStore()

const heroPaddingTop = computed(() =>
  `${calcHeroPaddingTop(appStore.statusBarHeight, {
    showLogin: props.showLogin,
    compact: props.compact,
  })}px`
)

const keyword = ref('')
</script>

<style scoped>
.brand-hero {
  background: linear-gradient(160deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  /* padding-top 不在这里写 —— 它要读状态栏高度，由 heroPaddingTop 内联给出 */
  padding: 0 var(--space-lg) var(--space-4xl);
  position: relative;
}

.brand-hero--compact {
  padding-bottom: var(--space-3xl);
}

.brand-hero__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand-hero__brand {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.brand-hero__mark {
  width: 72rpx;
  height: 72rpx;
  border-radius: var(--radius-circle);
  background: var(--bg-white);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.brand-hero__text {
  display: flex;
  flex-direction: column;
}

.brand-hero__title {
  font-size: var(--font-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-white);
  line-height: var(--leading-tight);
}

.brand-hero__slogan {
  font-size: var(--font-sm);
  color: rgba(255, 255, 255, 0.85);
  margin-top: var(--space-2xs);
}

.brand-hero__login {
  background: var(--bg-white);
  border-radius: var(--radius-pill);
  padding: 12rpx 28rpx;
  flex-shrink: 0;
}

.brand-hero__login-text {
  font-size: var(--font-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
}

/* 白胶囊由头图这边提供；SearchBar 的 inline 变体自己不画背景和阴影 */
.brand-hero__search {
  margin-top: var(--space-xl);
  background: var(--bg-white);
  border-radius: var(--radius-pill);
  height: 72rpx;
  display: flex;
  align-items: center;
  padding: 0 var(--space-lg);
}
</style>
