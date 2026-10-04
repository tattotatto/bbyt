<template>
  <view class="case-card" @tap="handleClick">
    <view class="case-card__image-wrapper">
      <image
        v-if="coverImage"
        class="case-card__image"
        :src="coverImage"
        mode="widthFix"
      />
      <!-- 无图兜底：原来是 <image src="">，mode="widthFix" 下没有图就没有高度，
           整张卡会塌成一条，标题（绝对定位在底部）也没地方待。
           所以给一个定高的品牌色底纹。案例图目前还没有，这是常态而非例外。 -->
      <view v-else class="case-card__image case-card__image--placeholder">
        <AppIcon name="photo" :size="72" tone="white" />
      </view>
      <view class="case-card__gradient" />
      <text class="case-card__title">{{ caseData.title }}</text>
    </view>

    <view class="case-card__tags">
      <text
        v-if="caseData.store_area_range"
        class="case-card__tag case-card__tag--area"
      >
        {{ caseData.store_area_range }}
      </text>
      <text
        v-for="tag in caseData.style_tags"
        :key="tag"
        class="case-card__tag case-card__tag--style"
      >
        {{ tag }}
      </text>
      <text
        v-for="tag in caseData.category_tags"
        :key="tag"
        class="case-card__tag case-card__tag--category"
      >
        {{ tag }}
      </text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AppIcon from './AppIcon.vue'

interface DesignCase {
  id: string | number
  title: string
  images: string[]
  style_tags: string[]
  category_tags: string[]
  /**
   * 门店面积区间，如 "50-100㎡"。后端 CaseListOut 里是 `str | null`
   * （schemas/case.py、models/case.py 都有这个字段），所以这里可以加。
   *
   * 注意**不要**顺手加 age_range —— 后端 case 的 schema 里没有这个字段，
   * 加了就是又一个 phantom field。
   */
  store_area_range?: string | null
}

interface Props {
  caseData: DesignCase
}

const props = defineProps<Props>()

const emit = defineEmits<{
  click: [id: string | number]
}>()

const coverImage = computed(() => {
  const images = props.caseData.images || []
  return images.length ? images[0] : ''
})

function handleClick() {
  emit('click', props.caseData.id)
}
</script>

<style scoped>
.case-card {
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--bg-white);
  box-shadow: var(--shadow-card);
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
}

.case-card__image-wrapper {
  position: relative;
  width: 100%;
}

.case-card__image {
  width: 100%;
  display: block;
}

.case-card__image--placeholder {
  height: 360rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(115deg, var(--color-primary-light), var(--color-primary-mid));
  opacity: 0.9;
}

.case-card__gradient {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 80px;
  background-image: linear-gradient(to top, rgba(0, 0, 0, 0.5), transparent);
}

.case-card__title {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 0 16px 12px;
  font-size: 28rpx;
  font-weight: 500;
  color: var(--text-white);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.case-card__tags {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: var(--space-2xs);
  padding: 12px;
}

.case-card__tag {
  font-size: var(--font-xs);
  padding: 4rpx 12rpx;
  border-radius: var(--radius-sm);
  line-height: 1.4;
}

.case-card__tag--area {
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

/* 两个标签色是本地刻意的配色（暖橙 / 冷蓝），词表里没有对应语义 token，
   所以背景保留字面值；品牌色本身改走 --color-primary，免得它有两份。 */
.case-card__tag--style {
  background: #FFF8F0;
  color: var(--color-primary);
}

.case-card__tag--category {
  background: #f0f9ff;
  color: #7EC8E3;
}
</style>
