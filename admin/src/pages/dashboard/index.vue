<template>
  <div class="dashboard">
    <h2 class="page-title">仪表盘</h2>

    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :lg="6" v-for="card in statCards" :key="card.label">
        <div class="stat-card" @click="router.push(card.route)">
          <div class="stat-card-inner">
            <div class="stat-icon-box" :style="{ background: card.gradient }">
              <el-icon :size="28" color="#fff">
                <component :is="card.icon" />
              </el-icon>
            </div>
            <div class="stat-info">
              <span class="stat-number">{{ card.value }}</span>
              <span class="stat-label">{{ card.label }}</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Goods, Document, User, PictureFilled } from '@element-plus/icons-vue'
import type { Component } from 'vue'
import { getProductList } from '@/api/products'
import { getOrderList } from '@/api/orders'
import { getUserList } from '@/api/users'
import { getCaseList } from '@/api/cases'

const router = useRouter()

interface StatCard {
  icon: Component
  label: string
  value: number
  gradient: string
  route: string
}

const statCards = ref<StatCard[]>([
  {
    icon: shallowRef(Goods),
    label: '商品总数',
    value: 0,
    gradient: 'linear-gradient(135deg, #FF7B7B, #FF9E9E)',
    route: '/products',
  },
  {
    icon: shallowRef(Document),
    label: '订单总数',
    value: 0,
    gradient: 'linear-gradient(135deg, #7EC8E3, #9ED8E8)',
    route: '/orders',
  },
  {
    icon: shallowRef(User),
    label: '待审核用户',
    value: 0,
    gradient: 'linear-gradient(135deg, #A8D8B9, #C0E8CE)',
    route: '/users',
  },
  {
    icon: shallowRef(PictureFilled),
    label: '案例总数',
    value: 0,
    gradient: 'linear-gradient(135deg, #FFD93D, #FFE580)',
    route: '/cases',
  },
])

onMounted(async () => {
  try {
    const [productRes, orderRes, userRes, caseRes] = await Promise.all([
      getProductList({ page: 1, page_size: 1 }),
      getOrderList({ page: 1, page_size: 1 }),
      getUserList({ page: 1, page_size: 1, status: 'pending_review' }),
      getCaseList({ page: 1, page_size: 1 }),
    ])

    statCards.value[0].value = productRes.total
    statCards.value[1].value = orderRes.total
    statCards.value[2].value = userRes.total
    statCards.value[3].value = caseRes.total
  } catch (error: any) {
    const msg = error?.response?.data?.message || error?.message || '数据加载失败'
    ElMessage.error(msg)
  }
})
</script>

<style scoped lang="scss">
.dashboard {
  // container for page-title + cards
}

.stat-card {
  margin-bottom: 20px;
  cursor: pointer;
  background: #fff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  padding: 24px;
  transition: transform 0.3s, box-shadow 0.3s;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
  }
}

.stat-card-inner {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon-box {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-top: 4px;
}
</style>
