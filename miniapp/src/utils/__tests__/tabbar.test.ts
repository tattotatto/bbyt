import { describe, it, expect } from 'vitest'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'

/**
 * 自定义 tabBar 的一致性检查。
 *
 * 为什么放在 utils/__tests__ 下：vitest.config.ts 的 include 只认
 * utils / api / stores 三个 __tests__ 目录。这条用例扫的是源码文件而不是
 * 某个 util，但项目里已有同样的先例（icon-map.test.ts 也是全项目扫描），
 * 所以沿用同一处，不去动测试基建。
 *
 * 为什么值得单独测：`uni.switchTab` 按 **索引** 跳转，而页面路径清单
 * 有两份 —— `pages.json` 的 `tabBar.list`（uni 拿它做路径校验）和
 * `custom-tab-bar/index.vue` 里的 `tabs` 数组（组件拿它渲染和跳转）。
 * 两份顺序一旦不一致，点第 N 个 tab 会跳到另一个页面，而且
 * **不会有任何编译错误或运行时异常** —— 只是安静地跳错。
 */

const ROOT = join(__dirname, '..', '..')

/**
 * 读文件，不存在就返回空串。
 *
 * 用 statSync + try/catch 而不是 `existsSync`：本项目的 `node:fs` 类型
 * 只暴露了 readFileSync / readdirSync / statSync 三个成员（icon-map.test.ts
 * 用的也是这三个），写 `existsSync` 会让 `vue-tsc --noEmit` 报 TS2305。
 *
 * 返回空串而不是抛错，是为了让「文件还没建」这种情况表现为一条能读懂的
 * 断言失败（期望 5 项、实得 0 项），而不是一个堆栈。
 */
function readIfExists(path: string): string {
  try {
    statSync(path)
    return readFileSync(path, 'utf-8')
  } catch {
    return ''
  }
}

interface TabSources {
  /** pages.json 的 tabBar 段；读不到时为 null */
  tabBar: { custom?: boolean; list?: { pagePath: string }[] } | null
  /** pages.json 的 pages 段里注册的路径 */
  registered: string[]
  /** custom-tab-bar/index.vue 里 tabs 数组的 pagePath，按源码顺序 */
  componentPaths: string[]
  /** 组件里标了 raised: true 的 pagePath */
  raisedPaths: string[]
}

function readSources(): TabSources {
  const pagesJsonPath = join(ROOT, 'pages.json')
  const componentPath = join(ROOT, 'custom-tab-bar', 'index.js')

  let tabBar: TabSources['tabBar'] = null
  let registered: string[] = []
  const pagesJson = readIfExists(pagesJsonPath)
  if (pagesJson) {
    // pages.json 里没有注释，是标准 JSON，直接 parse
    const cfg = JSON.parse(pagesJson)
    tabBar = cfg.tabBar ?? null
    registered = (cfg.pages ?? []).map((p: { path: string }) => p.path)
  }

  let componentPaths: string[] = []
  let raisedPaths: string[] = []
  const componentSrc = readIfExists(componentPath)
  if (componentSrc) {
    const text = componentSrc
    // 取 `const TABS = [ ... ]` 这一段的字面量，按出现顺序取 pagePath
    const block = text.match(/const\s+TABS\s*=\s*\[([\s\S]*?)\n\]/)
    if (block) {
      const entries = block[1].split(/\},\s*\n/).filter((l) => l.includes('pagePath'))
      for (const entry of entries) {
        const p = entry.match(/pagePath:\s*'([^']+)'/)
        if (p) componentPaths.push(p[1])
        // raised: true 与它同一条记录
        if (/\braised:\s*true/.test(entry) && p) raisedPaths.push(p[1])
      }
    }
  }

  return { tabBar, registered, componentPaths, raisedPaths }
}

