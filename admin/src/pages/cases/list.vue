<template>
  <div class="case-list-page">
    <!-- Header -->
    <div class="page-header">
      <h1 class="page-title">案例管理</h1>
      <el-button type="primary" @click="$router.push('/cases/create')">
        新增案例
      </el-button>
    </div>

    <!-- Search Bar -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" inline>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="搜索标题"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="分类标签">
          <el-select
            v-model="searchForm.category_tag"
            placeholder="全部分类"
            clearable
          >
            <el-option label="婴童游泳馆" value="婴童游泳馆" />
            <el-option label="母婴生活馆" value="母婴生活馆" />
            <el-option label="儿童乐园" value="儿童乐园" />
          </el-select>
        </el-form-item>
        <el-form-item label="风格标签">
          <el-select
            v-model="searchForm.style_tag"
            placeholder="全部风格"
            clearable
          >
            <el-option label="ins风" value="ins风" />
            <el-option label="自然原木" value="自然原木" />
            <el-option label="卡通童趣" value="卡通童趣" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Table -->
    <el-card class="table-card" shadow="never">
      <el-table
        :data="tableData"
        v-loading="loading"
        border
        stripe
      >
        <el-table-column label="图片" width="100" align="center">
          <template #default="{ row }">
            <el-image
              v-if="row.images && row.images.length"
              :src="row.images[0]"
              :preview-src-list="row.images"
              fit="cover"
              class="thumbnail-img"
            />
            <span v-else class="no-image">-</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="title"
          label="标题"
          min-width="180"
          show-overflow-tooltip
        />
        <el-table-column label="分类标签" width="220">
          <template #default="{ row }">
            <el-tag
              v-for="tag in row.category_tags"
              :key="tag"
              size="small"
              class="category-tag"
            >
              {{ tag }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风格标签" width="220">
          <template #default="{ row }">
            <el-tag
              v-for="tag in row.style_tags"
              :key="tag"
              size="small"
              class="style-tag"
            >
              {{ tag }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="area_range" label="面积" width="120" />
        <el-table-column label="精选" width="80" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.is_featured ? 'success' : 'info'"
              size="small"
            >
              {{ row.is_featured ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              size="small"
              @click="$router.push(`/cases/${row.id}/edit`)"
            >
              编辑
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Empty state -->
      <div v-if="!loading && tableData.length === 0" class="empty-state">
        <el-empty description="暂无案例数据" />
      </div>

      <!-- Pagination -->
      <div v-if="pagination.total > 0" class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="fetchList"
          @current-change="fetchList"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCaseList, deleteCase } from '@/api/cases'
import type { CaseItem, CaseListParams } from '@/api/cases'
import type { PaginatedResult } from '@/api/products'

const router = useRouter()

// ---------- Search ----------
const searchForm = reactive<CaseListParams>({
  keyword: '',
  category_tag: '',
  style_tag: ''
})

// ---------- Table ----------
const tableData = ref<CaseItem[]>([])
const loading = ref(false)

const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

// ---------- Methods ----------
async function fetchList() {
  loading.value = true
  try {
    const params: CaseListParams = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    if (searchForm.keyword) params.keyword = searchForm.keyword
    if (searchForm.category_tag) params.category_tag = searchForm.category_tag
    if (searchForm.style_tag) params.style_tag = searchForm.style_tag

    const res: PaginatedResult<CaseItem> = await getCaseList(params)
    tableData.value = res.items ?? []
    pagination.total = res.total ?? 0
  } catch {
    ElMessage.error('获取案例列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

function handleReset() {
  searchForm.keyword = ''
  searchForm.category_tag = ''
  searchForm.style_tag = ''
  pagination.page = 1
  fetchList()
}

async function handleDelete(row: CaseItem) {
  try {
    await ElMessageBox.confirm(
      `确认删除案例「${row.title}」吗？删除后不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    // user cancelled
    return
  }

  try {
    await deleteCase(row.id)
    ElMessage.success('删除成功')
    // If the current page is now empty and not the first page, go back one page
    if (tableData.value.length === 1 && pagination.page > 1) {
      pagination.page--
    }
    fetchList()
  } catch {
    ElMessage.error('删除失败')
  }
}

// ---------- Lifecycle ----------
onMounted(() => {
  fetchList()
})
</script>

<style lang="scss" scoped>
.case-list-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .page-title {
    font-size: 22px;
    font-weight: 600;
    color: var(--color-text, #4a3728);
    margin: 0;
  }
}

.search-card {
  margin-bottom: 16px;
  background: var(--color-bg, #FFF8F0);

  :deep(.el-card__body) {
    padding: 16px 20px 0;
  }

  :deep(.el-form-item) {
    margin-bottom: 16px;
  }
}

.table-card {
  background: var(--color-bg, #FFF8F0);
}

.thumbnail-img {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  display: block;
}

.no-image {
  color: var(--color-text-secondary, #7a6a5a);
  font-size: 12px;
}

// Coral category tags
.category-tag {
  margin: 2px 4px 2px 0;
  background-color: var(--color-primary-light, #FFF0ED) !important;
  color: var(--color-primary, #FF7B7B) !important;
  border-color: var(--color-primary, #FF7B7B) !important;
}

// Sky-blue style tags
.style-tag {
  margin: 2px 4px 2px 0;
  background-color: #e6f4ff !important;
  color: #1890ff !important;
  border-color: #91caff !important;
}

.empty-state {
  padding: 60px 0;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  padding-top: 16px;
}
</style>
