import http from './request'

export interface DesignCase {
  id: string
  title: string
  description: string | null
  images: string[]
  category_tags: string[]
  style_tags: string[]
  store_area_range: string | null
  is_featured: boolean
  created_at: string | null
}

export interface CaseListParams {
  page?: number
  page_size?: number
  style?: string
  area?: string
  category_tag?: string
  keyword?: string
}

export interface CaseListResult {
  list: DesignCase[]
  total: number
  page: number
  page_size: number
}

/** GET /cases/tags 的返回形状，与后端 app/api/cases.py:list_tags 一致 */
export interface CaseTags {
  category_tags: string[]
  style_tags: string[]
  area_ranges: string[]
}

// Get case list
export function getCaseList(params: CaseListParams): Promise<{ data: CaseListResult }> {
  return http.get<CaseListResult>('/cases', params)
}

// Get case detail
export function getCaseDetail(id: string): Promise<{ data: DesignCase }> {
  return http.get<DesignCase>(`/cases/${id}`)
}

// Get all filter tags in one call
export function getCaseTags(): Promise<{ data: CaseTags }> {
  return http.get<CaseTags>('/cases/tags')
}