/** 两边比较前都归一到不带前导斜杠的形式 */
const norm = (p: string) => p.replace(/^\//, '')

describe('自定义 tabBar 一致性', () => {
  it('pages.json 开启了 custom tabBar，且 list 有 5 项', () => {
    const { tabBar } = readSources()
    expect(tabBar, 'pages.json 里没有 tabBar 段').not.toBeNull()
    expect(tabBar!.custom, 'tabBar.custom 必须是 true，否则渲染的是原生底栏').toBe(true)
    expect(tabBar!.list).toHaveLength(5)
  })

  it('组件里的 tab 顺序与 pages.json 的 list 完全一致', () => {
    const { tabBar, componentPaths } = readSources()
    const configPaths = (tabBar!.list ?? []).map((t) => norm(t.pagePath))
    const viewPaths = componentPaths.map(norm)

    expect(
      viewPaths,
      'custom-tab-bar/index.vue 的 tabs 顺序与 pages.json 的 tabBar.list 不一致。\n' +
        'switchTab 按索引跳转，顺序错位会导致点第 N 个 tab 跳到另一个页面（且无任何报错）。\n' +
        `  pages.json : ${configPaths.join(' , ')}\n` +
        `  组件       : ${viewPaths.join(' , ')}`,
    ).toEqual(configPaths)
  })

  it('list 里的每一项都在 pages 段注册过', () => {
    const { tabBar, registered } = readSources()
    const reg = new Set(registered.map(norm))
    const missing = (tabBar!.list ?? [])
      .map((t) => t.pagePath)
      .filter((p) => !reg.has(norm(p)))
    expect(missing, '这些 tab 页没有在 pages.json 的 pages 段注册，switchTab 会失败').toEqual([])
  })

  it('凸起圆只有客服一个，且位于正中', () => {
    const { tabBar, raisedPaths } = readSources()
    expect(raisedPaths, '凸起圆必须恰好一个').toHaveLength(1)
    expect(norm(raisedPaths[0])).toBe(norm('pages/ai-assistant/index'))

    const configPaths = (tabBar!.list ?? []).map((t) => norm(t.pagePath))
    expect(
      configPaths.indexOf(norm(raisedPaths[0])),
      '凸起圆在正中才有对称感；位置变了要连几何一起重算',
    ).toBe(2)
  })

  it('原生 iconPath / selectedIconPath 已清空', () => {
    const { tabBar } = readSources()
    const withIcons = (tabBar!.list ?? []).filter(
      (t) => 'iconPath' in t || 'selectedIconPath' in t,
    )
    // 自定义 tabBar 不读这两个字段。旧值本身是坏的（selectedIconPath 全指向
    // 非选中图标），留着只会让后来者以为它们还有作用。
    expect(withIcons, 'custom: true 之后 iconPath / selectedIconPath 已无意义，应删除').toEqual([])
  })
})

/**
 * 显示底栏的 tab 页。
 *
 * 客服页（ai-assistant）不在其中：spec §2 #12 定的是聊天页不显示底栏，
 * 输入栏占住底部。它的特殊处理在 Task 13。
 */
const TAB_PAGES: { file: string; index: number; route: string }[] = [
  { file: 'pages/home/index.vue',     index: 0, route: 'pages/home/index' },
  { file: 'pages/cases/index.vue',    index: 1, route: 'pages/cases/index' },
  { file: 'pages/products/index.vue', index: 3, route: 'pages/products/index' },
  { file: 'pages/mine/index.vue',     index: 4, route: 'pages/mine/index' },
]

function readPage(file: string): string {
  return readIfExists(join(ROOT, file))
}

describe('tab 页的底栏配套', () => {
  it('4 个页面在 onShow 里写的是自己那一格的下标', () => {
    const bad: string[] = []
    for (const { file, index, route } of TAB_PAGES) {
      const text = readPage(file)
      const m = text.match(
        /onShow\s*\(\s*\(\s*\)\s*=>\s*\{[\s\S]*?\}\s*\)/,
      )
      if (!m) {
        bad.push(`${file}: 没有 onShow`)
        continue
      }
      const w = m[0].match(/setStorageSync\(\s*'tabbar_selected'\s*,\s*(\d+)\s*\)/)
      if (!w) {
        bad.push(`${file}: onShow 里没有写 tabbar_selected`)
        continue
      }
      if (Number(w[1]) !== index) {
        // 复制粘贴最容易出的错：4 个文件都写同一个数字。
        bad.push(`${file}: 写的是 ${w[1]}，应当是 ${index}（${route}）`)
      }
    }
    expect(bad, '这些 tab 页的选中态下标不对，切过去时底栏会高亮错的一格：\n' +
      bad.join('\n')).toEqual([])
  })

  it('4 个页面的根元素挂了 .has-custom-tabbar', () => {
    const bad: string[] = []
    for (const { file } of TAB_PAGES) {
      const text = readPage(file)
      // 只看 <template> 后的第一个 <view>，也就是根元素本身 ——
      // 光判断「文件里出现过这个类名」会被注释或子元素骗过。
      const root = text.match(/<template>\s*<view[^>]*\bclass="([^"]+)"/)
      if (!root) {
        bad.push(`${file}: 认不出根元素`)
        continue
      }
      if (!root[1].split(/\s+/).includes('has-custom-tabbar')) {
        bad.push(`${file}: 根元素 class 是 "${root[1]}"，缺 .has-custom-tabbar`)
      }
    }
    expect(bad, '自定义 tabBar 后页面不再自动预留底栏高度，' +
      '根元素缺 .has-custom-tabbar 会让最后一行内容被凸起圆和底栏盖住：\n' +
      bad.join('\n')).toEqual([])
  })
})

