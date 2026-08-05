import http from './request'

export interface Product {
  id: number
  name: string
  description: string
  images: string[]
  age_range: string       // e.g. "3-6岁"
  category_id: number
  category_name: string
  price_min: number
  price_max: number
  stock: number
  unit: string            // e.g. "件", "套", "箱"
  moq: number             // minimum order quantity
  safety_certifications: string[]  // e.g. ["3C", "CE"]
  material: string
  brand: string
  is_hot: boolean
  is_new: boolean
  sales_count: number
  created_at: string
}

export interface ProductListParams {
  page?: number
  page_size?: number
  category_id?: number
  age_range?: string
  keyword?: string
  sort?: 'default' | 'price_asc' | 'price_desc' | 'sales_desc' | 'newest'
  min_price?: number
  max_price?: number
}

export interface ProductListResult {
  list: Product[]
  total: number
  page: number
  page_size: number
}

// Price tier (quantity-based pricing)
export interface PriceTier {
  min_qty: number
  max_qty: number
  unit_price: number
}

export interface ProductDetail extends Product {
  detail_images: string[]
  price_tiers: PriceTier[]
  specs: ProductSpec[]
  related_products: Product[]
}

export interface ProductSpec {
  name: string
  options: string[]
}

// Get product list
export function getProductList(params: ProductListParams): Promise<{ data: ProductListResult }> {
  return http.get<ProductListResult>('/products', params)
}

// Get product detail
export function getProductDetail(id: number): Promise<{ data: ProductDetail }> {
  return http.get<ProductDetail>(`/products/${id}`)
}

// Get hot products
export function getHotProducts(limit?: number): Promise<{ data: Product[] }> {
  return http.get<Product[]>('/products/hot', { limit: limit || 10 })
}

// Get new arrivals
export function getNewProducts(limit?: number): Promise<{ data: Product[] }> {
  return http.get<Product[]>('/products/new', { limit: limit || 10 })
}

// Get product categories
export function getCategories(): Promise<{ data: Category[] }> {
  return http.get<Category[]>('/categories')
}

export interface Category {
  id: number
  name: string
  icon: string
  children?: Category[]
}
