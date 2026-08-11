// api/users.ts — 用户管理 API
import request from './request'
import type { PaginatedResult } from './products'

export interface UserItem {
  id: string
  phone: string
  role: string
  level: string                  // normal | silver | gold | platinum
  status: string                 // pending_review | active | frozen
  nickname?: string              // 微信用户昵称（phone 为 wx_ 前缀时展示）
  company_name?: string
  contact_person?: string
  business_license?: string
  credit_limit?: number          // 单位：分
  credit_balance?: number        // 单位：分
  created_at: string
}

export interface UserListParams {
  page?: number
  page_size?: number
  keyword?: string
  status?: string
  level?: string
  role?: string
}

export interface ReviewData {
  action: 'approve' | 'reject'
  level?: string                 // 审核通过时设置等级
  credit_limit?: number          // 审核通过时设置账期额度（单位：分）
  reject_reason?: string         // 拒绝原因
}

export function getUserList(params: UserListParams): Promise<PaginatedResult<UserItem>> {
  return request.get('/users/', { params }).then((res) => res.data)
}

export function reviewUser(userId: string, data: ReviewData): Promise<any> {
  return request.post('/users/review', { user_id: userId, ...data }).then((res) => res.data)
}

/** 获取设计师列表（用于订单指派） */
export function getDesigners(): Promise<UserItem[]> {
  return request.get('/users/', { params: { role: 'designer', page_size: 100 } }).then((res) => res.data.items)
}
