/**
 * 商品列表的一页结果怎么并进已有列表。
 *
 * 从 `pages/products/index.vue` 的 `loadProducts` 里提出来的：那段逻辑写在
 * .vue 里，而本项目没有组件测试环境（无 @vue/test-utils + jsdom），
 * 于是「hasMore 用过滤后的条数算」这个 bug 一直没人拦得住。提成纯函数后
 * `utils/__tests__/product-list.test.ts` 能钉死它。
 *
 * 这里唯一容易写错、也最值钱的一条：**hasMore 由服务端返回的条数决定**。
 */

/**
 * 只需要知道有没有货，不关心商品的其他字段。
 *
 * `stock` 写成 `number | null | undefined`：接口返回的是 `number | null`
 * （见 `api/products.ts` 的 ProductListItem），只写 `number` 会让
 * `ProductListItem` 不满足这个约束、泛型推不出来。
 */
export interface Stocked {
  stock?: number | null
}

export interface ProductPageOptions {
  /** 本次请求的是第几页（从 1 开始） */
  page: number
  /** 每页条数，与服务端约定的一致 */
  pageSize: number
  /** 下拉刷新：即便 page > 1 也整体替换 */
  isRefresh: boolean
  /** 「仅看有货」是客户端过滤，后端 /products 没有这个参数 */
  onlyInStock: boolean
}

export interface ProductPage<T> {
  items: T[]
  hasMore: boolean
}

/**
 * 把服务端返回的一页并进已有列表。
 *
 * @param raw 服务端返回的原始列表（可能是 null / undefined）
 * @param prev 已有的列表（只在「追加」分支用到）
 */
export function mergeProductPage<T extends Stocked>(
  raw: T[] | null | undefined,
  prev: T[],
  opts: ProductPageOptions,
): ProductPage<T> {
  const all = raw || []

  // 过滤只影响**这一页显示几条**，不影响「还有没有下一页」——
  // 过滤掉的商品后面还有页，拿过滤后的条数算 hasMore 会把分页截断：
  // 第 1 页 20 条里只要 1 条缺货，过滤后 19 < 20 就判定到底了，
  // 后面几页那些**有货**的商品再也翻不出来。
  const visible = opts.onlyInStock ? all.filter((p) => (p.stock ?? 0) > 0) : all

  const items = opts.isRefresh || opts.page === 1 ? visible : [...prev, ...visible]

  return { items, hasMore: all.length >= opts.pageSize }
}
