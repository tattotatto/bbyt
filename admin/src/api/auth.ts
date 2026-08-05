// api/auth.ts — 认证相关 API
import request from './request'

export interface LoginParams {
  phone: string
  password: string
}

export interface LoginResult {
  access_token: string
  refresh_token: string
}

export interface UserInfo {
  id: string
  phone: string
  role: string
  status: string
  created_at: string
}

/** 管理员登录 */
export function login(params: LoginParams): Promise<LoginResult> {
  return request.post('/auth/login', params).then((res) => res.data)
}

/** 获取当前用户信息 */
export function getMe(): Promise<UserInfo> {
  return request.get('/users/me').then((res) => res.data)
}