/**
 * 客服页不显示底栏（spec §2 #12 / §5.4 ⑤）。
 *
 * 上面 TAB_PAGES 的注释写着客服页的「特殊处理在 Task 13」—— 就是这一段。
 *
 * 关键事实：`tabBar.custom: true` 之后底栏不是微信原生渲染的，而是微信在
 * **每一个 tabBar 页**底部挂一份 `custom-tab-bar/index` 实例。也就是说，
 * 只要页面还在 `tabBar.list` 里，底栏就一定渲染 —— 页面侧写什么都拦不住
 * （不挂 `.has-custom-tabbar` 只是不预留它的高度）。
 * 所以「这一页不要底栏」只能由**组件自己按当前路由**决定。
 *
 * 反过来做（把客服页从 `tabBar.list` 拿掉）看着更直接，代价是：凸起圆失去
 * switchTab 语义、`tabbar_selected` 下标全体前移（products 3→2、mine 4→3），
 * 上面「list 有 5 项」「凸起圆位于正中」「4 个页面写的下标」三条不变量一起要改
 * —— 而其中「顺序错位」正是那个**不报错、只是安静跳错页**的坑。
 * 不值得为了省掉一个 wx:if 去动它。
 */
describe('客服页不显示底栏', () => {
  const component = (file: string) =>
    readIfExists(join(ROOT, 'custom-tab-bar', file))

  it('组件会按当前路由把自己藏起来', () => {
    const js = component('index.js')
    expect(js.includes('pages/ai-assistant/index'), 'index.js 里没有客服页路由').toBe(true)
    expect(/\bhidden\b/.test(js), 'index.js 没有 hidden 这个状态').toBe(true)
  })

  it('组件根元素绑了这个状态', () => {
    const root = component('index.wxml').match(/^\s*<view[^>]*>/m)
    expect(root, '读不到 index.wxml 的根元素').not.toBeNull()
    expect(
      /wx:if="\{\{!?hidden\}\}"/.test(root![0]),
      `index.wxml 的根元素没有按 hidden 决定渲染：\n  ${root![0]}\n` +
        '少了它，客服页底部会多出一条底栏，把输入栏顶上去',
    ).toBe(true)
  })

  it('客服页的根元素不挂 .has-custom-tabbar', () => {
    // 与上面 TAB_PAGES 那条互补：那条只保证 4 个页面**有**，
    // 这条保证第 5 个页面**没有**。多挂一个不会有任何报错，
    // 只是聊天页底部凭空多出一段空白。
    const text = readPage('pages/ai-assistant/index.vue')
    const root = text.match(/<template>\s*<view[^>]*\bclass="([^"]+)"/)
    expect(root, '认不出客服页的根元素').not.toBeNull()
    expect(
      root![1].split(/\s+/).includes('has-custom-tabbar'),
      '客服页挂了 .has-custom-tabbar —— 它不显示底栏，不该预留底栏的高度',
    ).toBe(false)
  })
})

