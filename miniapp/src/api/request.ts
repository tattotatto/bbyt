import { API_BASE_URL } from '../utils/constants'

// Types
interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: Record<string, any>
  header?: Record<string, string>
  showLoading?: boolean
  showToast?: boolean
}

interface ResponseData<T = any> {
  code: number
  message: string
  data: T
}

/**
 * `uni.request` 在没传 success/fail/complete 时返回 Promise，
 * **resolve 的是响应对象本身**，不是 `[error, res]`。
 *
 * 这套 uni-app（3.0.0-alpha-5020120260710001）的运行时里，包装成
 * `[null, data]` 的那段是注释掉的（`@dcloudio/uni-mp-weixin` 的 handlePromise），
 * 所以 `const [error, res] = await uni.request(...)` 是对普通对象做数组解构 ——
 * 直接抛 `TypeError: ... is not iterable`，被外层 catch 吞成「网络异常」，
 * 表现为**所有取服务端数据的区块都加载失败**（2026-10-12 的故障）。
 *
 * 网络层失败（微信的 fail 回调）走的是 Promise reject，由外层 catch 处理。
 * 契约由 api/__tests__/request.test.ts 钉住，别改回解构写法。
 */
interface UniResponse<T = any> {
  statusCode: number
  data: ResponseData<T>
  errMsg?: string
}

/** 调一次 uni.request，返回响应对象（失败则 reject）。 */
function sendRequest<T>(
  url: string,
  method: RequestOptions['method'],
  data: Record<string, any>,
  header: Record<string, string>
): Promise<UniResponse<T>> {
  return uni.request({ url, method, data, header, timeout: 30000 }) as unknown as Promise<UniResponse<T>>
}

// API base URL (from shared constants)
export const BASE_URL = API_BASE_URL

// Storage keys
const TOKEN_KEY = 'hxmall_token'
const REFRESH_TOKEN_KEY = 'hxmall_refresh_token'

// Token management
function getToken(): string | null {
  try { return uni.getStorageSync(TOKEN_KEY) || null } catch { return null }
}
function getRefreshToken(): string | null {
  try { return uni.getStorageSync(REFRESH_TOKEN_KEY) || null } catch { return null }
}
function setToken(token: string): void {
  try { uni.setStorageSync(TOKEN_KEY, token) } catch {}
}
function setRefreshToken(token: string): void {
  try { uni.setStorageSync(REFRESH_TOKEN_KEY, token) } catch {}
}
function clearTokens(): void {
  try {
    uni.removeStorageSync(TOKEN_KEY)
    uni.removeStorageSync(REFRESH_TOKEN_KEY)
    uni.removeStorageSync('hxmall_user_info')
  } catch {}
}

// Is currently refreshing token (to prevent multiple simultaneous refresh)
let isRefreshing = false
interface QueueItem {
  resolve: (value: any) => void
  reject: (reason: any) => void
  executeWithToken: (token: string) => Promise<void>
}
let refreshQueue: QueueItem[] = []

// Core request function
async function request<T = any>(options: RequestOptions): Promise<ResponseData<T>> {
  const { url, method = 'GET', data = {}, header = {}, showLoading = false, showToast = true } = options

  if (showLoading) {
    uni.showLoading({ title: '加载中...', mask: true })
  }

  // Build headers with auth token
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...header
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  try {
    const res = await sendRequest<T>(BASE_URL + url, method, data, headers)

    if (showLoading) uni.hideLoading()

    const response = res.data as ResponseData<T>

    // Handle token expired (HTTP 401 or specific error code)
    if (res.statusCode === 401 || response.code === 401 || response.code === 10001) {
      // Token expired, try to refresh
      if (!isRefreshing) {
        isRefreshing = true
        try {
          const newToken = await refreshAccessToken()
          isRefreshing = false
          // Resolve queued requests
          refreshQueue.forEach(item => item.executeWithToken(newToken))
          refreshQueue = []
          // Retry original request with new token
          headers['Authorization'] = `Bearer ${newToken}`
          const retryRes = await sendRequest<T>(BASE_URL + url, method, data, headers)
          return retryRes.data as ResponseData<T>
        } catch (refreshError) {
          isRefreshing = false
          // Reject all queued pending promises so they don't hang
          refreshQueue.forEach(item => item.reject(refreshError))
          refreshQueue = []
          clearTokens()
          // Redirect to login
          uni.reLaunch({ url: '/pages/mine/index' })
          return Promise.reject(refreshError)
        }
      } else {
        // Queue this request until token is refreshed
        return new Promise((resolve, reject) => {
          refreshQueue.push({
            resolve,
            reject,
            executeWithToken: async (newToken: string) => {
              headers['Authorization'] = `Bearer ${newToken}`
              try {
                const qRes = await sendRequest<T>(BASE_URL + url, method, data, headers)
                resolve(qRes.data as ResponseData<T>)
              } catch (queueError) {
                reject(queueError)
              }
            }
          })
        })
      }
    }

    // Handle business error
    if (response.code !== 0) {
      if (showToast) {
        uni.showToast({ title: response.message || '请求失败', icon: 'none' })
      }
      return Promise.reject(new Error(response.message || '请求失败'))
    }

    return response
  } catch (err) {
    if (showLoading) uni.hideLoading()
    if (showToast) {
      uni.showToast({ title: '网络异常，请稍后重试', icon: 'none' })
    }
    return Promise.reject(err)
  }
}

// Refresh access token using refresh token
async function refreshAccessToken(): Promise<string> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    throw new Error('No refresh token available')
  }

  const res = await sendRequest<{ access_token: string; refresh_token: string }>(
    BASE_URL + '/auth/refresh',
    'POST',
    { refresh_token: refreshToken },
    { 'Content-Type': 'application/json' }
  )

  const response = res.data as ResponseData<{ access_token: string; refresh_token: string }>
  if (response.code !== 0) {
    throw new Error(response.message || 'Token refresh failed')
  }

  setToken(response.data.access_token)
  setRefreshToken(response.data.refresh_token)
  return response.data.access_token
}

// Convenience methods
export const http = {
  get<T = any>(url: string, data?: Record<string, any>, options?: Partial<RequestOptions>): Promise<ResponseData<T>> {
    return request<T>({ url, method: 'GET', data, ...options })
  },
  post<T = any>(url: string, data?: Record<string, any>, options?: Partial<RequestOptions>): Promise<ResponseData<T>> {
    return request<T>({ url, method: 'POST', data, ...options })
  },
  put<T = any>(url: string, data?: Record<string, any>, options?: Partial<RequestOptions>): Promise<ResponseData<T>> {
    return request<T>({ url, method: 'PUT', data, ...options })
  },
  delete<T = any>(url: string, data?: Record<string, any>, options?: Partial<RequestOptions>): Promise<ResponseData<T>> {
    return request<T>({ url, method: 'DELETE', data, ...options })
  }
}

export { request, setToken, setRefreshToken, clearTokens, getToken, getRefreshToken }
export default http
