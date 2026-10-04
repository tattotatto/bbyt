import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('../request', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), del: vi.fn() },
}))

import * as authApi from '../auth'
import { useUserStore } from '../../stores/user'

// 与 stores/__tests__/user.test.ts 同一套装配：store 的 setup 会碰 uni 的存储 API，
// 而 useUserStore() 没有 active Pinia 时会直接抛 getActivePinia()。
const uniMock = {
  getStorageSync: () => '',
  setStorageSync: () => {},
  removeStorageSync: () => {},
  login: (opts: any) => opts?.success?.({ code: 'dev_b2_test' }),
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.stubGlobal('uni', uniMock)
})

describe('auth 接口契约', () => {
  it('不再导出 logout —— 后端没有 POST /auth/logout', () => {
    expect(authApi).not.toHaveProperty('logout')
  })

  it('登出是纯本地行为，靠 store 的 logout() 完成', () => {
    // 这一条是「别删错」的守卫：本任务删的是 api/auth.ts 的同名导出，
    // 不是 store 里这个。两者同名，删错任何一处页面就登不出去。
    expect(typeof useUserStore().logout).toBe('function')
  })
})