/**
 * 自定义 tabBar 是原生 js/wxml/wxss，uni-app 只做原样复制、不编译。
 * 这带来两个别处没有的失配风险，各测一条。
 */

const UV_ICONS = (() => {
  const src = readIfExists(
    join(ROOT, '..', 'node_modules', 'uview-plus', 'components', 'u-icon', 'icons.js'),
  )
  return new Set([...src.matchAll(/'uicon-([a-z0-9-]+)':/g)].map((m) => m[1]))
})()

describe('自定义 tabBar 的图标名', () => {
  // 从 .vue 迁到 .js 之后，这个文件不再含 "AppIcon" 字样，
  // 于是被 icon-map.test.ts 的模板扫描（它按「文件是否提到 AppIcon」筛）
  // 整个跳过了 —— 图标名写错在真机上只是一块空白，没有任何报错。
  // 所以在这里自己扫一遍，把丢掉的那层覆盖补回来。
  it('index.js 和 index.wxml 里的图标名都在 uview-plus 图标集里', () => {
    expect(UV_ICONS.size, '图标集没被解析出来，这条用例就成了空转').toBeGreaterThan(200)

    const bad: string[] = []
    for (const file of ['index.js', 'index.wxml']) {
      const text = readIfExists(join(ROOT, 'custom-tab-bar', file))
      if (!text) {
        bad.push(`${file}: 读不到`)
        continue
      }
      for (const m of text.matchAll(/\bicon(?:Active)?:\s*'([a-z0-9-]+)'/g)) {
        if (!UV_ICONS.has(m[1])) bad.push(`${file}: icon: '${m[1]}'`)
      }
    }
    expect(bad, '这些图标名在 uview-plus 里不存在，真机上会渲染成空白：\n' +
      bad.join('\n')).toEqual([])
  })
})

describe('自定义 tabBar 与全局定义的数值没有漂移', () => {
  // 原样复制的文件没法 import 任何东西，只能把值抄一遍。抄错不会报错，
  // 只会让底栏比设计稿高一点、圆偏一格 —— 肉眼很难发现。
  it('wxss 里每个 var(--tabbar-*/--z-sticky) 的兜底值都与 theme.scss 一致', () => {
    const theme = readIfExists(join(ROOT, 'styles', 'theme.scss'))
    const tokens = new Map(
      [...theme.matchAll(/--([a-z0-9-]+):\s*([^;}]+?);/g)].map((m) => [m[1], m[2].trim()]),
    )

    const wxss = readIfExists(join(ROOT, 'custom-tab-bar', 'index.wxss'))
    const bad: string[] = []
    let checked = 0
    for (const m of wxss.matchAll(/var\(--([a-z0-9-]+),\s*([^)]+)\)/g)) {
      const [, name, fallback] = m
      const real = tokens.get(name)
      if (real === undefined) continue
      checked++
      // 归一去空格，只比数值本身
      if (real.replace(/\s+/g, '') !== fallback.trim().replace(/\s+/g, '')) {
        bad.push(`--${name}: 兜底 ${fallback.trim()} ≠ theme.scss 的 ${real}`)
      }
    }
    expect(checked, '一个兜底值都没比对到，正则或写法变了').toBeGreaterThanOrEqual(5)
    expect(bad, '兜底值与 token 不一致，:root 没继承时底栏会按错的值渲染：\n' +
      bad.join('\n')).toEqual([])
  })

  it('wxml 里写死的图标颜色与 AppIcon 的 TONE_COLORS 一致', () => {
    const appIcon = readIfExists(join(ROOT, 'components', 'AppIcon.vue'))
    const tones = new Map(
      [...appIcon.matchAll(/\b(primary|ink|muted|white):\s*'(#[0-9a-fA-F]{3,8})'/g)]
        .map((m) => [m[1], m[2].toLowerCase()]),
    )
    expect(tones.size, 'AppIcon 的 TONE_COLORS 没解析出来').toBe(4)

    // u-icon 的 color 是 prop，最终落到行内 style 上，只能用确定的颜色字符串，
    // 没法写 var(--…)。所以这几个值在 wxml 里抄了一份。
    const wxml = readIfExists(join(ROOT, 'custom-tab-bar', 'index.wxml'))
    for (const tone of ['primary', 'muted']) {
      expect(
        wxml.toLowerCase().includes(tones.get(tone)!),
        `wxml 里没有 AppIcon 的 ${tone} 色 ${tones.get(tone)}，两边漂了`,
      ).toBe(true)
    }
  })
})

