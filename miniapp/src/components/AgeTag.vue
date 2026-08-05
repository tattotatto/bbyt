<template>
  <text :class="['age-tag', `age-tag--${size}`]">{{ range }}</text>
</template>

<script setup lang="ts">
interface Props {
  range: string
  size?: 'small' | 'medium'
}

withDefaults(defineProps<Props>(), {
  size: 'small'
})
</script>

<style scoped>
.age-tag {
  display: inline-block;
  background: #E8F4FD;
  color: #3A8FB7;
  border: 1px solid #C5E3F6;
  border-radius: 8px;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
  line-height: 1.4;
}

.age-tag--small {
  font-size: 20rpx;
  padding: 2px 8px;
}

.age-tag--medium {
  font-size: 24rpx;
  padding: 4px 12px;
}
</style>
