import http from './request'

export interface DesignCase {
  id: number
  title: string
  description: string
  images: string[]
  cover_image: string
  style_tags: string[]      // e.g. ["北欧风", "简约"]
  category_tags: string[]    // e.g. ["婴儿房", "玩具收纳"]
  designer_name: string
  designer_avatar: string
  used_products: CaseProduct[]
  view_count: number
  like_count: number
  is_liked: boolean
  created_at: string
}

export interface CaseProduct {
  id: number
  name: string
  image: string
  price: number
}

export interface CaseListParams {
  page?: number
  page_size?: number
  style_tag?: string
  category_tag?: string
  keyword?: string
}

export interface CaseListResult {
  list: DesignCase[]
  total: number
  page: number
  page_size: number
}

// Get case list
export function getCaseList(params: CaseListParams): Promise<{ data: CaseListResult }> {
  return http.get<CaseListResult>('/cases', params)
}

// Get case detail
export function getCaseDetail(id: number): Promise<{ data: DesignCase }> {
  return http.get<DesignCase>(`/cases/${id}`)
}

// Like a case
export function likeCase(id: number): Promise<{ data: { is_liked: boolean; like_count: number } }> {
  return http.post(`/cases/${id}/like`)
}

// Get case style tags
export function getStyleTags(): Promise<{ data: string[] }> {
  return http.get<string[]>('/cases/tags/styles')
}

// Get case category tags
export function getCategoryTags(): Promise<{ data: string[] }> {
  return http.get<string[]>('/cases/tags/categories')
}
