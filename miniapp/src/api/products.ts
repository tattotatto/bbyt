import http from './request'
import type { Paginated, Category, PricingTier } from './types'

// ── Re-export common types ────────────────────────────────────────────────────
export type { Paginated, Category, PricingTier }

// ── Product types ─────────────────────────────────────────────────────────────
export interface ProductListItem {
  id: string; name: string; images: string[]; age_range: string | null;
  safety_certifications: SafetyCertification[]; is_virtual: boolean; stock: number | null;
  min_order_qty: number; status: string; price_min: number | null; price_max: number | null
}
export interface SafetyCertification {
  name: string; icon?: string
}
export interface ProductDetail {
  id: string; category_id: string | null; name: string; images: string[]; description: string | null;
  specs: Record<string, string[]> | null; age_range: string | null; safety_certifications: SafetyCertification[];
  is_virtual: boolean; virtual_detail: unknown; stock: number | null; min_order_qty: number;
  pricing_rules: Record<string, PricingTier[]>; status: string; sales_count: number;
  category: Category | null; created_at: string | null; updated_at: string | null
}
export interface ProductListParams {
  page?: number; page_size?: number; category_id?: string; age_range?: string; keyword?: string;
  sort?: 'newest' | 'sales_desc' | 'price_asc' | 'price_desc'
}

// Backward-compat alias (consumer pages reference "Product")
export type Product = ProductListItem

// ── API functions ─────────────────────────────────────────────────────────────
export const getProductList = (params?: ProductListParams) => http.get<Paginated<ProductListItem>>('/products', params)
export const getProductDetail = (id: string) => http.get<ProductDetail>(`/products/${id}`)
export const getHotProducts = (limit = 10) => http.get<ProductListItem[]>('/products/hot', { limit })
export const getNewProducts = (limit = 10) => http.get<ProductListItem[]>('/products/new', { limit })
export const getCategories = () => http.get<Category[]>('/products/categories')
