import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Types (define them in this file)
interface UserInfo {
  id: number
  nickname: string
  avatar: string
  phone: string
  level: number        // 0=普通, 1=银卡, 2=金卡, 3=钻石
  level_name: string
  company_name?: string
  created_at: string
}

interface LoginParams {
  code: string
  phone?: string
  userInfo?: {
    nickName: string
    avatarUrl: string
  }
}

const TOKEN_KEY = 'hxmall_token'
const REFRESH_TOKEN_KEY = 'hxmall_refresh_token'
const USER_INFO_KEY = 'hxmall_user_info'

export const useUserStore = defineStore('user', () => {
  // State
  const token = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const userInfo = ref<UserInfo | null>(null)

  // Getters
  const isLoggedIn = computed(() => !!token.value)
  const userLevel = computed(() => userInfo.value?.level ?? 0)
  const levelLabel = computed(() => {
    const labels = ['普通会员', '银卡会员', '金卡会员', '钻石会员']
    return labels[userLevel.value] || '普通会员'
  })
  const discountRate = computed(() => {
    const rates = [1, 0.95, 0.9, 0.85]
    return rates[userLevel.value] || 1
  })
  const nickname = computed(() => userInfo.value?.nickname || '未登录')
  const avatar = computed(() => userInfo.value?.avatar || '/static/images/default-avatar.png')

  // Actions

  // Initialize: restore state from storage
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

  // Login
  async function login(params: LoginParams) {
    // Call WeChat login API (placeholder - actual API call goes here)
    // In real implementation: const res = await wxLogin(params)
    // For now set mock data to demonstrate the store works
    const mockResponse = {
      access_token: 'mock_access_token_' + Date.now(),
      refresh_token: 'mock_refresh_token_' + Date.now(),
      expires_in: 7200,
      user_info: {
        id: 1,
        nickname: params.userInfo?.nickName || '微信用户',
        avatar: params.userInfo?.avatarUrl || '',
        phone: params.phone || '',
        level: 0,
        level_name: '普通会员',
        company_name: '',
        created_at: new Date().toISOString()
      }
    }

    token.value = mockResponse.access_token
    refreshToken.value = mockResponse.refresh_token
    userInfo.value = mockResponse.user_info

    // Persist
    try {
      uni.setStorageSync(TOKEN_KEY, mockResponse.access_token)
      uni.setStorageSync(REFRESH_TOKEN_KEY, mockResponse.refresh_token)
      uni.setStorageSync(USER_INFO_KEY, JSON.stringify(mockResponse.user_info))
    } catch { /* ignore */ }
  }

  // Logout
  function logout() {
    token.value = null
    refreshToken.value = null
    userInfo.value = null
    try {
      uni.removeStorageSync(TOKEN_KEY)
      uni.removeStorageSync(REFRESH_TOKEN_KEY)
      uni.removeStorageSync(USER_INFO_KEY)
    } catch { /* ignore */ }
    // Redirect to home
    uni.switchTab({ url: '/pages/home/index' })
  }

  // Update token
  function updateToken(accessToken: string, refresh_token?: string) {
    token.value = accessToken
    if (refresh_token) refreshToken.value = refresh_token
    try {
      uni.setStorageSync(TOKEN_KEY, accessToken)
      if (refresh_token) uni.setStorageSync(REFRESH_TOKEN_KEY, refresh_token)
    } catch { /* ignore */ }
  }

  // Fetch user info from server
  async function fetchUserInfo() {
    // Placeholder: const res = await getUserProfile()
    // For now, keep existing user info
    if (!userInfo.value && token.value) {
      try {
        const saved = uni.getStorageSync(USER_INFO_KEY)
        if (saved) userInfo.value = JSON.parse(saved)
      } catch { /* ignore */ }
    }
  }

  // Update user info locally
  function updateUserInfo(info: Partial<UserInfo>) {
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
    init, login, logout, updateToken, fetchUserInfo, updateUserInfo
  }
})
