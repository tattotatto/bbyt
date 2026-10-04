import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../request', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), del: vi.fn() },
}))

import http from '../request'
import { getCaseList, getCaseTags } from '../cases'

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

  it('风格筛选参数名是 style，不是 style_tag', async () => {
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

  it('不传筛选条件时不带多余的空参数', async () => {
    await getCaseList({ page: 1, page_size: 20 })
    const [, params] = mockGet.mock.calls[0]
    expect(params).toEqual({ page: 1, page_size: 20 })
  })
})
