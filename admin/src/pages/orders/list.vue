<template>
  <div class="orders-page">
    <h1 class="page-title">订单管理</h1>

    <!-- Status Filter Tabs -->
    <el-tabs v-model="activeTab" class="status-tabs" @tab-change="handleTabChange">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane label="待支付" name="pending_payment" />
      <el-tab-pane label="已支付" name="paid" />
      <el-tab-pane label="已发货" name="shipped" />
      <el-tab-pane label="已完成" name="completed" />
      <el-tab-pane label="已取消" name="cancelled" />
    </el-tabs>

    <!-- Search Bar -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索订单号"
          clearable
          class="search-input"
          @keyup.enter="handleSearch"
        />
        <el-select
          v-model="searchType"
          placeholder="订单类型"
          clearable
          style="width: 160px"
        >
          <el-option label="全部" value="" />
          <el-option label="实物商品" value="physical_goods" />
          <el-option label="店面设计" value="store_design" />
        </el-select>
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>
    </div>

    <!-- Orders Table -->
    <el-table
      v-loading="loading"
      :data="orderList"
      border
      stripe
      class="orders-table"
    >
      <!-- 订单号 -->
      <el-table-column label="订单号" min-width="180">
        <template #default="{ row }">
          <el-tooltip :content="row.order_no" placement="top" :disabled="row.order_no.length <= 20">
            <span>{{ truncateOrderNo(row.order_no) }}</span>
          </el-tooltip>
        </template>
      </el-table-column>

      <!-- 类型 -->
      <el-table-column label="类型" width="100" align="center">
        <template #default="{ row }">
          <el-tag
            :type="row.type === 'physical_goods' ? 'primary' : 'success'"
            size="small"
          >
            {{ row.type === 'physical_goods' ? '实物商品' : '店面设计' }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 商品 -->
      <el-table-column label="商品" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <span v-if="row.items && row.items.length > 0">
            {{ row.items[0]?.name
            }}<template v-if="row.items.length > 1">
              等{{ row.items.length }}件
            </template>
          </span>
          <span v-else>-</span>
        </template>
      </el-table-column>

      <!-- 金额 -->
      <el-table-column label="金额" width="140" align="right">
        <template #default="{ row }">
          <span class="amount">{{ formatAmount(row.total_amount) }}</span>
        </template>
      </el-table-column>

      <!-- 支付方式 -->
      <el-table-column label="支付方式" width="110" align="center">
        <template #default="{ row }">
          <el-tag size="small" :type="paymentMethodTagType(row.payment_method)">
            {{ paymentMethodText(row.payment_method) }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 支付状态 -->
      <el-table-column label="支付状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag size="small" :type="paymentStatusTagType(row.payment_status)">
            {{ paymentStatusText(row.payment_status) }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 订单状态 -->
      <el-table-column label="订单状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag size="small" :type="orderStatusTagType(row.status)">
            {{ orderStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 时间 -->
      <el-table-column label="时间" width="160" align="center">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>

      <!-- 操作 -->
      <el-table-column label="操作" width="100" align="center" fixed="right">
        <template #default="{ row }">
          <el-button
            type="primary"
            link
            size="small"
            @click="goToDetail(row.id)"
          >
            查看详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { getOrderList } from '@/api/orders'
import type { OrderItem, OrderListParams } from '@/api/orders'

const router = useRouter()

// === State ===
const loading = ref(false)
const orderList = ref<OrderItem[]>([])

const activeTab = ref('')
const searchKeyword = ref('')
const searchType = ref('')

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

// === Methods ===

/** Truncate order number to 20 chars for display */
function truncateOrderNo(orderNo: string): string {
  if (orderNo.length > 20) {
    return orderNo.slice(0, 10) + '...' + orderNo.slice(-7)
  }
  return orderNo
}

/** Format cents (分) to yuan (元) display */
function formatAmount(cents: number): string {
  const yuan = cents / 100
  return '¥' + yuan.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

/** Format ISO date string to YYYY-MM-DD HH:mm */
function formatDateTime(dateStr: string): string {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/** Payment method display text */
function paymentMethodText(method: string): string {
  const map: Record<string, string> = {
    wechat_pay: '微信支付',
    bank_transfer: '银行转账',
    credit: '账期',
  }
  return map[method] || method
}

/** Payment method tag type */
function paymentMethodTagType(method: string): string {
  const map: Record<string, string> = {
    wechat_pay: 'success',
    bank_transfer: 'warning',
    credit: 'info',
  }
  return map[method] || 'info'
}

/** Payment status display text */
function paymentStatusText(status: string): string {
  const map: Record<string, string> = {
    pending: '待支付',
    paid: '已支付',
    confirmed: '已确认',
    overdue: '已逾期',
  }
  return map[status] || status
}

/** Payment status tag type */
function paymentStatusTagType(status: string): string {
  const map: Record<string, string> = {
    pending: 'warning',
    paid: 'success',
    confirmed: 'success',
    overdue: 'danger',
  }
  return map[status] || 'info'
}

/** Order status display text */
function orderStatusText(status: string): string {
  const map: Record<string, string> = {
    pending_payment: '待支付',
    paid: '已支付',
    shipped: '已发货',
    confirmed: '已确认',
    completed: '已完成',
    cancelled: '已取消',
  }
  return map[status] || status
}

/** Order status tag type */
function orderStatusTagType(status: string): string {
  const map: Record<string, string> = {
    pending_payment: 'warning',
    paid: '',
    shipped: '',
    confirmed: '',
    completed: 'success',
    cancelled: 'info',
  }
  return map[status] || ''
}

/** Fetch order list from API */
async function fetchOrders() {
  loading.value = true
  try {
    const params: OrderListParams = {
      page: pagination.page,
      page_size: pagination.page_size,
      status: activeTab.value || undefined,
      keyword: searchKeyword.value || undefined,
      type: searchType.value || undefined,
    }
    const res = await getOrderList(params)
    orderList.value = res.items
    pagination.total = res.total
  } catch (error: any) {
    const msg = error?.response?.data?.message || error?.message || '加载订单列表失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

// === Event Handlers ===

function handleTabChange() {
  pagination.page = 1
  fetchOrders()
}

function handleSearch() {
  pagination.page = 1
  fetchOrders()
}

function handlePageChange(page: number) {
  pagination.page = page
  fetchOrders()
}

function handleSizeChange(size: number) {
  pagination.page_size = size
  pagination.page = 1
  fetchOrders()
}

function goToDetail(id: string) {
  router.push(`/orders/${id}`)
}

// === Lifecycle ===
onMounted(() => {
  fetchOrders()
})
</script>

<style scoped lang="scss">
.orders-page {
  padding: 4px 0;
}

.status-tabs {
  margin-bottom: 16px;

  :deep(.el-tabs__header) {
    margin-bottom: 0;
  }

  :deep(.el-tabs__nav-wrap::after) {
    height: 1px;
  }

  :deep(.el-tabs__item.is-active) {
    color: var(--color-primary);
    font-weight: 600;
  }

  :deep(.el-tabs__active-bar) {
    background-color: var(--color-primary);
  }
}

.amount {
  color: var(--color-primary);
  font-weight: 700;
  font-size: 14px;
}

.orders-table {
  margin-top: 4px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
