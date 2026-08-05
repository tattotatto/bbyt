<template>
  <div class="products-list-page">
    <!-- 页面标题 -->
    <div class="toolbar">
      <h1 class="page-title">商品管理</h1>
      <div class="toolbar-right">
        <el-button type="primary" @click="$router.push('/products/create')">
          <el-icon><Plus /></el-icon>
          新增商品
        </el-button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <el-card class="search-card">
      <div class="search-bar">
        <el-input
          v-model="filters.keyword"
          placeholder="搜索商品名称"
          clearable
          class="search-input"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select
          v-model="filters.category_id"
          placeholder="全部品类"
          clearable
          style="width: 180px"
        >
          <el-option
            v-for="cat in categoryList"
            :key="cat.id"
            :label="cat.name"
            :value="cat.id"
          />
        </el-select>

        <el-select
          v-model="filters.status"
          placeholder="全部状态"
          clearable
          style="width: 140px"
        >
          <el-option label="全部" value="" />
          <el-option label="上架" value="on_sale" />
          <el-option label="下架" value="off_sale" />
        </el-select>

        <el-select
          v-model="filters.age_range"
          placeholder="全部适龄"
          clearable
          style="width: 140px"
        >
          <el-option label="全部" value="" />
          <el-option label="0-3岁" value="0-3岁" />
          <el-option label="3-6岁" value="3-6岁" />
          <el-option label="6岁+" value="6岁+" />
        </el-select>

        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>
    </el-card>

    <!-- 表格 -->
    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        style="width: 100%"
      >
        <el-table-column label="图片" width="100">
          <template #default="{ row }">
            <el-image
              v-if="row.images && row.images.length"
              :src="row.images[0]"
              :preview-src-list="row.images"
              fit="cover"
              style="width: 60px; height: 60px; border-radius: 8px"
            />
            <div
              v-else
              class="image-placeholder"
            >
              <el-icon><PictureFilled /></el-icon>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="name" label="名称" min-width="160" show-overflow-tooltip />

        <el-table-column label="品类" width="120">
          <template #default="{ row }">
            {{ row.category?.name || '-' }}
          </template>
        </el-table-column>

        <el-table-column label="适龄" width="100">
          <template #default="{ row }">
            <el-tag
              :type="ageTagType(row.age_range)"
              effect="light"
            >
              {{ row.age_range || '-' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="stock" label="库存" width="100" align="center" />

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'on_sale' ? 'success' : 'info'"
              effect="light"
            >
              {{ row.status === 'on_sale' ? '上架' : '下架' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              @click="$router.push(`/products/${row.id}/edit`)"
            >
              编辑
            </el-button>
            <el-button
              v-if="row.status === 'on_sale'"
              type="warning"
              link
              @click="handleToggleStatus(row, 'off_sale')"
            >
              下架
            </el-button>
            <el-button
              v-else
              type="success"
              link
              @click="handleToggleStatus(row, 'on_sale')"
            >
              上架
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="loadData"
        @size-change="loadData"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, PictureFilled } from '@element-plus/icons-vue'
import {
  getProductList,
  getCategories,
  setProductStatus,
} from '@/api/products'
import type { ProductItem, Category, ProductListParams } from '@/api/products'

const router = useRouter()

// ===== 状态 =====
const loading = ref(false)
const tableData = ref<ProductItem[]>([])
const categoryList = ref<Category[]>([])

const filters = reactive<{
  keyword: string
  category_id: string
  status: string
  age_range: string
}>({
  keyword: '',
  category_id: '',
  status: '',
  age_range: '',
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

// ===== 方法 =====
function ageTagType(ageRange: string): '' | 'primary' | 'success' | 'warning' | 'info' | 'danger' {
  if (ageRange === '0-3岁') return 'primary'    // sky blue via Element's primary
  if (ageRange === '3-6岁') return 'danger'      // coral (danger is red-ish in Element)
  if (ageRange === '6岁+') return 'success'      // mint (success is green in Element)
  return 'info'
}

async function loadCategories() {
  try {
    categoryList.value = await getCategories()
  } catch {
    // silently fail
  }
}

async function loadData() {
  loading.value = true
  try {
    const params: ProductListParams = {
      page: pagination.page,
      page_size: pagination.page_size,
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.category_id) params.category_id = filters.category_id
    if (filters.status) params.status = filters.status
    if (filters.age_range) params.age_range = filters.age_range

    const result = await getProductList(params)
    tableData.value = result.items
    pagination.total = result.total
  } catch {
    ElMessage.error('加载商品列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  loadData()
}

async function handleToggleStatus(row: ProductItem, action: 'on_sale' | 'off_sale') {
  const label = action === 'on_sale' ? '上架' : '下架'
  try {
    await ElMessageBox.confirm(
      `确定要将「${row.name}」${label}吗？`,
      '操作确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
    await setProductStatus(row.id, action)
    ElMessage.success(`${label}成功`)
    loadData()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(`${label}失败`)
    }
  }
}

// ===== 生命周期 =====
onMounted(() => {
  loadCategories()
  loadData()
})
</script>

<style lang="scss" scoped>
.products-list-page {
  padding: 24px;

  .page-title {
    font-size: 22px;
    font-weight: 600;
    color: var(--color-text);
    margin-bottom: 0;
  }

  .toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
  }
}

.search-card {
  margin-bottom: 20px;

  .search-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;

    .search-input {
      width: 240px;
    }
  }
}

.table-card {
  :deep(.el-card__body) {
    padding-bottom: 8px;
  }
}

.image-placeholder {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  background: var(--color-primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  font-size: 24px;
}
</style>
