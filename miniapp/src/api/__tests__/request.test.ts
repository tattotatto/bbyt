import { describe, it, expect, vi, beforeEach } from 'vitest'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { BASE_URL, http } from '../request'
import { API_BASE_URL } from '../../utils/constants'

describe('request base url', () => {
  it('uses the shared API_BASE_URL', () => {
    expect(BASE_URL).toBe(API_BASE_URL)
  })
})

// ══════════════════════════════════════════════════════════════════════════
//  请求层与 uni.request 的约定
// ══════════════════════════════════════════════════════════════════════════
//
// 2026-10-12 的线上症状：小程序里所有「从服务器取的数据」都显示加载失败，
// 而同一个接口用 curl 打是 200 —— 服务端没问题，是请求层拿错了返回值。
//
// 这套 uni-app（3.0.0-alpha-5020120260710001）的 `uni.request` 在没有传
// success/fail/complete 时返回 Promise，**resolve 的是响应对象本身**
// （{ statusCode, data, header, errMsg }），不是 [error, res]。
// 运行时里那个 [null, data] 的数组包装是**注释掉的**：
//   node_modules/@dcloudio/uni-mp-weixin/dist/uni.api.esm.js 的 handlePromise()
// 于是 `const [error, res] = await uni.request(...)` 是对普通对象做数组解构，
// 直接抛 TypeError（object is not iterable），落进外层 catch 变成
// 「网络异常，请稍后重试」——每个分区都成错误态。
//
// 这个文件里的用例是行为级的：真的把 uni.request 换成替身，跑通请求层，
// 而不是检查源码里有没有某段字符串（那三条静默失败的教训）。
// ══════════════════════════════════════════════════════════════════════════

interface UniCall {
  url: string
  method: string
  data: Record<string, any>
  header: Record<string, string>
}

/** 微信侧单次请求的应答：resolve 响应对象，或 reject 表示网络层失败。 */
type Responder = (call: UniCall) => Promise<any>

const storage = new Map<string, any>()
let calls: UniCall[] = []
let toasts: string[] = []
let reLaunches: string[] = []
let responder: Responder = () => Promise.reject(new Error('测试没设 responder'))

const uniMock = {
  getStorageSync: (k: string) => storage.get(k) ?? '',
  setStorageSync: (k: string, v: any) => { storage.set(k, v) },
  removeStorageSync: (k: string) => { storage.delete(k) },
  showToast: (o: { title: string }) => { toasts.push(o.title) },
  showLoading: () => {},
  hideLoading: () => {},
  reLaunch: (o: { url: string }) => { reLaunches.push(o.url) },
  request: (o: UniCall) => {
    // 快照参数再记录：请求层在 401 重试前会就地改 header 对象，
    // 存引用的话连第一次调用的记录也会跟着变（真实传输是同步读走的）。
    const snapshot: UniCall = { ...o, data: { ...o.data }, header: { ...o.header } }
    calls.push(snapshot)
    return responder(snapshot)
  },
}

/** 后端成功响应（信封 {code,message,data}）。 */
const ok = (data: any, statusCode = 200) =>
  Promise.resolve({ statusCode, data: { code: 0, message: 'ok', data } })

/** 后端业务错误。 */
const bizError = (code: number, message: string, statusCode = 200) =>
  Promise.resolve({ statusCode, data: { code, message, data: null } })

beforeEach(() => {
  vi.stubGlobal('uni', uniMock)
  storage.clear()
  calls = []
  toasts = []
  reLaunches = []
  responder = () => Promise.reject(new Error('测试没设 responder'))
})

describe('请求层怎么读 uni.request 的返回值', () => {
  it('成功时把响应对象当对象取，返回业务信封（不是 [error, res]）', async () => {
    // 复现用例：这一条在修复前会以 TypeError（object is not iterable）被拒，
    // 也就是线上「所有需要服务器数据的区块都加载失败」。
    responder = () => ok([{ id: 7, name: '哈衣' }])

    const res = await http.get('/products/hot')

    expect(res.code).toBe(0)
    expect(res.data).toEqual([{ id: 7, name: '哈衣' }])
  })

  it('打到 BASE_URL + 路径上，且带上 Content-Type', async () => {
    responder = () => ok([])

    await http.get('/products/hot')

    expect(calls[0].url).toBe(`${BASE_URL}/products/hot`)
    expect(calls[0].method).toBe('GET')
    expect(calls[0].header['Content-Type']).toBe('application/json')
  })

  it('有 token 时带 Authorization，没有就不带（空串不算有）', async () => {
    responder = () => ok([])

    await http.get('/cart')
    expect(calls[0].header.Authorization).toBeUndefined()

    storage.set('hxmall_token', 'tk_1')
    await http.get('/cart')
    expect(calls[1].header.Authorization).toBe('Bearer tk_1')
  })

  it('网络层失败（fail -> reject）要转成拒绝，而不是抛到调用方之外', async () => {
    // 数组解构时代，错误是 resolve 出来的 [error]；现在 reject 才是失败。
    responder = () => Promise.reject(new Error('request:fail timeout'))

    await expect(http.get('/products/hot')).rejects.toBeTruthy()
  })

  it('业务码不是 0 时拒绝，并把后端的 message 提示出来', async () => {
    responder = () => bizError(40004, '商品已下架')

    await expect(http.get('/products/1')).rejects.toThrow('商品已下架')
    expect(toasts).toContain('商品已下架')
  })

  it('业务码 0 但 data 为空集合时照常返回（空不是错误）', async () => {
    // 生产库现在就是空的：接口 200 + code 0 + data: []，
    // 这种要交给页面的空状态处理，不能变成「加载失败」。
    responder = () => ok([])

    const res = await http.get('/cases', { page: 1 })

    expect(res.code).toBe(0)
    expect(res.data).toEqual([])
    expect(toasts).toEqual([])
  })
})

