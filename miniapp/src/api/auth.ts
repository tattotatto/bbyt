import http from './request'

// Types
export interface LoginParams {
  code: string  // WeChat login code (wx.login)
  phone?: string
  userInfo?: WechatUserInfo
}

export interface WechatUserInfo {
  nickName: string
  avatarUrl: string
  gender: number
  country: string
  province: string
  city: string
}

export interface LoginResult {
  access_token: string
  refresh_token: string
  expires_in: number
  user_info: UserProfile
}

export interface UserProfile {
  id: number
  nickname: string
  avatar: string
  phone: string
  level: number
  level_name: string
  company_name?: string
  created_at: string
}

// WeChat login
export function wxLogin(params: LoginParams): Promise<{ data: LoginResult }> {
  return http.post<LoginResult>('/auth/wx-login', params)
}

// Phone number login
export function phoneLogin(phone: string, code: string): Promise<{ data: LoginResult }> {
  return http.post<LoginResult>('/auth/phone-login', { phone, code })
}

// Send verification code
export function sendVerifyCode(phone: string): Promise<{ data: { success: boolean } }> {
  return http.post('/auth/send-code', { phone })
}

// Get user profile
export function getUserProfile(): Promise<{ data: UserProfile }> {
  return http.get<UserProfile>('/user/profile')
}

// Update user profile
export function updateUserProfile(data: Partial<UserProfile>): Promise<{ data: UserProfile }> {
  return http.put<UserProfile>('/user/profile', data)
}

// Logout
export function logout(): Promise<{ data: { success: boolean } }> {
  return http.post('/auth/logout')
}

// Refresh token
export function refreshToken(refresh_token: string): Promise<{ data: { access_token: string; refresh_token: string; expires_in: number } }> {
  return http.post('/auth/refresh', { refresh_token })
}
