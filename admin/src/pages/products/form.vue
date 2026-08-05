<template>
  <div class="product-form-page">
    <!-- 页面标题 -->
    <h1 class="page-title">{{ isEdit ? '编辑商品' : '新增商品' }}</h1>

    <el-card class="form-card">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="110px"
        label-position="left"
      >
        <!-- ========== 基本信息 ========== -->
        <h3 class="section-title">基本信息</h3>

        <el-form-item label="商品名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入商品名称"
            maxlength="60"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="品类" prop="category_id">
          <el-select
            v-model="form.category_id"
            placeholder="请选择品类"
            style="width: 100%"
          >
            <el-option
              v-for="cat in flatCategories"
              :key="cat.id"
              :label="cat.displayName"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请输入商品描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-divider />

        <!-- ========== 商品图片 ========== -->
        <h3 class="section-title">商品图片</h3>

        <el-form-item label="上传图片">
          <div class="upload-section">
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :http-request="handleUpload"
              :show-file-list="false"
              accept="image/*"
              multiple
              drag
              action=""
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                将图片拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持多图上传，建议尺寸 800x800，每张不超过10MB
                </div>
              </template>
            </el-upload>

            <!-- 已上传图片列表 -->
            <div v-if="form.images.length > 0" class="image-preview-list">
              <div
                v-for="(img, index) in form.images"
                :key="index"
                class="image-preview-item"
              >
                <el-image
                  :src="img"
                  fit="cover"
                  style="width: 100px; height: 100px; border-radius: 8px"
                  :preview-src-list="form.images"
                  :initial-index="index"
                />
                <div class="image-actions">
                  <el-button
                    v-if="index > 0"
                    circle
                    size="small"
                    @click="moveImageUp(index)"
                  >
                    <el-icon><ArrowUp /></el-icon>
                  </el-button>
                  <el-button
                    v-if="index < form.images.length - 1"
                    circle
                    size="small"
                    @click="moveImageDown(index)"
                  >
                    <el-icon><ArrowDown /></el-icon>
                  </el-button>
                  <el-button
                    circle
                    size="small"
                    type="danger"
                    @click="removeImage(index)"
                  >
                    <el-icon><Close /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-form-item>

        <el-divider />

        <!-- ========== 规格信息 ========== -->
        <h3 class="section-title">规格信息</h3>

        <el-form-item label="适龄段" prop="age_range">
          <el-select
            v-model="form.age_range"
            placeholder="请选择适龄段"
            style="width: 100%"
          >
            <el-option label="0-3岁" value="0-3岁" />
            <el-option label="3-6岁" value="3-6岁" />
            <el-option label="6岁+" value="6岁+" />
          </el-select>
        </el-form-item>

        <el-form-item label="安全认证">
          <div class="cert-list">
            <div
              v-for="(cert, index) in form.safety_certifications"
              :key="index"
              class="cert-item"
            >
              <el-input
                v-model="cert.name"
                placeholder="认证名称，如：CE认证、3C认证"
                style="flex: 1"
              />
              <el-button
                type="danger"
                :icon="Delete"
                circle
                plain
                @click="removeCert(index)"
              />
            </div>
            <el-button type="primary" plain @click="addCert">
              <el-icon><Plus /></el-icon>
              添加认证
            </el-button>
          </div>
        </el-form-item>

        <el-divider />

        <!-- ========== 库存信息 ========== -->
        <h3 class="section-title">库存信息</h3>

        <el-form-item label="库存数量" prop="stock">
          <el-input-number
            v-model="form.stock"
            :min="0"
            :step="1"
            controls-position="right"
            style="width: 220px"
          />
        </el-form-item>

        <el-form-item label="最低起批量" prop="min_order_qty">
          <el-input-number
            v-model="form.min_order_qty"
            :min="1"
            :step="1"
            controls-position="right"
            style="width: 220px"
          />
        </el-form-item>

        <el-divider />

        <!-- ========== 定价规则 ========== -->
        <h3 class="section-title">定价规则</h3>
        <p class="section-explain">为每个会员等级设置阶梯定价规则</p>

        <el-form-item label="">
          <el-tabs v-model="activePricingTab" class="pricing-tabs">
            <el-tab-pane label="普通会员" name="normal">
              <PricingTable
                :tiers="pricing.normal"
                @add="addPricingTier('normal')"
                @remove="removePricingTier('normal', $event)"
              />
            </el-tab-pane>
            <el-tab-pane label="白银会员" name="silver">
              <PricingTable
                :tiers="pricing.silver"
                @add="addPricingTier('silver')"
                @remove="removePricingTier('silver', $event)"
              />
            </el-tab-pane>
            <el-tab-pane label="黄金会员" name="gold">
              <PricingTable
                :tiers="pricing.gold"
                @add="addPricingTier('gold')"
                @remove="removePricingTier('gold', $event)"
              />
            </el-tab-pane>
            <el-tab-pane label="白金会员" name="platinum">
              <PricingTable
                :tiers="pricing.platinum"
                @add="addPricingTier('platinum')"
                @remove="removePricingTier('platinum', $event)"
              />
            </el-tab-pane>
          </el-tabs>
        </el-form-item>

        <el-divider />

        <!-- ========== 虚拟商品 ========== -->
        <h3 class="section-title">虚拟商品</h3>

        <el-form-item label="虚拟商品">
          <el-switch
            v-model="form.is_virtual"
            active-text="虚拟商品（店面设计服务）"
          />
        </el-form-item>

        <template v-if="form.is_virtual">
          <el-form-item label="服务详情">
            <el-input
              v-model="form.virtual_detail.serviceDesc"
              type="textarea"
              :rows="3"
              placeholder="请描述店面设计服务的具体内容"
            />
          </el-form-item>

          <el-form-item label="适用面积">
            <el-select
              v-model="form.virtual_detail.area"
              placeholder="请选择适用面积"
              style="width: 100%"
            >
              <el-option label="50㎡以下" value="50㎡以下" />
              <el-option label="50-100㎡" value="50-100㎡" />
              <el-option label="100-200㎡" value="100-200㎡" />
              <el-option label="200㎡以上" value="200㎡以上" />
            </el-select>
          </el-form-item>

          <el-form-item label="风格偏好">
            <el-select
              v-model="form.virtual_detail.styles"
              placeholder="请选择风格偏好（可多选）"
              style="width: 100%"
              multiple
            >
              <el-option label="ins风" value="ins风" />
              <el-option label="自然原木" value="自然原木" />
              <el-option label="卡通童趣" value="卡通童趣" />
            </el-select>
          </el-form-item>

          <el-form-item label="预算范围">
            <el-select
              v-model="form.virtual_detail.budget"
              placeholder="请选择预算范围"
              style="width: 100%"
            >
              <el-option label="5000以下" value="5000以下" />
              <el-option label="5000-10000" value="5000-10000" />
              <el-option label="10000-20000" value="10000-20000" />
              <el-option label="20000以上" value="20000以上" />
            </el-select>
          </el-form-item>
        </template>

        <el-divider />

        <!-- ========== 提交按钮 ========== -->
        <el-form-item>
          <el-button
            type="default"
            @click="$router.push('/products')"
          >
            取消
          </el-button>
          <el-button
            type="primary"
            :loading="submitting"
            @click="handleSubmit"
          >
            保存
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// ============================================================
//  PricingTable — 阶梯定价子组件 (render-function, inline)
// ============================================================
import { h, reactive, ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  UploadFilled,
  ArrowUp,
  ArrowDown,
  Close,
  Plus,
  Delete,
} from '@element-plus/icons-vue'
import {
  createProduct,
  updateProduct,
  setPricing,
  getCategories,
  uploadFile,
} from '@/api/products'
import type {
  PricingTier,
  PricingRules,
  Category,
  ProductItem,
} from '@/api/products'
import request from '@/api/request'

