import { describe, it, expect } from 'vitest'
import { mergeProductPage } from '../product-list'

/**
 * 商品列表分页合并。
 *
 * 这段逻辑原来是写在 `pages/products/index.vue` 的 `loadProducts` 里的。
 * 项目没有组件测试环境（无 @vue/test-utils + jsdom），写在 .vue 里的逻辑
 * 测不到 —— 下面第一条用例描述的那个 bug 就是这么活下来的：
 *
 *   「仅看有货」是**客户端**过滤（后端 /products 没有这个参数）。
 *   如果 `hasMore` 用过滤后的条数算，那么第 1 页 20 条里只要有 1 条缺货，
 *   过滤后剩 19 条 < 20，`hasMore` 就成了 false —— 页面显示「已经到底了」，
 *   `onReachBottom` 再也不翻页。用户永远看不到后面几页里那些**有货**的商品。
 *
 * 所以 `hasMore` 必须由**服务端返回的条数**决定：服务端按 PAGE_SIZE 分页，
 * 客户端过滤掉几条不代表后面没有页了。
 */

const PAGE_SIZE = 20

/** 造 n 条商品，第 `outOfStockAt` 条缺货。 */
function makeItems(n: number, outOfStockAt: number[] = []) {
  return Array.from({ length: n }, (_, i) => ({
    id: `p${i + 1}`,
    stock: outOfStockAt.includes(i) ? 0 : 10,
  }))
}

const opts = (over: Partial<Parameters<typeof mergeProductPage>[2]> = {}) => ({
  page: 1,
  pageSize: PAGE_SIZE,
  isRefresh: false,
  onlyInStock: false,
  ...over,
})

describe('mergeProductPage —— hasMore 由服务端条数决定', () => {
  it('返回满页时还有下一页', () => {
    const r = mergeProductPage(makeItems(20), [], opts())
    expect(r.hasMore).toBe(true)
  })

  it('返回不满页时到底了', () => {
    const r = mergeProductPage(makeItems(7), [], opts())
    expect(r.hasMore).toBe(false)
  })

  it('空集合 / null / undefined 时到底了，且列表为空', () => {
    expect(mergeProductPage([], [], opts())).toEqual({ items: [], hasMore: false })
    expect(mergeProductPage(null, [], opts())).toEqual({ items: [], hasMore: false })
    expect(mergeProductPage(undefined, [], opts())).toEqual({ items: [], hasMore: false })
  })
})

describe('mergeProductPage —— 「仅看有货」不能截断分页', () => {
  it('满页里过滤掉一条，hasMore 仍然是 true', () => {
    // 这条就是 bug 的复现：过滤后只剩 19 条，不能因此判定到底了。
    const r = mergeProductPage(makeItems(20, [3]), [], opts({ onlyInStock: true }))
    expect(r.items).toHaveLength(19)
    expect(r.hasMore, '过滤后的条数不能用来算 hasMore，否则后面几页的有货商品永远看不到').toBe(
      true,
    )
  })

  it('满页全被过滤掉，items 为空但 hasMore 仍是 true', () => {
    const r = mergeProductPage(
      makeItems(20, Array.from({ length: 20 }, (_, i) => i)),
      [],
      opts({ onlyInStock: true }),
    )
    expect(r.items).toEqual([])
    expect(r.hasMore, '不能因为这一页没货就以为后面也没货').toBe(true)
  })

  it('关闭「仅看有货」时一条都不过滤', () => {
    const r = mergeProductPage(makeItems(20, [0, 5]), [], opts({ onlyInStock: false }))
    expect(r.items).toHaveLength(20)
  })
})

describe('mergeProductPage —— 首页替换、后续页追加', () => {
  it('page 1 替换已有列表', () => {
    const prev = makeItems(20)
    const r = mergeProductPage(makeItems(3), prev, opts({ page: 1 }))
    expect(r.items).toHaveLength(3)
  })

  it('下拉刷新（isRefresh）即便 page > 1 也替换', () => {
    const prev = makeItems(20)
    const r = mergeProductPage(makeItems(3), prev, opts({ page: 2, isRefresh: true }))
    expect(r.items).toHaveLength(3)
  })

  it('page 2 追加在已有列表之后', () => {
    const prev = makeItems(20)
    const r = mergeProductPage(makeItems(20), prev, opts({ page: 2 }))
    expect(r.items).toHaveLength(40)
    expect(r.items[0].id).toBe('p1')
    expect(r.items[20].id).toBe('p1')
  })

  it('不修改传进来的 prev 数组', () => {
    const prev = makeItems(3)
    mergeProductPage(makeItems(3), prev, opts({ page: 2 }))
    expect(prev).toHaveLength(3)
  })
})
