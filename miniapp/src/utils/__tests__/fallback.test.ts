import { describe, it, expect, vi, afterEach } from 'vitest'
import { applyFallback, isFallbackEnabled } from '../../mock/fallback'
import { DEMO_PRODUCTS } from '../../mock/demo-data'

afterEach(() => {
  vi.unstubAllEnvs()
})

describe('applyFallback —— 只在「空集合」时兜底', () => {
  it('空数组时替换为演示数据', () => {
    expect(applyFallback([], DEMO_PRODUCTS)).toBe(DEMO_PRODUCTS)
  })

  it('null / undefined 时也替换', () => {
    expect(applyFallback(null, DEMO_PRODUCTS)).toBe(DEMO_PRODUCTS)
    expect(applyFallback(undefined, DEMO_PRODUCTS)).toBe(DEMO_PRODUCTS)
  })

  it('有数据时原样返回，不替换', () => {
    const real = [{ id: 'r1' }] as any
    expect(applyFallback(real, DEMO_PRODUCTS)).toBe(real)
  })

  // 这条是本模块存在的主要理由：请求失败时兜底会掩盖真实故障。
  // 失败在调用方表现为 catch 分支，不会走到这里 —— 见下面「失败不替换」的说明用例。
  it('请求失败时调用方走 catch，不会调用本函数', () => {
    const page = async (fetch: () => Promise<any[]>) => {
      try {
        const list = await fetch()
        return applyFallback(list, DEMO_PRODUCTS)
      } catch {
        return []          // 失败保持空 -> 页面渲染错误态，不盖假数据
      }
    }
    return Promise.all([
      page(async () => { throw new Error('network') }).then((r) => {
        expect(r).toEqual([])
      }),
      page(async () => []).then((r) => {
        expect(r).toBe(DEMO_PRODUCTS)
      }),
    ])
  })
})

describe('isFallbackEnabled —— 开关', () => {
  it('显式 true 时开启', () => {
    vi.stubEnv('VITE_DEMO_FALLBACK', 'true')
    expect(isFallbackEnabled()).toBe(true)
  })

  it('未配置时按 false 处理', () => {
    vi.stubEnv('VITE_DEMO_FALLBACK', '')
    expect(isFallbackEnabled()).toBe(false)
  })

  it('只认字符串 true，其他值一律关闭', () => {
    for (const v of ['false', '1', 'TRUE', 'yes']) {
      vi.stubEnv('VITE_DEMO_FALLBACK', v)
      expect(isFallbackEnabled()).toBe(false)
    }
  })
})
