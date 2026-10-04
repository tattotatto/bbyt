import { describe, it, expect } from 'vitest'
import { readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

/**
 * 我的页（pages/mine/index）的契约。
 *
 * 状态在 `<script setup>` 里不导出，所以扫源码。扫的是几条**改错了不会报错**
 * 的要求 —— 这一页原来的九条菜单链接全是死的（`/pages/mine/company`，
 * 而 pages.json 注册的是 `pages/mine/company/index`），点了没反应、没有任何提示：
 *
 *   1. 菜单/订单入口的路由路径没在 pages.json 里注册 → 点了静默失败
 *   2. 订单入口用了后端不认识的状态值（旧的 `pending`，订单页认的是
 *      `pending_payment`）→ 跳到「全部」，看起来像"就是没有待付款订单"
 *   3. tabBar 页用 navigateTo 跳 → 静默失败（必须 switchTab）
 *   4. 又写一个 goToLogin → 两条登录路径，早晚漂
 *   5. 页面上留着 emoji → 跨机型字形差异（spec §3，全站换 AppIcon）
 *
 * 用 statSync + try/catch 而不是 `existsSync`：本项目的 `node:fs` 类型只暴露
 * readFileSync / readdirSync / statSync，写 existsSync 会让 vue-tsc 报 TS2305
 * （同 tabbar.test.ts / ai-assistant-page.test.ts）。
 */

const ROOT = join(__dirname, '..', '..')
const PAGE = 'pages/mine/index.vue'
const ORDER_LIST = 'pages/order/list.vue'

function readIfExists(path: string): string {
  try {
    statSync(path)
    return readFileSync(path, 'utf-8')
  } catch {
    return ''
  }
}

const src = () => readIfExists(join(ROOT, PAGE))

/**
 * 从 `marker` 之后的第一个 `{` 开始，返回配对括号内的块内容。
 * 不用正则取块：块里有嵌套的对象字面量，`/\[[\s\S]*?\]/` 会提前收口。
 */
function blockAfter(text: string, marker: string): string | null {
  const at = text.indexOf(marker)
  if (at < 0) return null
  const open = text.indexOf('{', at)
  if (open < 0) return null
  let depth = 0
  for (let i = open; i < text.length; i++) {
    if (text[i] === '{') depth++
    else if (text[i] === '}') {
      depth--
      if (depth === 0) return text.slice(open + 1, i)
    }
  }
  return null
}

/**
 * 从 `marker` **之后**的第一个 `[` 开始，返回配对括号内的数组内容。
 *
 * 不能用 blockAfter 取数组：数组字面量里第一个 `{` 只是**第一个元素**，
 * 括号配对会在那里收口，于是「订单页认得的 status 值」只剩第一个 ——
 * 断言看着是绿的，其实只比了一个值。
 *
 * 起点从 marker 末尾算起：marker 自己可能带 `[]`（`const tabs: TabItem[]`），
 * 从 marker 开头找 `[` 会命中它。
 */
function arrayAfter(text: string, marker: string): string | null {
  const at = text.indexOf(marker)
  if (at < 0) return null
  const open = text.indexOf('[', at + marker.length)
  if (open < 0) return null
  let depth = 0
  for (let i = open; i < text.length; i++) {
    if (text[i] === '[') depth++
    else if (text[i] === ']') {
      depth--
      if (depth === 0) return text.slice(open + 1, i)
    }
  }
  return null
}

/** pages.json 里注册过的所有路由（去掉前导斜杠）。 */
function registeredRoutes(): Set<string> {
  const cfg = JSON.parse(readIfExists(join(ROOT, 'pages.json')))
  return new Set<string>((cfg.pages ?? []).map((p: { path: string }) => p.path))
}

/** pages.json 里 tabBar 页的路由 —— 这些只能用 switchTab 跳。 */
function tabBarRoutes(): Set<string> {
  const cfg = JSON.parse(readIfExists(join(ROOT, 'pages.json')))
  return new Set<string>(
    (cfg.tabBar?.list ?? []).map((t: { pagePath: string }) =>
      String(t.pagePath).replace(/^\//, ''),
    ),
  )
}

/**
 * 页面里所有跳转目标的路由。
 *
 * 两种写法都要抓：`uni.navigateTo({ url: '/x' })` 和 `navigateTo('/x')`。
 * 只抓前者会漏掉后者 —— 而旧版这一页九条菜单全是后者，于是断言看着是绿的，
 * 实际一条路由都没看到（这类"空集合断言"是死断言，不会红也拦不住任何东西）。
 *
 * 模板字符串里嵌了三元表达式（`/pages/order/list${status ? ...}`），
 * 所以取到第一个 `?`、`$` 或反引号就截断 —— 留下的正好是路由本身。
 */
function routesIn(text: string): string[] {
  const out: string[] = []
  const patterns = [
    /url:\s*[`'"]([^`'"]+)/g,
    /(?:navigateTo|redirectTo|reLaunch|switchTab)\(\s*[`'"]([^`'"]+)/g,
  ]
  for (const re of patterns) {
    for (const m of text.matchAll(re)) {
      const raw = m[1].split('?')[0].split('$')[0].split('`')[0].trim()
      if (raw) out.push(raw)
    }
  }
  return [...new Set(out)]
}

/** 订单列表页认得的 status 值，从它的 tabs 数组里取，避免两处漂。 */
function orderTabValues(): string[] {
  const text = readIfExists(join(ROOT, ORDER_LIST))
  const body = arrayAfter(text, 'const tabs: TabItem[] =')
  if (!body) return []
  return [...body.matchAll(/value:\s*'([^']+)'/g)].map((m) => m[1])
}

describe('我的页', () => {
  it('页面源码读得到（改名或挪走后这条先炸，免得下面几条假绿）', () => {
    expect(src(), `${PAGE} 读不到`).not.toBe('')
  })

  it('菜单与订单入口的路由都真的注册过', () => {
    const registered = registeredRoutes()
    const routes = routesIn(src())
    // 先证明真的看到了路由：解析器失灵时下面那条会以空集合"通过"。
    expect(routes.length, '一条跳转目标都没解析到 —— 解析器失灵了，不是页面没问题')
      .toBeGreaterThan(0)
    const dead = routes.filter((r) => !registered.has(r.replace(/^\//, '')))
    expect(
      dead,
      '这些路由没在 pages.json 里注册，点了会静默失败（没有 toast，什么都不发生）：\n' +
        dead.map((d) => `  ${d}`).join('\n'),
    ).toEqual([])
  })

  it('跳 tabBar 页一律用 switchTab', () => {
    // navigateTo / redirectTo 跳 tabBar 页是**静默失败**：既没报错也没反应。
    // 只能 switchTab。
    // 两种写法都扫：`navigateTo({ url: '/x' })` 和 `navigateTo('/x')`。
    // 只扫前者的话，旧版这种位置参数写法整页都看不见 —— 断言绿得毫无意义。
    const tabs = tabBarRoutes()
    const bad = [
      ...src().matchAll(/(?:navigateTo|redirectTo)\(\s*(?:\{\s*url:\s*)?['"`]([^'"`]+)/g),
    ]
      .map((m) => m[1].replace(/^\//, '').split('?')[0])
      .filter((r) => tabs.has(r))
    expect(bad, `这些是 tabBar 页，必须 switchTab：\n  ${bad.join('\n  ')}`).toEqual([])
  })

  it('联系客服指向客服 tab', () => {
    // 客服是 tabBar 页（index 2），连的是改造后的蓓贝客服页。
    expect(
      /switchTab\s*\(\s*\{\s*url:\s*['"`]\/pages\/ai-assistant\/index['"`]/.test(src()),
      '联系客服没有 switchTab 到 /pages/ai-assistant/index',
    ).toBe(true)
  })

  it('订单入口的状态值订单页认得', () => {
    const text = src()
    const body = blockAfter(text, 'const ORDER_ENTRIES')
    expect(body, '没有 ORDER_ENTRIES（订单五宫格的数据源）').not.toBeNull()

    const statuses = [...body!.matchAll(/status:\s*'([^']+)'/g)].map((m) => m[1])
    expect(statuses.length, 'ORDER_ENTRIES 里一个 status 都没解析到').toBeGreaterThan(0)

    // 旧代码这里写的是 'pending'，而订单页认的是 'pending_payment' ——
    // 两字之差，点「待付款」落到「全部」，看起来像"就是没有待付款订单"。
    //
    // 'refunding' 是**已知且唯一**的例外：订单页的 tabs 里没有退款一档，
    // 后端也没有这个状态，所以点「退款售后」会落到「全部」且不高亮。
    // 这是本任务范围外的既有行为（订单页属于那 15 个范围外页面），
    // 已记入 ledger 的 Ruling G 和 Task 15 的视觉回归记录。
    //
    // 写成一份显式的例外清单，而不是把字面量直接塞进 allowed：
    // 一旦出现**第二个**订单页不认的状态值，下面这条就红 ——
    // 白名单不会把新问题一起吞掉。
    const KNOWN_UNSUPPORTED = ['refunding']
    const allowed = new Set([...orderTabValues(), ...KNOWN_UNSUPPORTED])
    const unknown = statuses.filter((s) => !allowed.has(s))
    expect(
      unknown,
      `订单页认的是 ${[...orderTabValues()].join(' / ')}：\n  ${unknown.join('\n  ')}`,
    ).toEqual([])

    // 反向断言：例外必须还是必要的。订单页哪天补上退款 tab，这条会红，
    // 提醒把 KNOWN_UNSUPPORTED 清空 —— 否则例外会一直躺在那里没人收。
    const nowSupported = KNOWN_UNSUPPORTED.filter((s) => orderTabValues().includes(s))
    expect(
      nowSupported,
      `订单页现在认得这些值了，请从 KNOWN_UNSUPPORTED 里删掉：${nowSupported.join(' / ')}`,
    ).toEqual([])

    expect(
      statuses,
      '待付款必须是 pending_payment（订单页 tabs 里的值）',
    ).toContain('pending_payment')
  })

  it('只有一条登录路径', () => {
    const text = src()
    expect(text, '新写了 goToLogin —— 该页已有 handleLogin，两条路径早晚漂').not.toMatch(
      /function\s+goToLogin/,
    )
    expect(text, '没有 handleLogin').toMatch(/function\s+handleLogin/)
    expect(text, '头图的 @login 没绑到 handleLogin').toMatch(/@login="handleLogin"/)
  })

  it('页面里不再有 emoji（都换成了 AppIcon）', () => {
    // 用 Unicode 属性而不是写死一张表：写死的表在有人加新 emoji 时不会红。
    const found = new Map<string, string>()
    for (const ch of src()) {
      if (!/\p{Extended_Pictographic}/u.test(ch)) continue
      if (!found.has(ch)) found.set(ch, 'U+' + (ch.codePointAt(0) ?? 0).toString(16).toUpperCase())
    }
    expect(
      [...found.entries()].map(([c, cp]) => `${c} (${cp})`),
      '这些 emoji 还在页面里。brief Step 3 要求全部换成 AppIcon',
    ).toEqual([])
  })
})
