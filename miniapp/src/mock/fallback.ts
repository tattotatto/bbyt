/**
 * 演示数据兜底判定。
 *
 * 两条规则，都很要紧：
 *
 * 1. **只在空集合时兜底。** 请求失败时不兜底 —— 失败在调用方表现为
 *    catch 分支，页面渲染错误态。用假数据盖住真实故障，会让线上问题
 *    一直看不见。
 * 2. **开关缺失时按关闭处理。** 上线漏配的后果是「页面空」（用户看到
 *    空状态），比「线上展示假数据」轻得多。
 */
import { DEMO_CASES, DEMO_PRODUCTS } from './demo-data'

export function isFallbackEnabled(): boolean {
  // 只认严格的字符串 'true'。'1' / 'TRUE' / 'yes' 一律当关闭 ——
  // 这个开关决定线上要不要展示假数据，宁可漏开也不要误开。
  return import.meta.env.VITE_DEMO_FALLBACK === 'true'
}

/**
 * 空集合时用演示数据替换。纯函数，无副作用。
 *
 * @param data 接口返回的数组（可能是空数组 / null / undefined）
 * @param demo 对应的演示数据
 */
export function applyFallback<T>(data: T[] | null | undefined, demo: T[]): T[] {
  if (!isFallbackEnabled()) return data ?? []
  if (!data || data.length === 0) return demo
  return data
}

/** 各分区常用组合，省得每个页面都 import 一遍演示数据。 */
export const fallbackFor = {
  products: (data: unknown[] | null | undefined) => applyFallback(data as any, DEMO_PRODUCTS),
  cases: (data: unknown[] | null | undefined) => applyFallback(data as any, DEMO_CASES),
}
