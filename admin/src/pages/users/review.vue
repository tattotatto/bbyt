<template>
  <div class="review-page">
    <el-result icon="info" title="审核功能" sub-title="请从用户列表页面进行审核操作">
      <template #extra>
        <el-button type="primary" @click="$router.push('/users')">返回用户列表</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
// Review operations are handled inline in list.vue via el-dialog.
// This page exists as a route target and redirects users to the list.
</script>

<style lang="scss" scoped>
.review-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 40px;
  background-color: var(--color-bg, #FFF8F0);
}
</style>
