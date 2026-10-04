import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../request', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), del: vi.fn() },
}))

import http from '../request'
import { getCaseList, getCaseTags } from '../cases'
import type { CaseListParams } from '../cases'

const mockGet = vi.mocked(http.get)

describe('案例接口契约', () => {
  beforeEach(() => {
    mockGet.mockReset()
    mockGet.mockResolvedValue({ data: {} } as any)
  })

  it('标签接口打在后端真实存在的 /cases/tags 上', async () => {
    await getCaseTags()
    // 用 mock.calls[0][0] 而不是 toHaveBeenCalledWith('/cases/tags', undefined)：
    // getCaseTags() 只传一个实参，记录下来的 args 是 ['/cases/tags']（长度 1），
    // 和期望的 ['/cases/tags', undefined]（长度 2）长度不等，匹配不上。
    expect(mockGet.mock.calls[0][0]).toBe('/cases/tags')
    expect(mockGet.mock.calls[0]).toHaveLength(1)
  })

  it('筛选条件按调用方传入原样转发给 /cases', async () => {
    await getCaseList({ style: 'ins风' })
    const [url, params] = mockGet.mock.calls[0]
    expect(url).toBe('/cases')
    expect(params).toMatchObject({ style: 'ins风' })
    expect(params).not.toHaveProperty('style_tag')
  })

  it('类型筛选参数名是 category_tag', async () => {
    await getCaseList({ category_tag: '儿童房' })
    const [, params] = mockGet.mock.calls[0]
    expect(params).toMatchObject({ category_tag: '儿童房' })
  })

  it('筛选条件为空时按调用方传入原样转发，不擅自增删参数', async () => {
    await getCaseList({ page: 1, page_size: 20 })
    const [, params] = mockGet.mock.calls[0]
    expect(params).toEqual({ page: 1, page_size: 20 })
  })

  it('CaseListParams 不接受 style_tag 这个参数名', () => {
    // 这条用例的断言方式是 @ts-expect-error：下一行必须报类型错误。
    // 若有人把 style_tag 加回接口，这行就不再报错，vue-tsc 会因「未使用的 @ts-expect-error」而失败。
    // 注意 vitest 走 esbuild 不做类型检查 —— 真正执行这个断言的是 `npx vue-tsc --noEmit`，
    // 它覆盖 src/**/*.ts（见 miniapp/tsconfig.json 的 include），本文件在其中。
    // @ts-expect-error style_tag 不是 CaseListParams 的合法字段
    const params: CaseListParams = { style_tag: 'ins风' }
    expect(params).toBeDefined()
  })
})
