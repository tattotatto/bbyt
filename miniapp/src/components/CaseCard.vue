<template>
  <view class="case-card" @tap="handleClick">
    <view class="case-card__image-wrapper">
      <image
        class="case-card__image"
        :src="caseData.images && caseData.images.length ? caseData.images[0] : ''"
        mode="widthFix"
      />
      <view class="case-card__gradient" />
      <text class="case-card__title">{{ caseData.title }}</text>
    </view>

    <view class="case-card__tags">
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
interface DesignCase {
  id: string | number
  title: string
  images: string[]
  style_tags: string[]
  category_tags: string[]
}

interface Props {
  caseData: DesignCase
}

const props = defineProps<Props>()

const emit = defineEmits<{
  click: [id: string | number]
}>()

function handleClick() {
  emit('click', props.caseData.id)
}
</script>

<style scoped>
.case-card {
  border-radius: 12px;
  overflow: hidden;
  background: #ffffff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
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
  color: #ffffff;
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
  padding: 12px;
}

.case-card__tag {
  font-size: 20rpx;
  padding: 4px 10px;
  border-radius: 50px;
  margin-right: 8px;
  margin-bottom: 6px;
  line-height: 1.4;
}

.case-card__tag--style {
  background: #FFF8F0;
  color: #FF7B7B;
}

.case-card__tag--category {
  background: #f0f9ff;
  color: #7EC8E3;
}
</style>
