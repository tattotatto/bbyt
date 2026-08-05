<template>
  <div class="case-form-page">
    <!-- Header -->
    <div class="page-header">
      <h1 class="page-title">{{ isEdit ? '编辑案例' : '新增案例' }}</h1>
    </div>

    <el-card class="form-card" shadow="never">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        label-position="right"
      >
        <!-- 标题 -->
        <el-form-item label="标题" prop="title">
          <el-input
            v-model="form.title"
            placeholder="请输入案例标题"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <!-- 描述 -->
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请输入案例描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <!-- 案例图片 -->
        <el-form-item label="案例图片">
          <div class="upload-section">
            <el-upload
              drag
              multiple
              action=""
              :show-file-list="false"
              :http-request="handleUpload"
              accept="image/*"
              class="upload-dragger"
            >
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                拖拽图片到此处或 <em>点击上传</em>
              </div>
            </el-upload>
            <p class="upload-tip">支持多图上传，建议高清案例图</p>

            <!-- Uploaded images -->
            <div v-if="form.images.length > 0" class="image-list">
              <div
                v-for="(img, index) in form.images"
                :key="img"
                class="image-item"
              >
                <el-image
                  :src="img"
                  fit="cover"
                  :preview-src-list="form.images"
                  :initial-index="index"
                  class="image-thumb"
                />
                <span class="image-remove" @click="handleRemoveImage(index)">
                  <el-icon><Close /></el-icon>
                </span>
              </div>
            </div>
          </div>
        </el-form-item>

        <!-- 分类标签 -->
        <el-form-item label="分类标签" prop="category_tags">
          <el-select
            v-model="form.category_tags"
            multiple
            placeholder="请选择分类标签"
            style="width: 100%"
          >
            <el-option label="婴童游泳馆" value="婴童游泳馆" />
            <el-option label="母婴生活馆" value="母婴生活馆" />
            <el-option label="儿童乐园" value="儿童乐园" />
          </el-select>
        </el-form-item>

        <!-- 风格标签 -->
        <el-form-item label="风格标签" prop="style_tags">
          <el-select
            v-model="form.style_tags"
            multiple
            placeholder="请选择风格标签"
            style="width: 100%"
          >
            <el-option label="ins风" value="ins风" />
            <el-option label="自然原木" value="自然原木" />
            <el-option label="卡通童趣" value="卡通童趣" />
          </el-select>
        </el-form-item>

        <!-- 面积范围 -->
        <el-form-item label="面积范围" prop="area_range">
          <el-select
            v-model="form.area_range"
            placeholder="请选择面积范围"
            style="width: 100%"
          >
            <el-option label="50㎡以下" value="50㎡以下" />
            <el-option label="50-100㎡" value="50-100㎡" />
            <el-option label="100-200㎡" value="100-200㎡" />
            <el-option label="200㎡以上" value="200㎡以上" />
          </el-select>
        </el-form-item>

        <!-- 排序权重 -->
        <el-form-item label="排序权重">
          <el-input-number
            v-model="form.sort_order"
            :min="0"
            :max="9999"
            controls-position="right"
          />
          <span class="field-hint">数值越大越靠前</span>
        </el-form-item>

        <!-- 是否精选 -->
        <el-form-item label="是否精选">
          <el-switch
            v-model="form.is_featured"
            active-text="是"
            inactive-text="否"
          />
        </el-form-item>

        <!-- Submit -->
        <el-form-item>
          <el-button
            type="primary"
            :loading="submitting"
            @click="handleSubmit"
          >
            保存
          </el-button>
          <el-button @click="$router.push('/cases')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules, UploadRequestOptions } from 'element-plus'
import { UploadFilled, Close } from '@element-plus/icons-vue'
import { createCase, updateCase, getCaseDetail } from '@/api/cases'
import type { CaseForm } from '@/api/cases'
import { uploadFile } from '@/api/products'

const router = useRouter()
const route = useRoute()

// ---------- Edit / Create ----------
const isEdit = computed(() => !!route.params.id)
const editId = computed(() => (isEdit.value ? String(route.params.id) : undefined))

// ---------- Form ----------
const formRef = ref<FormInstance>()

const form = reactive<CaseForm>({
  title: '',
  description: '',
  images: [],
  category_tags: [],
  style_tags: [],
  area_range: '',
  sort_order: 0,
  is_featured: false
})

