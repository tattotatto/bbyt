<template>
  <div class="order-detail-page">
    <!-- Header -->
    <div class="detail-header">
      <div class="header-left">
        <el-button @click="goBack" :icon="ArrowLeft" plain>返回列表</el-button>
        <h1 class="page-title" style="margin-bottom: 0">订单详情</h1>
      </div>
    </div>

    <template v-if="order">
      <!-- Section 1 - 订单基本信息 -->
      <el-card class="detail-card">
        <template #header>
          <span class="card-title">订单基本信息</span>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单编号">
            {{ order.order_no }}
          </el-descriptions-item>
          <el-descriptions-item label="订单类型">
            <el-tag :type="order.type === 'physical_goods' ? 'primary' : 'success'" size="small">
              {{ order.type === 'physical_goods' ? '实物商品' : '店面设计' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="下单时间">
            {{ formatDateTime(order.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDateTime(order.updated_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="零售商">
            {{ order.retailer?.phone }}
            <template v-if="order.retailer?.company_name">
              / {{ order.retailer.company_name }}
            </template>
          </el-descriptions-item>
          <el-descriptions-item label="订单状态">
            <el-tag :type="orderStatusTagType(order.status)" size="small">
              {{ orderStatusText(order.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="支付方式">
            {{ paymentMethodText(order.payment_method) }}
          </el-descriptions-item>
          <el-descriptions-item label="支付状态">
            <el-tag :type="paymentStatusTagType(order.payment_status)" size="small">
              {{ paymentStatusText(order.payment_status) }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-divider />

      <!-- Section 2 - 商品列表 -->
      <el-card class="detail-card">
        <template #header>
          <span class="card-title">商品列表</span>
        </template>
        <el-table :data="order.items" border stripe>
          <el-table-column label="商品名称" min-width="240" show-overflow-tooltip>
            <template #default="{ row: item }">
              {{ item.name }}
            </template>
          </el-table-column>
          <el-table-column label="数量" width="80" align="center">
            <template #default="{ row: item }">
              {{ item.qty }}
            </template>
          </el-table-column>
          <el-table-column label="单价(元)" width="140" align="right">
            <template #default="{ row: item }">
              {{ formatAmount(item.unit_price) }}
            </template>
          </el-table-column>
          <el-table-column label="小计(元)" width="140" align="right">
            <template #default="{ row: item }">
              <span class="amount">{{ formatAmount(item.subtotal) }}</span>
            </template>
          </el-table-column>
        </el-table>
        <div class="order-total">
          合计：<span class="total-amount">{{ formatAmount(order.total_amount) }}</span>
        </div>
      </el-card>

      <el-divider />

      <!-- Section 3 - 支付信息 -->
      <el-card class="detail-card">
        <template #header>
          <span class="card-title">支付信息</span>
        </template>

        <!-- 微信支付已确认 -->
        <div v-if="order.payment_method === 'wechat_pay' && order.payment_status === 'paid'" class="payment-status-row">
          <el-tag type="success" size="large">微信支付已确认</el-tag>
        </div>

        <!-- 银行转账 -->
        <div v-if="order.payment_method === 'bank_transfer'" class="bank-transfer-section">
          <div v-if="order.bank_receipt_url" class="receipt-image-wrapper">
            <p class="receipt-label">银行转账凭证：</p>
            <el-image
              :src="order.bank_receipt_url"
              :preview-src-list="[order.bank_receipt_url]"
              fit="contain"
              style="width: 320px; height: 200px; border-radius: 8px; border: 1px solid var(--color-border)"
              :preview-teleported="true"
              preview
            />
          </div>
          <div class="bank-action-row">
            <template v-if="order.payment_status === 'pending'">
              <el-button
                type="primary"
                :loading="actionLoading"
                @click="handleConfirmReceipt"
              >
                确认收款
              </el-button>
            </template>
            <template v-else-if="order.payment_status === 'paid'">
              <el-tag type="success" size="large">已确认收款</el-tag>
            </template>
          </div>
        </div>

        <!-- 账期 or no receipt info -->
        <div v-if="order.payment_method !== 'wechat_pay' && order.payment_method !== 'bank_transfer'" class="payment-status-row">
          <span class="text-secondary">
            当前支付方式：{{ paymentMethodText(order.payment_method) }}，
            支付状态：{{ paymentStatusText(order.payment_status) }}
          </span>
        </div>
      </el-card>

      <el-divider />

      <!-- Section 4 - 状态操作 -->
      <el-card class="detail-card">
        <template #header>
          <span class="card-title">状态操作</span>
        </template>
        <div class="action-buttons">
          <!-- 确认收款 -->
          <template v-if="order.status === 'pending_payment' || order.status === 'paid'">
            <el-button
              type="primary"
              :loading="actionLoading"
              @click="handleAction('paid', '确认收款')"
            >
              确认收款
            </el-button>
          </template>

          <!-- 标记发货 -->
          <template v-if="order.status === 'paid'">
            <el-button
              type="warning"
              :loading="actionLoading"
              @click="handleAction('shipped', '标记发货')"
            >
              标记发货
            </el-button>
          </template>

          <!-- 确认完成 -->
          <template v-if="order.status === 'shipped'">
            <el-button
              type="success"
              :loading="actionLoading"
              @click="handleAction('completed', '确认完成')"
            >
              确认完成
            </el-button>
          </template>

          <!-- 取消订单 -->
          <template v-if="order.status === 'pending_payment'">
            <el-button
              type="danger"
              :loading="actionLoading"
              @click="handleAction('cancelled', '取消订单')"
            >
              取消订单
            </el-button>
          </template>

          <span v-if="order.status === 'completed' || order.status === 'cancelled'" class="text-secondary">
            该订单已{{ order.status === 'completed' ? '完成' : '取消' }}，无需操作
          </span>
        </div>
      </el-card>

      <!-- Section 5 - 设计服务订单 -->
      <template v-if="order.type === 'store_design' && order.store_design_detail">
        <el-divider />
        <el-card class="detail-card">
          <template #header>
            <span class="card-title">设计服务信息</span>
          </template>

          <el-descriptions :column="2" border style="margin-bottom: 20px">
            <el-descriptions-item v-if="order.store_design_detail.store_area" label="店面面积">
              {{ order.store_design_detail.store_area }}
            </el-descriptions-item>
            <el-descriptions-item v-if="order.store_design_detail.style_preference" label="风格偏好">
              {{ order.store_design_detail.style_preference }}
            </el-descriptions-item>
            <el-descriptions-item v-if="order.store_design_detail.budget_range" label="预算范围">
              {{ order.store_design_detail.budget_range }}
            </el-descriptions-item>

            <!-- 指派设计师 -->
            <el-descriptions-item label="指派设计师" :span="2">
              <template v-if="order.store_design_detail.assigned_designer">
                {{ order.store_design_detail.assigned_designer.name }}
              </template>
              <template v-else>
                <div class="designer-assign-row">
                  <el-select
                    v-model="selectedDesignerId"
                    placeholder="请选择设计师"
                    :loading="designersLoading"
                    style="width: 220px; margin-right: 12px"
                  >
                    <el-option
                      v-for="d in designerList"
                      :key="d.id"
                      :label="d.contact_person || d.phone"
                      :value="d.id"
                    />
                  </el-select>
                  <el-button
                    type="primary"
                    size="small"
                    :disabled="!selectedDesignerId"
                    :loading="assignLoading"
                    @click="handleAssignDesigner"
                  >
                    指派
                  </el-button>
                </div>
              </template>
            </el-descriptions-item>
          </el-descriptions>

          <!-- 设计进度 -->
          <div v-if="order.store_design_detail.delivery_progress" class="design-progress">
            <p class="subsection-label">设计进度</p>
            <el-steps
              :active="progressStepIndex"
              finish-status="success"
              align-center
            >
              <el-step title="简要" description="brief" />
              <el-step title="草稿" description="draft" />
              <el-step title="修订" description="revision" />
              <el-step title="定稿" description="finalized" />
            </el-steps>
          </div>

          <!-- 附件 -->
          <div v-if="order.store_design_detail.attachments && order.store_design_detail.attachments.length > 0" class="attachments-section">
            <p class="subsection-label">附件</p>
            <ul class="attachment-list">
              <li v-for="(url, idx) in order.store_design_detail.attachments" :key="idx">
                <el-link type="primary" :href="url" target="_blank">
                  <el-icon><Link /></el-icon>
                  附件 {{ idx + 1 }}
                </el-link>
              </li>
            </ul>
          </div>
        </el-card>
      </template>
    </template>

    <!-- Loading state -->
    <div v-else-if="loading" class="loading-wrapper">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- Empty / error state -->
    <el-empty v-else description="订单数据加载失败" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Link } from '@element-plus/icons-vue'
import { getOrderDetail, updateOrderStatus, assignDesigner } from '@/api/orders'
import type { OrderItem } from '@/api/orders'
import { getDesigners } from '@/api/users'
import type { UserItem } from '@/api/users'

const route = useRoute()
const router = useRouter()

// === State ===
const loading = ref(false)
const actionLoading = ref(false)
const assignLoading = ref(false)
const designersLoading = ref(false)
const order = ref<OrderItem | null>(null)
const designerList = ref<UserItem[]>([])
const selectedDesignerId = ref('')

// === Computed: delivery progress step index ===
const progressSteps = ['brief', 'draft', 'revision', 'finalized']
const progressStepIndex = computed(() => {
  const current = order.value?.store_design_detail?.delivery_progress
  if (!current) return -1
  const idx = progressSteps.indexOf(current)
  return idx >= 0 ? idx : -1
})

// === Methods ===

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

// === Actions ===

function goBack() {
  router.push('/orders')
}

async function fetchOrder() {
  const id = route.params.id as string
  if (!id) {
    ElMessage.error('订单 ID 无效')
    return
  }
  loading.value = true
  try {
    order.value = await getOrderDetail(id)
  } catch (error: any) {
    const msg = error?.response?.data?.message || error?.message || '加载订单详情失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

async function fetchDesigners() {
  designersLoading.value = true
  try {
    designerList.value = await getDesigners()
  } catch (error: any) {
    const msg = error?.response?.data?.message || error?.message || '加载设计师列表失败'
    ElMessage.error(msg)
  } finally {
    designersLoading.value = false
  }
}

/** Handle confirm receipt (bank transfer) */
async function handleConfirmReceipt() {
  if (!order.value) return
  try {
    await ElMessageBox.confirm('确认已收到该笔银行转账款项？', '确认收款', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'info',
    })
  } catch {
    return
  }

  actionLoading.value = true
  try {
    await updateOrderStatus(order.value.id, 'paid')
    ElMessage.success('已确认收款')
    await fetchOrder()
  } catch (error: any) {
    const msg = error?.response?.data?.message || error?.message || '操作失败'
    ElMessage.error(msg)
  } finally {
    actionLoading.value = false
  }
}

/** Handle status action with confirm dialog */
async function handleAction(status: string, actionName: string) {
  if (!order.value) return
  try {
    await ElMessageBox.confirm(`确认执行「${actionName}」操作？`, '操作确认', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: status === 'cancelled' ? 'error' : 'warning',
    })
  } catch {
    return
  }

  actionLoading.value = true
  try {
    await updateOrderStatus(order.value.id, status)
    ElMessage.success(`${actionName}成功`)
    await fetchOrder()
  } catch (error: any) {
    const msg = error?.response?.data?.message || error?.message || '操作失败'
    ElMessage.error(msg)
  } finally {
    actionLoading.value = false
  }
}

/** Assign designer */
async function handleAssignDesigner() {
  if (!order.value || !selectedDesignerId.value) return

  assignLoading.value = true
  try {
    await assignDesigner(order.value.id, selectedDesignerId.value)
    ElMessage.success('设计师指派成功')
    selectedDesignerId.value = ''
    await fetchOrder()
  } catch (error: any) {
    const msg = error?.response?.data?.message || error?.message || '指派失败'
    ElMessage.error(msg)
  } finally {
    assignLoading.value = false
  }
}

// === Lifecycle ===
onMounted(() => {
  fetchOrder()
  fetchDesigners()
})
</script>

<style scoped lang="scss">
.order-detail-page {
  padding: 4px 0;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.detail-card {
  margin-bottom: 0;

  :deep(.el-card__header) {
    padding: 14px 20px;
    background: var(--color-primary-light);
    border-bottom: 1px solid var(--color-border);
  }
}

.order-total {
  text-align: right;
  margin-top: 16px;
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text);

  .total-amount {
    color: var(--color-primary);
    font-weight: 700;
    font-size: 18px;
  }
}

.amount {
  color: var(--color-primary);
  font-weight: 600;
}

.payment-status-row {
  padding: 8px 0;
}

.text-secondary {
  color: var(--color-text-secondary);
  font-size: 14px;
}

.bank-transfer-section {
  .receipt-image-wrapper {
    margin-bottom: 16px;
  }

  .receipt-label {
    margin-bottom: 8px;
    color: var(--color-text-secondary);
    font-size: 14px;
  }

  .bank-action-row {
    padding: 8px 0;
  }
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.designer-assign-row {
  display: flex;
  align-items: center;
}

.design-progress {
  margin-bottom: 20px;
}

.subsection-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
  margin-bottom: 12px;
}

.attachments-section {
  .attachment-list {
    list-style: none;
    padding: 0;

    li {
      margin-bottom: 8px;
    }
  }
}

.loading-wrapper {
  padding: 40px;
  background: #fff;
  border-radius: var(--radius-md);
}
</style>
