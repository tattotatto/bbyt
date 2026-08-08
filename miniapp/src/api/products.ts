import http from './request'

// ── Common types ──────────────────────────────────────────────────────────────
export interface Paginated<T> { items: T[]; total: number; page: number; page_size: number }
export interface Category { id: string; parent_id: string | null; name: string; icon: string | null; sort_order: number; status: string; children: Category[] }
export interface PricingTier { qty: number; price: number }

// ── Product types ─────────────────────────────────────────────────────────────
export interface ProductListItem {
  id: string; name: string; images: string[]; age_range: string | null;
  safety_certifications: unknown[]; is_virtual: boolean; stock: number | null;
  min_order_qty: number; status: string; price_min: number | null; price_max: number | null;
  // @deprecated backward-compat
  description?: string | null; category_name?: string; unit?: string; moq?: number;
  is_hot?: boolean; is_new?: boolean; sales_count?: number; material?: string; brand?: string
}
export interface ProductDetail {
  id: string; category_id: string | null; name: string; images: string[]; description: string | null;
  specs: Record<string, string[]> | { name: string; options: string[] }[] | null; age_range: string | null; safety_certifications: unknown[];
  is_virtual: boolean; virtual_detail: unknown; stock: number | null; min_order_qty: number;
  pricing_rules: Record<string, PricingTier[]>; status: string; category: Category | null;
  created_at: string | null; updated_at: string | null;
  // @deprecated backward-compat
  price_min?: number | null; price_max?: number | null; moq?: number; unit?: string;
  detail_images?: string[]; price_tiers?: PricingTier[]; sales_count?: number;
  related_products?: ProductListItem[]; category_name?: string
}
export interface ProductListParams {
  page?: number; page_size?: number; category_id?: string; age_range?: string; keyword?: string;
  sort?: 'newest' | 'sales_desc' | 'price_asc' | 'price_desc'
}

// Backward-compat alias
export type Product = ProductListItem

// ── API functions ─────────────────────────────────────────────────────────────
export const getProductList = (params?: ProductListParams) => http.get<Paginated<ProductListItem>>('/products', params)
export const getProductDetail = (id: string) => http.get<ProductDetail>(`/products/${id}`)
export const getHotProducts = (limit = 10) => http.get<ProductListItem[]>('/products/hot', { limit })
export const getNewProducts = (limit = 10) => http.get<ProductListItem[]>('/products/new', { limit })
export const getCategories = () => http.get<Category[]>('/products/categories')