// ---- PricingTable (inline component via h() render) ----
const PricingTable = {
  name: 'PricingTable',
  props: {
    tiers: { type: Array as () => PricingTier[], required: true },
  },
  emits: ['add', 'remove'],
  setup(props: any, { emit }: any) {
    return () =>
      h('div', [
        h(
          'el-table',
          { data: props.tiers, border: true, style: { width: '100%' } },
          [
            h(
              'el-table-column',
              { label: '起购数量', width: '180' },
              {
                default: ({ row }: any) =>
                  h('el-input-number', {
                    modelValue: row.qty,
                    'onUpdate:modelValue': (v: number) => (row.qty = v),
                    min: 1,
                    controlsPosition: 'right',
                    style: { width: '140px' },
                    placeholder: '起购数量',
                  }),
              },
            ),
            h(
              'el-table-column',
              { label: '单价（元）', width: '180' },
              {
                default: ({ row }: any) =>
                  h('el-input-number', {
                    modelValue: row.price,
                    'onUpdate:modelValue': (v: number) => (row.price = v),
                    min: 0,
                    precision: 2,
                    step: 0.01,
                    controlsPosition: 'right',
                    style: { width: '140px' },
                    placeholder: '单价',
                  }),
              },
            ),
            h(
              'el-table-column',
              { label: '操作', width: '90' },
              {
                default: ({ $index }: any) =>
                  h(
                    'el-button',
                    {
                      type: 'danger',
                      link: true,
                      onClick: () => emit('remove', $index),
                    },
                    '删除',
                  ),
              },
            ),
          ],
        ),
        h(
          'div',
          { style: { marginTop: '12px' } },
          h(
            'el-button',
            {
              type: 'primary',
              plain: true,
              size: 'small',
              onClick: () => emit('add'),
            },
            { default: () => [h('el-icon', null, () => h(Plus)), ' 添加阶梯'] },
          ),
        ),
      ])
  },
}

