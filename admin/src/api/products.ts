// api/products.ts — 商品管理 API + 文件上传
import request from './request'

// ===== 品类 =====
export interface Category {
  id: string
  name: string
  parent_id: string | null
  icon: string
  sort_order: number
  status: string
  children?: Category[]
}

export function getCategories(): Promise<Category[]> {
  return request.get('/products/categories').then((res) => res.data)
}

export function createCategory(data: { name: string; parent_id?: string; icon?: string; sort_order?: number }): Promise<Category> {
  return request.post('/products/categories', data).then((res) => res.data)
}

// ===== 定价 =====
export interface PricingTier {
  qty: number
  price: number  // 单位：元（前后端传输时转为分）
}

export interface PricingRules {
  normal: PricingTier[]
  silver: PricingTier[]
  gold: PricingTier[]
  platinum: PricingTier[]
}

// ===== 商品 =====
export interface ProductForm {
  name: string
  category_id: string
  description: string
  images: string[]
  age_range: string
  safety_certifications: { name: string; icon?: string }[]
  stock: number
  min_order_qty: number
  is_virtual: boolean
  virtual_detail?: Record<string, any>
}

export interface ProductItem {
  id: string
  name: string
  category: Category
  images: string[]
  age_range: string
  stock: number
  min_order_qty: number
  status: string
  pricing_rules: PricingRules | null
  is_virtual: boolean
  description: string
  safety_certifications: { name: string; icon?: string }[]
  virtual_detail?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface ProductListParams {
  page?: number
  page_size?: number
  keyword?: string
  category_id?: string
  status?: string
  age_range?: string
}

export interface PaginatedResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export function getProductList(params: ProductListParams): Promise<PaginatedResult<ProductItem>> {
  return request.get('/products/', { params }).then((res) => res.data)
}

export function createProduct(data: ProductForm): Promise<ProductItem> {
  // 将前端价格（元）转为后端（分）
  return request.post('/products/', data).then((res) => res.data)
}

export function updateProduct(id: string, data: Partial<ProductForm>): Promise<ProductItem> {
  return request.put(`/products/${id}`, data).then((res) => res.data)
}

export function setPricing(id: string, pricingRules: PricingRules): Promise<any> {
  // 将价格从元转为分发送
  const rulesInCents: any = {}
  for (const [level, tiers] of Object.entries(pricingRules)) {
    rulesInCents[level] = tiers.map((t: PricingTier) => ({ qty: t.qty, price: Math.round(t.price * 100) }))
  }
  return request.put(`/products/${id}/pricing`, rulesInCents).then((res) => res.data)
}

export function setProductStatus(id: string, statusAction: 'on_sale' | 'off_sale'): Promise<any> {
  return request.put(`/products/${id}/status`, null, { params: { status_action: statusAction } }).then((res) => res.data)
}

// ===== 文件上传 =====
export function uploadFile(file: File): Promise<{ url: string }> {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((res) => res.data)
}
