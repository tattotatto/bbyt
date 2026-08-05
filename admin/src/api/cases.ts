// api/cases.ts — 案例管理 API
import request from './request'
import type { PaginatedResult } from './products'

export interface CaseForm {
  title: string
  description: string
  images: string[]
  category_tags: string[]   // 多选：婴童游泳馆/母婴生活馆/儿童乐园
  style_tags: string[]       // 多选：ins风/自然原木/卡通童趣
  area_range: string         // 面积范围
  sort_order: number
  is_featured: boolean
}

export interface CaseItem extends CaseForm {
  id: string
  status: string
  created_at: string
  updated_at: string
}

export interface CaseListParams {
  page?: number
  page_size?: number
  keyword?: string
  category_tag?: string
  style_tag?: string
  is_featured?: boolean
}

export function getCaseList(params: CaseListParams): Promise<PaginatedResult<CaseItem>> {
  return request.get('/cases/', { params }).then((res) => res.data)
}

export function createCase(data: CaseForm): Promise<CaseItem> {
  return request.post('/cases/', data).then((res) => res.data)
}

export function updateCase(id: string, data: Partial<CaseForm>): Promise<CaseItem> {
  return request.put(`/cases/${id}`, data).then((res) => res.data)
}

export function deleteCase(id: string): Promise<void> {
  return request.delete(`/cases/${id}`).then((res) => res.data)
}

/** 获取单个案例详情（用于编辑回填） */
export function getCaseDetail(id: string): Promise<CaseItem> {
  return request.get(`/cases/${id}`).then((res) => res.data)
}