// ============================================================
//  主组件
// ============================================================
const route = useRoute()
const router = useRouter()

const isEdit = computed(() => !!route.params.id)
const formRef = ref()
const uploadRef = ref()
const submitting = ref(false)

// ---- 品类列表 ----
const categoryList = ref<Category[]>([])

interface FlatCategory {
  id: string
  displayName: string
}

const flatCategories = computed<FlatCategory[]>(() => {
  const result: FlatCategory[] = []
  function flatten(list: Category[], prefix = '') {
    for (const cat of list) {
      const name = prefix ? `${prefix} / ${cat.name}` : cat.name
      result.push({ id: cat.id, displayName: name })
      if (cat.children && cat.children.length) {
        flatten(cat.children, name)
      }
    }
  }
  flatten(categoryList.value)
  return result
})

async function loadCategories() {
  try {
    categoryList.value = await getCategories()
  } catch {
    // silently fail
  }
}

// ---- 表单数据 ----
const form = reactive({
  name: '',
  category_id: '',
  description: '',
  images: [] as string[],
  age_range: '',
  safety_certifications: [{ name: '' }] as { name: string; icon?: string }[],
  stock: 0,
  min_order_qty: 1,
  is_virtual: false,
  virtual_detail: {
    serviceDesc: '',
    area: '',
    styles: [] as string[],
    budget: '',
  },
})

// ---- 表单校验规则 ----
const rules = {
  name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择品类', trigger: 'change' }],
}

// ---- 定价数据 ----
const pricing = reactive<PricingRules>({
  normal: [] as PricingTier[],
  silver: [] as PricingTier[],
  gold: [] as PricingTier[],
  platinum: [] as PricingTier[],
})

const activePricingTab = ref('normal')

type PricingLevel = keyof PricingRules

function addPricingTier(level: PricingLevel) {
  pricing[level].push({ qty: 1, price: 0 })
}

function removePricingTier(level: PricingLevel, index: number) {
  pricing[level].splice(index, 1)
}

// ---- 安全认证 ----
function addCert() {
  form.safety_certifications.push({ name: '' })
}

function removeCert(index: number) {
  form.safety_certifications.splice(index, 1)
}

// ---- 图片管理 ----
async function handleUpload(options: any) {
  const file = options.file as File
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('图片大小不能超过10MB')
    return
  }
  try {
    const result = await uploadFile(file)
    if (result.url) {
      form.images.push(result.url)
      ElMessage.success('上传成功')
    }
  } catch {
    ElMessage.error('上传失败，请重试')
  }
}

function removeImage(index: number) {
  form.images.splice(index, 1)
}

function moveImageUp(index: number) {
  if (index <= 0) return
  ;[form.images[index - 1], form.images[index]] = [form.images[index], form.images[index - 1]]
}

function moveImageDown(index: number) {
  if (index >= form.images.length - 1) return
  ;[form.images[index], form.images[index + 1]] = [form.images[index + 1], form.images[index]]
}

