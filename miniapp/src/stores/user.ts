import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { wxLogin, getUserProfile } from '../api/auth'
import type { UserProfile } from '../api/auth'

const TOKEN_KEY = 'hxmall_token'
const REFRESH_TOKEN_KEY = 'hxmall_refresh_token'
const USER_INFO_KEY = 'hxmall_user_info'

// Numeric level mapping for backward compatibility (detail.vue, checkout.vue, PriceTable.vue)
const LEVEL_NUMBER_MAP: Record<string, number> = {
  normal: 0,
  silver: 1,
  gold: 2,
  platinum: 3,
}

export const useUserStore = defineStore('user', () => {
  // ── State ────────────────────────────────────────────────────────────────────
  const token = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const userInfo = ref<UserProfile | null>(null)

  // ── Getters ──────────────────────────────────────────────────────────────────
  const isLoggedIn = computed(() => !!token.value)

  /** Numeric level (0-3) for backward compatibility with PriceTable etc. */
  const userLevel = computed(() => {
    if (!userInfo.value?.level) return 0
    return LEVEL_NUMBER_MAP[userInfo.value.level] ?? 0
  })

  /** Chinese level label derived from backend level string */
  const levelLabel = computed(() => {
    const labels: Record<string, string> = {
      normal: '普通会员',
      silver: '银卡会员',
      gold: '金卡会员',
      platinum: '钻石会员',
    }
    return labels[userInfo.value?.level ?? ''] ?? '普通会员'
  })

  /** Discount rate derived from level (backward compat) */
  const discountRate = computed(() => {
    const rates = [1, 0.95, 0.9, 0.85]
    return rates[userLevel.value] || 1
  })

  /** Display nickname with fallback */
  const nickname = computed(() => userInfo.value?.nickname || '未登录')

  /** Display avatar with fallback */
  const avatar = computed(() => userInfo.value?.avatar || '/static/images/default-avatar.png')

  // ── Actions ──────────────────────────────────────────────────────────────────

  /** Initialize: restore state from storage */
  function init() {
    try {
      const savedToken = uni.getStorageSync(TOKEN_KEY)
      const savedRefreshToken = uni.getStorageSync(REFRESH_TOKEN_KEY)
      const savedUserInfo = uni.getStorageSync(USER_INFO_KEY)
      if (savedToken) token.value = savedToken
      if (savedRefreshToken) refreshToken.value = savedRefreshToken
      if (savedUserInfo) {
        try {
          userInfo.value = JSON.parse(savedUserInfo)
        } catch { /* ignore parse error */ }
      }
    } catch { /* ignore storage errors */ }
  }

  /** Login via WeChat: uni.login → wxLogin API → store token + userInfo */
  async function login(userInfoParam?: { nickName?: string; avatarUrl?: string }): Promise<void> {
    // 1. Get WeChat login code
    const code = await new Promise<string>((resolve, reject) => {
      uni.login({
        success: (res: any) => {
          if (res.code) {
            resolve(res.code)
          } else {
            reject(new Error(res.errMsg || 'uni.login failed'))
          }
        },
        fail: (err: any) => reject(new Error(err.errMsg || 'uni.login failed')),
      })
    })

    // 2. Call backend wxLogin
    const res = await wxLogin({
      code,
      user_info: userInfoParam,
    })

    const { access_token, refresh_token, user_info } = res.data

    // 3. Store tokens and user info
    token.value = access_token
    refreshToken.value = refresh_token
    userInfo.value = user_info

    // 4. Persist
    try {
      uni.setStorageSync(TOKEN_KEY, access_token)
      uni.setStorageSync(REFRESH_TOKEN_KEY, refresh_token)
      uni.setStorageSync(USER_INFO_KEY, JSON.stringify(user_info))
    } catch { /* ignore */ }
  }

  /** Logout: clear state + storage, redirect to home */
  function logout() {
    token.value = null
    refreshToken.value = null
    userInfo.value = null
    try {
      uni.removeStorageSync(TOKEN_KEY)
      uni.removeStorageSync(REFRESH_TOKEN_KEY)
      uni.removeStorageSync(USER_INFO_KEY)
    } catch { /* ignore */ }
    uni.switchTab({ url: '/pages/home/index' })
  }

  /** Update token (called by request interceptor on token refresh) */
  function updateToken(accessToken: string, refresh_token?: string) {
    token.value = accessToken
    if (refresh_token) refreshToken.value = refresh_token
    try {
      uni.setStorageSync(TOKEN_KEY, accessToken)
      if (refresh_token) uni.setStorageSync(REFRESH_TOKEN_KEY, refresh_token)
    } catch { /* ignore */ }
  }

  /** Fetch user profile from /users/me */
  async function fetchUserInfo(): Promise<void> {
    const res = await getUserProfile()
    userInfo.value = res.data
    try {
      uni.setStorageSync(USER_INFO_KEY, JSON.stringify(res.data))
    } catch { /* ignore */ }
  }

  /** Update user info locally */
  function updateUserInfo(info: Partial<UserProfile>) {
    if (userInfo.value) {
      userInfo.value = { ...userInfo.value, ...info }
      try {
        uni.setStorageSync(USER_INFO_KEY, JSON.stringify(userInfo.value))
      } catch { /* ignore */ }
    }
  }

  return {
    // State
    token, refreshToken, userInfo,
    // Getters
    isLoggedIn, userLevel, levelLabel, discountRate, nickname, avatar,
    // Actions
    init, login, logout, updateToken, fetchUserInfo, updateUserInfo,
  }
})
