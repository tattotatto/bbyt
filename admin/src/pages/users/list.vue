<template>
  <div class="user-list-page">
    <h1 class="page-title">用户管理</h1>

    <!-- Status filter tabs -->
    <el-tabs v-model="statusFilter" class="status-tabs" @tab-change="handleStatusChange">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane label="待审核" name="pending_review" />
      <el-tab-pane label="已激活" name="active" />
      <el-tab-pane label="已冻结" name="frozen" />
    </el-tabs>

    <!-- Search bar -->
    <div class="search-bar">
      <el-input
        v-model="keyword"
        placeholder="请输入手机号或公司名"
        clearable
        class="search-input"
        @keyup.enter="handleSearch"
      />
      <el-select v-model="levelFilter" placeholder="全部等级" clearable class="search-select">
        <el-option label="全部" value="" />
        <el-option label="普通" value="normal" />
        <el-option label="白银" value="silver" />
        <el-option label="黄金" value="gold" />
        <el-option label="白金" value="platinum" />
      </el-select>
      <el-button type="primary" @click="handleSearch">搜索</el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>

    <!-- Table -->
    <el-table :data="tableData" v-loading="loading" border stripe class="user-table">
      <el-table-column prop="phone" label="手机号" width="140" />
      <el-table-column prop="company_name" label="公司名" min-width="180">
        <template #default="{ row }">
          {{ row.company_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="contact_person" label="联系人" width="120">
        <template #default="{ row }">
          {{ row.contact_person || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="level" label="等级" width="100" align="center">
        <template #default="{ row }">
          <el-tag :style="getLevelTagStyle(row.level)" size="small">
            {{ levelLabel(row.level) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small">
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="注册时间" width="180" align="center">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" align="center" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'pending_review'"
            type="primary"
            size="small"
            @click="openReviewDialog(row)"
          >
            审核
          </el-button>
          <span v-else class="reviewed-text">已审核</span>
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="handleSearch"
        @current-change="handlePageChange"
      />
    </div>

    <!-- ==================== Review Dialog ==================== -->
    <el-dialog
      v-model="reviewDialogVisible"
      title="零售商审核"
      width="520px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div v-if="currentUser" class="review-info">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="手机号">
            {{ currentUser.phone }}
          </el-descriptions-item>
          <el-descriptions-item label="公司名">
            {{ currentUser.company_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="营业执照号">
            {{ currentUser.business_license || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="联系人">
            {{ currentUser.contact_person || '-' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="review-actions">
        <el-button type="success" @click="handleApprove">审核通过</el-button>
        <el-button type="danger" @click="handleReject">审核拒绝</el-button>
      </div>
    </el-dialog>

    <!-- Approve sub-dialog -->
    <el-dialog
      v-model="approveFormVisible"
      title="审核通过 - 设置信息"
      width="480px"
      :close-on-click-modal="false"
      append-to-body
      destroy-on-close
    >
      <el-form ref="approveFormRef" :model="approveForm" :rules="approveRules" label-width="100px">
        <el-form-item label="设置等级" prop="level">
          <el-select v-model="approveForm.level" placeholder="请选择等级">
            <el-option label="普通" value="normal" />
            <el-option label="白银" value="silver" />
            <el-option label="黄金" value="gold" />
            <el-option label="白金" value="platinum" />
          </el-select>
        </el-form-item>
        <el-form-item label="账期额度(元)" prop="creditLimitYuan">
          <el-input-number
            v-model="approveForm.creditLimitYuan"
            :min="0"
            :precision="2"
            placeholder="0表示不设账期"
            class="credit-input"
          />
          <span class="form-tip">0表示不设账期</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="approveFormVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmApprove">确认通过</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { getUserList, reviewUser } from '@/api/users'
import type { UserItem, UserListParams, ReviewData } from '@/api/users'
import type { PaginatedResult } from '@/api/products'

// ──────────── Reactive state ────────────
const loading = ref(false)

// Filter state
const statusFilter = ref('')
const keyword = ref('')
const levelFilter = ref('')

// Table state
const tableData = ref<UserItem[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// Review dialog state
const reviewDialogVisible = ref(false)
const currentUser = ref<UserItem | null>(null)

// Approve sub-form state
const approveFormVisible = ref(false)
const approveFormRef = ref<FormInstance>()
const approveForm = reactive({
  level: 'normal' as string,
  creditLimitYuan: 0,
})
const approveRules: FormRules = {
  level: [{ required: true, message: '请选择等级', trigger: 'change' }],
}

// ──────────── Helpers ────────────
function levelLabel(level: string): string {
  const map: Record<string, string> = {
    normal: '普通',
    silver: '白银',
    gold: '黄金',
    platinum: '白金',
  }
  return map[level] || level
}

function getLevelTagStyle(level: string): Record<string, string> {
  const styles: Record<string, Record<string, string>> = {
    normal: { backgroundColor: '#e0e0e0', color: '#666', borderColor: '#ccc' },
    silver: { backgroundColor: '#e8f4f8', color: '#7EC8E3', borderColor: '#b3dce8' },
    gold: { backgroundColor: '#FFD93D', color: '#4a3728', borderColor: '#e6c235' },
    platinum: { backgroundColor: '#FF7B7B', color: '#fff', borderColor: '#e66a6a' },
  }
  return styles[level] || {}
}

function statusTagType(status: string): 'warning' | 'success' | 'danger' | 'info' {
  const map: Record<string, 'warning' | 'success' | 'danger' | 'info'> = {
    pending_review: 'warning',
    active: 'success',
    frozen: 'danger',
  }
  return map[status] || 'info'
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending_review: '待审核',
    active: '已激活',
    frozen: '已冻结',
  }
  return map[status] || status
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  const s = String(d.getSeconds()).padStart(2, '0')
  return `${y}-${m}-${day} ${h}:${min}:${s}`
}

// ──────────── Data fetching ────────────
async function fetchList() {
  loading.value = true
  try {
    const params: UserListParams = {
      page: currentPage.value,
      page_size: pageSize.value,
      role: 'retailer',
    }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    if (keyword.value) {
      params.keyword = keyword.value
    }
    if (levelFilter.value) {
      params.level = levelFilter.value
    }

    const res = await getUserList(params)
    tableData.value = res.items || []
    total.value = res.total || 0
  } catch {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// ──────────── Event handlers ────────────
function handleStatusChange() {
  currentPage.value = 1
  fetchList()
}

function handleSearch() {
  currentPage.value = 1
  fetchList()
}

function handleReset() {
  keyword.value = ''
  levelFilter.value = ''
  statusFilter.value = ''
  currentPage.value = 1
  fetchList()
}

function handlePageChange() {
  fetchList()
}

// ──────────── Review logic ────────────
function openReviewDialog(user: UserItem) {
  currentUser.value = user
  reviewDialogVisible.value = true
}

function handleApprove() {
  if (!currentUser.value) return

  ElMessageBox.confirm(
    `确认通过用户 ${currentUser.value.phone} 的审核吗？`,
    '审核确认',
    { confirmButtonText: '确认通过', cancelButtonText: '取消', type: 'warning' }
  )
    .then(() => {
      reviewDialogVisible.value = false
      approveForm.level = 'normal'
      approveForm.creditLimitYuan = 0
      approveFormVisible.value = true
    })
    .catch(() => {
      // user cancelled
    })
}

async function confirmApprove() {
  if (!approveFormRef.value) return

  await approveFormRef.value.validate(async (valid) => {
    if (!valid || !currentUser.value) return

    try {
      const creditLimitInCents = Math.round(approveForm.creditLimitYuan * 100)
      await reviewUser(currentUser.value.id, {
        action: 'approve',
        level: approveForm.level,
        credit_limit: creditLimitInCents,
      } as ReviewData)
      ElMessage.success('审核通过')
      approveFormVisible.value = false
      reviewDialogVisible.value = false
      fetchList()
    } catch {
      ElMessage.error('审核操作失败')
    }
  })
}

function handleReject() {
  if (!currentUser.value) return

  ElMessageBox.confirm(
    `确认拒绝用户 ${currentUser.value.phone} 的审核吗？此操作不可撤销。`,
    '拒绝确认',
    { confirmButtonText: '确认拒绝', cancelButtonText: '取消', type: 'error' }
  )
    .then(async () => {
      try {
        await reviewUser(currentUser.value!.id, {
          action: 'reject',
        } as ReviewData)
        ElMessage.success('已拒绝该用户')
        reviewDialogVisible.value = false
        fetchList()
      } catch {
        ElMessage.error('审核操作失败')
      }
    })
    .catch(() => {
      // user cancelled
    })
}

// ──────────── Lifecycle ────────────
onMounted(() => {
  fetchList()
})
</script>

<style lang="scss" scoped>
.user-list-page {
  padding: 24px;
  background-color: var(--color-bg, #FFF8F0);
  min-height: 100%;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text, #4a3728);
  margin: 0 0 20px 0;
}

.status-tabs {
  background: #fff;
  border-radius: 8px;
  padding: 0 20px;
  margin-bottom: 16px;

  :deep(.el-tabs__header) {
    margin-bottom: 0;
  }

  :deep(.el-tabs__item.is-active) {
    color: var(--color-primary, #FF7B7B);
  }

  :deep(.el-tabs__active-bar) {
    background-color: var(--color-primary, #FF7B7B);
  }
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 16px 20px;
  background: #fff;
  border-radius: 8px;

  .search-input {
    width: 240px;
  }

  .search-select {
    width: 140px;
  }

  .el-button--primary {
    background-color: var(--color-primary, #FF7B7B);
    border-color: var(--color-primary, #FF7B7B);

    &:hover {
      background-color: #e66a6a;
      border-color: #e66a6a;
    }
  }
}

.user-table {
  background: #fff;
  border-radius: 8px;
}

.reviewed-text {
  color: var(--color-text-secondary, #7a6a5a);
  font-size: 13px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding: 12px 20px;
  background: #fff;
  border-radius: 8px;
}

// ── Review dialog ──
.review-info {
  margin-bottom: 20px;
}

.review-actions {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding-top: 8px;
}

// ── Approve sub-form ──
.credit-input {
  width: 100%;
}

.form-tip {
  margin-left: 8px;
  font-size: 12px;
  color: var(--color-text-secondary, #7a6a5a);
}
</style>