// ---- 加载编辑数据 ----
async function loadProduct() {
  if (!isEdit.value) return
  try {
    const id = route.params.id as string
    const res: any = await request.get(`/products/${id}`)
    // 响应拦截器将 axios response.data 返回，即 { code, data, message }
    // 产品数据在 res.data 中（拦截器返回的是整个 body，再 .then(res => res.data) 拿到内部 data）
    // 但这里直接 await 拿到的是拦截器返回体 { code, data, message }
    const product: ProductItem = res.data

    // 填充表单
    form.name = product.name
    form.category_id = product.category?.id || ''
    form.description = product.description || ''
    form.images = product.images || []
    form.age_range = product.age_range || ''
    form.safety_certifications =
      product.safety_certifications && product.safety_certifications.length > 0
        ? product.safety_certifications.map((c) => ({ name: c.name, icon: c.icon }))
        : [{ name: '' }]
    form.stock = product.stock ?? 0
    form.min_order_qty = product.min_order_qty ?? 1
    form.is_virtual = product.is_virtual ?? false

    if (product.virtual_detail) {
      form.virtual_detail = {
        serviceDesc: (product.virtual_detail as any).serviceDesc || '',
        area: (product.virtual_detail as any).area || '',
        styles: (product.virtual_detail as any).styles || [],
        budget: (product.virtual_detail as any).budget || '',
      }
    }

    // 填充定价规则（后端以分为单位，转回元）
    if (product.pricing_rules) {
      for (const level of ['normal', 'silver', 'gold', 'platinum'] as PricingLevel[]) {
        const tiers = product.pricing_rules[level]
        if (tiers && Array.isArray(tiers)) {
          pricing[level] = tiers.map((t: PricingTier) => ({
            qty: t.qty,
            price: t.price,
          }))
        }
      }
    }
  } catch {
    ElMessage.error('加载商品信息失败')
    router.push('/products')
  }
}

// ---- 提交 ----
async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    // 组装提交数据
    const productData = {
      name: form.name,
      category_id: form.category_id,
      description: form.description,
      images: form.images,
      age_range: form.age_range,
      safety_certifications: form.safety_certifications.filter((c) => c.name.trim()),
      stock: form.stock,
      min_order_qty: form.min_order_qty,
      is_virtual: form.is_virtual,
      virtual_detail: form.is_virtual ? { ...form.virtual_detail } : undefined,
    }

    let productId: string

    if (isEdit.value) {
      // 编辑模式
      const id = route.params.id as string
      await updateProduct(id, productData)
      productId = id
    } else {
      // 新增模式
      const created = await createProduct(productData)
      productId = created.id
    }

    // 设置定价规则（如果有任何定价数据）
    const hasPricing = Object.values(pricing).some((arr) => arr.length > 0)
    if (hasPricing) {
      await setPricing(productId, pricing)
    }

    ElMessage.success(isEdit.value ? '商品更新成功' : '商品创建成功')
    router.push('/products')
  } catch {
    ElMessage.error('保存失败，请重试')
  } finally {
    submitting.value = false
  }
}

// ---- 生命周期 ----
onMounted(() => {
  loadCategories()
  loadProduct()
})
</script>

<style lang="scss" scoped>
.product-form-page {
  padding: 24px;

  .page-title {
    font-size: 22px;
    font-weight: 600;
    color: var(--color-text);
    margin-bottom: 24px;
  }
}

.form-card {
  max-width: 900px;
  border-radius: var(--radius-md);
  border-color: var(--color-border);
  box-shadow: var(--shadow-card);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 16px;
  padding-left: 12px;
  border-left: 3px solid var(--color-primary);
}

.section-explain {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: -8px 0 16px;
}

// ---- 上传区域 ----
.upload-section {
  width: 100%;
}

.image-preview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
}

.image-preview-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--color-border);

  .image-actions {
    display: flex;
    gap: 4px;
    padding: 6px;
    justify-content: center;
    background: #fff;
  }
}

// ---- 认证列表 ----
.cert-list {
  width: 100%;
}

.cert-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

// ---- 定价标签页 ----
.pricing-tabs {
  width: 100%;
}

// ---- Element Plus 覆盖 ----
:deep(.el-upload-dragger) {
  border-radius: var(--radius-sm);
  border-color: var(--color-border);
  background: var(--color-bg);
}

:deep(.el-divider) {
  margin: 24px 0;
  border-color: var(--color-border);
}

:deep(.el-tabs__item) {
  color: var(--color-text-secondary);
}

:deep(.el-tabs__item.is-active) {
  color: var(--color-primary);
}

:deep(.el-tabs__active-bar) {
  background-color: var(--color-primary);
}
</style>
