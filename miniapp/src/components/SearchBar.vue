<template>
  <view class="search-bar" :class="{ 'search-bar--inline': variant === 'inline' }">
    <view class="search-bar__icon">
      <AppIcon name="search" :size="30" tone="muted" />
    </view>
    <input
      class="search-bar__input"
      :value="modelValue"
      :placeholder="placeholder"
      :focus="autoFocus"
      placeholder-style="color: #c4b5a5"
      confirm-type="search"
      @input="onInput"
      @confirm="onConfirm"
      @focus="onFocus"
      @blur="onBlur"
    />
    <view
      v-if="modelValue"
      class="search-bar__clear"
      @tap.stop="onClear"
    >
      <AppIcon name="close" :size="28" tone="muted" />
    </view>
    <view
      v-else-if="showVoice"
      class="search-bar__voice"
      @tap.stop="onVoice"
    >
      <AppIcon name="mic" :size="30" tone="muted" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { watch, ref } from 'vue'
import AppIcon from './AppIcon.vue'

interface Props {
  placeholder?: string
  modelValue?: string
  showVoice?: boolean
  autoFocus?: boolean
  /** standalone = 自带背景阴影，独立使用；inline = 透明，由外层容器（如 BrandHero 的白胶囊）提供背景 */
  variant?: 'standalone' | 'inline'
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '搜索儿童产品...',
  modelValue: '',
  showVoice: true,
  autoFocus: false,
  variant: 'standalone',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  search: [keyword: string]
  voice: []
  focus: []
  blur: []
  clear: []
}>()

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function onInput(e: any) {
  const val = e.detail.value || ''
  emit('update:modelValue', val)
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function onConfirm(e: any) {
  const keyword = (e.detail.value || '').trim()
  if (keyword) {
    emit('search', keyword)
  }
}

function onClear() {
  emit('update:modelValue', '')
  emit('clear')
}

function onVoice() {
  emit('voice')
}

function onFocus() {
  emit('focus')
}

function onBlur() {
  emit('blur')
}
</script>

<style scoped>
.search-bar {
  display: flex;
  flex-direction: row;
  align-items: center;
  background: #fff;
  border-radius: 50px;
  padding: 0 20rpx;
  height: 72rpx;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

/* 图标的外观（尺寸、颜色）由 AppIcon 的 props 决定 —— 这里不再写
   color/font-size，否则它们会是一份和 tone="muted" 不一致的第二真相
   （旧值 #7a6a5a，muted 是 #a89a8a）。只留布局。 */
.search-bar__icon {
  margin-right: 12rpx;
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.search-bar__input {
  flex: 1;
  font-size: 28rpx;
  color: #4a3728;
  border: none;
  background: transparent;
  height: 72rpx;
  line-height: 72rpx;
}

.search-bar__clear {
  padding: 8rpx;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-bar__voice {
  padding: 8rpx;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* inline 变体的外层（BrandHero 的白胶囊）已经画了背景和圆角，
   自己再画一层就是双层白底。高度也交给外层定，这里只是填满。 */
.search-bar--inline {
  background: transparent;
  box-shadow: none;
  border: none;
  padding: 0;
  flex: 1;
}
</style>