const rules: FormRules = {
  title: [
    { required: true, message: '请输入案例标题', trigger: 'blur' },
    { min: 2, max: 100, message: '标题长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入案例描述', trigger: 'blur' },
    { min: 2, max: 500, message: '描述长度在 2 到 500 个字符', trigger: 'blur' }
  ],
  category_tags: [
    { required: true, message: '请至少选择一个分类标签', trigger: 'change' }
  ]
}

const submitting = ref(false)
const loading = ref(false)

// ---------- Image Upload ----------
async function handleUpload(options: UploadRequestOptions) {
  try {
    const res = await uploadFile(options.file)
    // Handle possible response shapes: { url }, { data: { url } }, or direct string
    const url: string = typeof res === 'string' ? res : (res.url || '')
    if (url) {
      form.images.push(url)
      ElMessage.success('图片上传成功')
    } else {
      ElMessage.error('未能获取图片地址')
    }
  } catch {
    ElMessage.error('图片上传失败')
  }
}

function handleRemoveImage(index: number) {
  form.images.splice(index, 1)
}

// ---------- Submit ----------
async function handleSubmit() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    ElMessage.warning('请完善必填字段')
    return
  }

  submitting.value = true
  try {
    const payload = { ...form }

    if (isEdit.value && editId.value !== undefined) {
      await updateCase(editId.value, payload)
      ElMessage.success('案例更新成功')
    } else {
      await createCase(payload)
      ElMessage.success('案例创建成功')
    }

    router.push('/cases')
  } catch {
    ElMessage.error(isEdit.value ? '案例更新失败' : '案例创建失败')
  } finally {
    submitting.value = false
  }
}

// ---------- Load existing case for edit ----------
async function fetchDetail() {
  if (!editId.value) return

  loading.value = true
  try {
    const data = await getCaseDetail(editId.value)
    form.title = data.title ?? ''
    form.description = data.description ?? ''
    form.images = data.images ?? []
    form.category_tags = data.category_tags ?? []
    form.style_tags = data.style_tags ?? []
    form.area_range = data.area_range ?? ''
    form.sort_order = data.sort_order ?? 0
    form.is_featured = data.is_featured ?? false
  } catch {
    ElMessage.error('获取案例详情失败')
    router.push('/cases')
  } finally {
    loading.value = false
  }
}

// ---------- Lifecycle ----------
onMounted(() => {
  if (isEdit.value) {
    fetchDetail()
  }
})
</script>

<style lang="scss" scoped>
.case-form-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;

  .page-title {
    font-size: 22px;
    font-weight: 600;
    color: var(--color-text, #4a3728);
    margin: 0;
  }
}

.form-card {
  max-width: 800px;
  background: var(--color-bg, #FFF8F0);

  :deep(.el-card__body) {
    padding: 24px 32px;
  }
}

// Upload
.upload-section {
  width: 100%;
}

.upload-dragger {
  :deep(.el-upload-dragger) {
    background: #fff;
    border: 2px dashed var(--color-primary, #FF7B7B);
    border-radius: 8px;

    &:hover {
      border-color: var(--color-primary, #FF7B7B);
      background: var(--color-primary-light, #FFF0ED);
    }
  }
}

.upload-icon {
  font-size: 42px;
  color: var(--color-primary, #FF7B7B);
  margin-bottom: 8px;
}

.upload-tip {
  margin: 8px 0 4px;
  font-size: 12px;
  color: var(--color-text-secondary, #7a6a5a);
}

// Image thumbnails
.image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 12px;
}

.image-item {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #e8e8e8;
  flex-shrink: 0;

  .image-thumb {
    width: 100%;
    height: 100%;
    display: block;
  }

  .image-remove {
    position: absolute;
    top: 2px;
    right: 2px;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.55);
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 12px;
    transition: background 0.2s;

    &:hover {
      background: var(--color-primary, #FF7B7B);
    }
  }
}

// Hint text
.field-hint {
  margin-left: 10px;
  font-size: 12px;
  color: var(--color-text-secondary, #7a6a5a);
}

// Override primary button to coral
:deep(.el-button--primary) {
  --el-button-bg-color: var(--color-primary, #FF7B7B);
  --el-button-border-color: var(--color-primary, #FF7B7B);
  --el-button-hover-bg-color: #ff9595;
  --el-button-hover-border-color: #ff9595;
  --el-button-active-bg-color: #e66a6a;
  --el-button-active-border-color: #e66a6a;
}

// Subtle empty selections
:deep(.el-select .el-tag) {
  margin: 2px 4px 2px 0;
}
</style>