describe('401 的处理', () => {
  it('没有 refresh token 时清掉本地凭据、回登录页、拒绝', async () => {
    storage.set('hxmall_token', 'expired')
    storage.set('hxmall_user_info', '{"id":"u1"}')
    // 后端的 401 不是业务信封，是 FastAPI 的 {"detail": "请先登录"}
    responder = () => Promise.resolve({ statusCode: 401, data: { detail: '请先登录' } })

    await expect(http.get('/users/me')).rejects.toBeTruthy()

    expect(storage.has('hxmall_token')).toBe(false)
    expect(storage.has('hxmall_user_info')).toBe(false)
    expect(reLaunches).toEqual(['/pages/mine/index'])
  })

  it('有 refresh token 时刷新并自动重试，调用方拿到数据', async () => {
    storage.set('hxmall_token', 'expired')
    storage.set('hxmall_refresh_token', 'rt_1')

    let n = 0
    responder = (call) => {
      if (call.url.endsWith('/auth/refresh')) {
        return ok({ access_token: 'fresh', refresh_token: 'rt_2' })
      }
      // 第一次 401，换成新 token 后 200
      return ++n === 1
        ? Promise.resolve({ statusCode: 401, data: { detail: '请先登录' } })
        : ok({ id: 'u1' })
    }

    const res = await http.get('/users/me')

    expect(res.data).toEqual({ id: 'u1' })
    expect(storage.get('hxmall_token')).toBe('fresh')
    expect(storage.get('hxmall_refresh_token')).toBe('rt_2')
    // 中间夹着一次 /auth/refresh，所以按 url 过滤出重试那一发，
    // 不能按下标取（calls[1] 是刷新请求本身）。
    const meCalls = calls.filter((c) => c.url.endsWith('/users/me'))
    expect(meCalls).toHaveLength(2)
    expect(meCalls[0].header.Authorization).toBe('Bearer expired')
    expect(meCalls[1].header.Authorization).toBe('Bearer fresh')
  })
})

// ── 平台约定：别把数组解构「改回去」 ──────────────────────────────────────
describe('uni.request 的 Promise 形状（平台约定）', () => {
  const api = (() => {
    try {
      return readFileSync(
        join(__dirname, '..', '..', '..', 'node_modules', '@dcloudio', 'uni-mp-weixin', 'dist', 'uni.api.esm.js'),
        'utf-8',
      )
    } catch {
      return ''
    }
  })()

  it('读得到 uni-app 运行时（防空转）', () => {
    expect(api, 'uni-mp-weixin 的运行时读不到，这条约定的依据要重新找').not.toBe('')
  })

  it('promisify 把 resolve 直接当成功回调 —— 没有 [err, res] 包装', () => {
    // 找到了 handlePromise 的函数体：数组包装（return promise.then(d => [null, d])）
    // 是注释掉的，所以 resolve 的就是响应对象。哪天依赖升级把它打开，
    // 请求层要跟着改回数组解构 —— 这条会先失败。
    const at = api.indexOf('function handlePromise')
    expect(at, '运行时里找不到 handlePromise').toBeGreaterThan(-1)
    // 必须剥掉注释行：那段数组包装正是被注释掉的，注释里就写着 `[null, data]`，
    // 不剥的话这条用例永远是红的（theme-tokens 那条也被同一个坑绊过）。
    const body = api
      .slice(at, api.indexOf('\n}', at))
      .split('\n')
      .filter((line) => !line.trim().startsWith('//'))
      .join('\n')
    expect(body, 'handlePromise 又开始包 [err, res] 了，请求层的取法要跟着改').not.toContain('[null')
    expect(body, 'handlePromise 不再是直接返回 promise 了').toContain('return promise')

    // 数组包装若是被打开，一定是 `[null, data]` 这种形状；
    // 同时确认成功/失败是直接挂到 resolve/reject 上的（就是 resolve 响应对象）。
    expect(api).toContain('success: resolve')
    expect(api).toContain('fail: reject')
  })
})