// ── 跳转方式 ──────────────────────────────────────────────────────────────

/**
 * 遍历 src 下的 .vue / .ts。
 *
 * 跳过 __tests__：本文件自己的正则字面量和断言消息里就写着这些 URL，
 * 扫自己必然自伤（icon-map.test.ts 的源码扫描也是这么处理的）。
 */
function collectSources(dir: string): string[] {
  const out: string[] = []
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry)
    if (statSync(full).isDirectory()) {
      if (entry === '__tests__') continue
      out.push(...collectSources(full))
      continue
    }
    if (full.endsWith('.vue') || full.endsWith('.ts')) out.push(full)
  }
  return out
}

/** '.../src/pages/home/index.vue' -> 'pages/home/index.vue' */
const rel = (f: string) => f.slice(ROOT.length + 1)

/** 去掉 query，只留路径 —— 路由限制只看路径部分 */
const pathOf = (url: string) => url.split('?')[0]

// url 的两种写法：`{ url: '...' }` 与 `uni.navigateTo('...')`。
// `[^}]*?` 遇到模板字符串里的 `${...}` 会提前在 `}` 处停住，但 `url:`
// 总在 `${` 之前，所以仍然取得到（首页的 `/pages/products/index?keyword=${…}` 就是这种）。
const CALL_OBJECT = /uni\.(?:navigateTo|redirectTo)\s*\(\s*\{[^}]*?url\s*:\s*[`'"]([^`'"]+)/
const CALL_STRING = /uni\.(?:navigateTo|redirectTo)\s*\(\s*[`'"]([^`'"]+)/
const CALL_SWITCH = /uni\.switchTab\s*\(\s*\{[^}]*?url\s*:\s*[`'"]([^`'"]+)/

/**
 * 微信两条硬规则，写错都是**静默失败** —— 点了没反应，控制台之外没有任何提示：
 *
 *   navigateTo / redirectTo → tabBar 页：✗（跳不过去）
 *   switchTab              → 非 tabBar 页：✗（同样跳不过去）
 *
 * 写错不会有编译错误，也没有别的测试会红。旧首页有 5 处 navigateTo 指向
 * tabBar 页（分类、搜索、两个「查看更多」），一直是点不动的哑按钮；
 * 改版把分类横滚和「查看更多」做成了主入口，这个 bug 会立刻浮出来。
 */
describe('tabBar 页与普通页的跳转方式', () => {
  function scan(): { bad: string[]; calls: number; tabs: Set<string> } {
    const { tabBar } = readSources()
    const tabs = new Set((tabBar!.list ?? []).map((t) => norm(t.pagePath)))
    const bad: string[] = []
    let calls = 0

    for (const file of collectSources(ROOT)) {
      const text = readIfExists(file)

      for (const re of [CALL_OBJECT, CALL_STRING]) {
        for (const m of text.matchAll(new RegExp(re, 'g'))) {
          calls++
          const p = norm(pathOf(m[1]))
          if (tabs.has(p)) {
            bad.push(`${rel(file)}: navigateTo/redirectTo → ${p}（这是 tabBar 页，跳不过去）`)
          }
        }
      }

      for (const m of text.matchAll(new RegExp(CALL_SWITCH, 'g'))) {
        calls++
        const p = norm(pathOf(m[1]))
        if (!tabs.has(p)) {
          bad.push(`${rel(file)}: switchTab → ${p}（这不是 tabBar 页，跳不过去）`)
        }
      }
    }

    return { bad, calls, tabs }
  }

  it('没有 navigateTo / redirectTo 指向 tabBar 页', () => {
    const forwards = scan().bad.filter((m) => m.includes('navigateTo'))
    expect(
      forwards,
      '这些调用跳不过去，真机上点了没反应：\n' + forwards.join('\n'),
    ).toEqual([])
  })

  it('没有 switchTab 指向非 tabBar 页', () => {
    const back = scan().bad.filter((m) => m.includes('switchTab'))
    expect(
      back,
      'switchTab 只能跳 tabBar 页，其余一律失败：\n' + back.join('\n'),
    ).toEqual([])
  })

  it('扫描本身抓到了调用点，不是空转', () => {
    // 源码里要是改用了 wx.* 前缀，上面两条会一起变成空断言 —— 这条拦住它。
    const { calls } = scan()
    expect(calls, '一个跳转调用都没扫到，说明正则或前缀写法变了').toBeGreaterThanOrEqual(20)
  })
})

/**
 * 原生组件的运行时全局。
 *
 * `src/custom-tab-bar/` 是**原样复制**到输出目录的（uni-app 不编译它），
 * 所以这个文件里的标识符按微信运行时的原样解析 —— 编译过的页面会被
 * 重写成 `e.index.switchTab`（走 import），而这个文件没有编译这一步。
 *
 * 微信只提供 `wx`。uni-app 运行时在产物里挂的是 `globalThis.wx` /
 * `globalThis.document` / `globalThis.harmonyChannel`，**没有** `globalThis.uni`
 * —— 所以这里写 `uni.xxx` 会抛 `ReferenceError`，且因为它在事件回调里，
 * 表现为「点 tab 高亮变了一下、页面不动」，没有任何报错提示。
 */
describe('原生 custom-tab-bar 不使用未定义的全局 uni', () => {
  const SRC = () => readIfExists(join(ROOT, 'custom-tab-bar', 'index.js'))

  it('文件读得到', () => {
    expect(SRC(), 'custom-tab-bar/index.js 读不到').not.toBe('')
  })

  it('不出现 uni.xxx 调用', () => {
    const hits = [...SRC().matchAll(/(?<![\w.$])uni\s*\.\s*([A-Za-z_$][\w$]*)/g)].map(
      (m) => m[1],
    )
    expect(
      [...new Set(hits)],
      '这是原样复制的原生文件，没有编译步骤，`uni` 在微信里不存在 —— ' +
        '用 `wx` 代替（`wx.getStorageSync` 与页面的 `uni.setStorageSync` 是同一个存储区）',
    ).toEqual([])
  })

  it('只用 wx 前缀调用原生 API（证明上面那条不是空转）', () => {
    const hits = [...SRC().matchAll(/(?<![\w.$])wx\s*\.\s*([A-Za-z_$][\w$]*)/g)].map(
      (m) => m[1],
    )
    expect(
      new Set(hits),
      '一个 wx.* 调用都没有 —— 要么文件被改了，要么正则失灵了',
    ).toEqual(new Set(['getStorageSync', 'setStorageSync', 'switchTab']))
  })

  it('跳转用的是切换 tab 的 API，不是普通跳转', () => {
    // navigateTo / redirectTo 跳 tabBar 页是静默失败，这里必须 switchTab。
    expect(SRC(), '跳转没有用 switchTab').toMatch(/wx\.switchTab\s*\(\s*\{/)
  })
})
