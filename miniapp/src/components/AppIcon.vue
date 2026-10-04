<template>
  <u-icon
    :name="name"
    :size="sizePx"
    :color="resolvedColor"
    :bold="bold"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'

/**
 * 全站唯一的图标出口。
 *
 * 为什么不直接在页面里写 u-icon：尺寸/色板的默认值散在 20 个页面里会立刻失配，
 * 而且以后换图标集时要改 20 个文件。这里收口。
 *
 * 注意 `<u-icon>` 不加 import —— pages.json 的 easycom 规则
 * `"^u-(.*)": "uview-plus/components/u-$1/u-$1.vue"` 会自动解析。
 */
type Tone = 'primary' | 'ink' | 'muted' | 'white' | 'inherit'

const props = withDefaults(defineProps<{
  /** u-icon 名，不带 uicon- 前缀，如 shopping-cart */
  name: string
  /** rpx 数字，与设计稿一致 */
  size?: number | string
  tone?: Tone
  bold?: boolean
}>(), {
  size: 32,
  tone: 'inherit',
  bold: false,
})

const TONE_COLORS: Record<Exclude<Tone, 'inherit'>, string> = {
  primary: '#e16531',
  ink: '#2B2320',
  muted: '#a89a8a',
  white: '#ffffff',
}

/** u-icon 的 size 走 px；我们的设计稿是 rpx。转换后交给它。 */
const sizePx = computed(() => {
  if (typeof props.size === 'string' && props.size.endsWith('rpx')) {
    const n = parseFloat(props.size)
    return `${(n * (uni.getSystemInfoSync().windowWidth || 375)) / 750}px`
  }
  const n = typeof props.size === 'number' ? props.size : parseFloat(props.size)
  if (Number.isNaN(n)) return '16px'
  return `${(n * (uni.getSystemInfoSync().windowWidth || 375)) / 750}px`
})

const resolvedColor = computed(() => {
  if (props.tone === 'inherit') return undefined   // 交给 CSS 的 currentColor
  return TONE_COLORS[props.tone]
})
</script>
