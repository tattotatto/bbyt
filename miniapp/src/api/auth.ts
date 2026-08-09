import http from './request'

// ── Types ─────────────────────────────────────────────────────────────────────
// UserProfile aligned to backend UserOut (includes retailer_profile nested)
export interface UserProfile {
  id: string; phone: string; role: string; level: string; status: string;
  nickname?: string | null; avatar?: string | null; credit_limit?: number; credit_balance?: number;
  retailer_profile?: {
    company_name: string | null
    business_license: string | null
    contact_person: string | null
    purchase_history_summary?: string | null
    preferred_categories?: string[] | null
  } | null
}

/** Body for PUT /users/me/profile — retailer profile partial update */
export interface RetailerProfileUpdate {
  company_name?: string
  business_license?: string
  contact_person?: string
}

// ── API functions ─────────────────────────────────────────────────────────────
export const wxLogin = (params: { code: string; user_info?: { nickName?: string; avatarUrl?: string } }) =>
  http.post<{ access_token: string; refresh_token: string; user_info: UserProfile }>('/auth/wx-login', params)

export const getUserProfile = () => http.get<UserProfile>('/users/me')

export const updateUserProfile = (data: RetailerProfileUpdate) =>
  http.put<UserProfile>('/users/me/profile', data)

export const logout = () => http.post('/auth/logout')

export const refreshToken = (refresh_token: string) =>
  http.post<{ access_token: string; refresh_token: string }>('/auth/refresh', { refresh_token })
