import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '../user'
import { wxLogin, getUserProfile } from '../../api/auth'

vi.mock('../../api/auth', () => ({
  wxLogin: vi.fn(),
  getUserProfile: vi.fn(),
}))

const storage: Record<string, string> = {}
const uniMock = {
  getStorageSync: (k: string) => storage[k] ?? '',
  setStorageSync: (k: string, v: string) => { storage[k] = String(v) },
  removeStorageSync: (k: string) => { delete storage[k] },
  login: (opts: any) => opts?.success?.({ code: 'dev_b2_test' }),
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.stubGlobal('uni', uniMock)
  Object.keys(storage).forEach(k => delete storage[k])
  vi.clearAllMocks()
})

const FAKE_USER = { id: 'u1', phone: '', role: 'retailer', level: 'normal', status: 'pending_review', nickname: '小暖用户', avatar: null }

describe('user store login', () => {
  it('gets wechat code, calls wxLogin, stores token and userInfo', async () => {
    const mWx = wxLogin as unknown as ReturnType<typeof vi.fn>
    mWx.mockResolvedValue({ data: { access_token: 'at1', refresh_token: 'rt1', user_info: FAKE_USER } })
    const store = useUserStore()
    await store.login()
    expect(mWx).toHaveBeenCalledWith(expect.objectContaining({ code: 'dev_b2_test' }))
    expect(store.isLoggedIn).toBe(true)
    expect(store.userInfo?.nickname).toBe('小暖用户')
    expect(store.levelLabel).toBe('普通会员')
  })
})

describe('user store fetchUserInfo', () => {
  it('fetches profile from /users/me', async () => {
    const mGet = getUserProfile as unknown as ReturnType<typeof vi.fn>
    mGet.mockResolvedValue({ data: FAKE_USER })
    const store = useUserStore()
    await store.fetchUserInfo()
    expect(mGet).toHaveBeenCalled()
    expect(store.userInfo?.id).toBe('u1')
  })
})
