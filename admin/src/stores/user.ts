// stores/user.ts — 管理员登录状态管理
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getMe } from '@/api/auth'
import type { UserInfo } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  // ===== 状态 =====
  const token = ref<string>(localStorage.getItem('access_token') || '')
  const refreshToken = ref<string>(localStorage.getItem('refresh_token') || '')
  const userInfo = ref<UserInfo | null>(null)

  // ===== 计算属性 =====
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.role === 'admin' || userInfo.value?.role === 'operator')

  // ===== 动作 =====
  /** 登录 */
  async function login(phone: string, password: string) {
    const result = await loginApi({ phone, password })
    token.value = result.access_token
    refreshToken.value = result.refresh_token
    localStorage.setItem('access_token', result.access_token)
    localStorage.setItem('refresh_token', result.refresh_token)
    // 获取用户信息
    await fetchUser()
  }

  /** 获取当前用户信息 */
  async function fetchUser() {
    if (!token.value) return
    try {
      const user = await getMe()
      userInfo.value = user
    } catch {
      // 如果获取失败，清除登录状态
      logout()
    }
  }

  /** 退出登录 */
  function logout() {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return { token, refreshToken, userInfo, isLoggedIn, isAdmin, login, fetchUser, logout }
})
