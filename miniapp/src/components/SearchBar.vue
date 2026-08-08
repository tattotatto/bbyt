<template>
  <view class="search-bar">
    <view class="search-bar__icon">🔍</view>
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
      <text class="search-bar__clear-icon">✕</text>
    </view>
    <view
      v-else-if="showVoice"
      class="search-bar__voice"
      @tap.stop="onVoice"
    >
      <text class="search-bar__voice-icon">🎤</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { watch, ref } from 'vue'

interface Props {
  placeholder?: string
  modelValue?: string
  showVoice?: boolean
  autoFocus?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '搜索儿童产品...',
  modelValue: '',
  showVoice: true,
  autoFocus: false,
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

.search-bar__icon {
  color: #7a6a5a;
  font-size: 32rpx;
  margin-right: 12rpx;
  flex-shrink: 0;
  line-height: 1;
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

.search-bar__clear-icon {
  color: #7a6a5a;
  font-size: 28rpx;
  line-height: 1;
}

.search-bar__voice {
  padding: 8rpx;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-bar__voice-icon {
  color: #FF7B7B;
  font-size: 32rpx;
  line-height: 1;
}
</style>
