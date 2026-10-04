import http from './request'
import type { Paginated } from './types'

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

// 直接采用仓库既有的分页形状（api/types.ts 的 Paginated<T>），不再自己重声明一份。
// 后端 app/schemas/common.py 的 PaginatedResponse 就是 items/total/page/page_size，
// 重声明那份曾把 items 写成 list，让案例列表对真实响应用不了。
export type CaseListResult = Paginated<DesignCase>

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
