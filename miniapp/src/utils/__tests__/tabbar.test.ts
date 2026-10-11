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

/**
 * uview-plus 的图标集。
 *
 * icons.js 里的值可能是 `\uXXXX` 转义、也可能是字面 PUA 字符，两种写法先
 * 统一还原成字符再比 —— 否则比的是写法，不是字形。
 */
const UV_ICON_SRC = readIfExists(
  join(ROOT, '..', 'node_modules', 'uview-plus', 'components', 'u-icon', 'icons.js'),
)

/** `''` → 对应的字符 */
function unescapeGlyph(s: string): string {
  return s.replace(/\\u([0-9a-fA-F]{4})/g, (_, h: string) =>
    String.fromCharCode(parseInt(h, 16)),
  )
}

const UV_ICONS = new Set([...UV_ICON_SRC.matchAll(/'uicon-([a-z0-9-]+)':/g)].map((m) => m[1]))

const UV_GLYPHS = new Map(
  [...UV_ICON_SRC.matchAll(/'uicon-([a-z0-9-]+)':\s*'([^']*)'/g)].map((m) => [
    m[1],
    unescapeGlyph(m[2]),
  ]),
)

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

  it('图标颜色跟着 token 走，不是写死的十六进制', () => {
    // 旧实现是 `<u-icon color="#e16531">`：u-icon 的 color 是 Vue prop，
    // 只能收一个确定的颜色字符串，于是品牌色在 wxml 里抄了一份。
    // 2026-10-11 品牌色 #FF7B7B → #e16531 时，正是这种抄写不会跟着走。
    // 图标改成原生 <text> 后颜色回到 CSS，这条钉住它别再抄回 wxml 里去。
    const wxss = readIfExists(join(ROOT, 'custom-tab-bar', 'index.wxss'))

    const base = wxss.match(/^\.tabbar__icon\s*\{([^}]*)\}/m)
    expect(base, '认不出 .tabbar__icon 规则').not.toBeNull()
    expect(base![1], '图标默认色应当引用 --text-muted 这个 token').toMatch(
      /color:\s*var\(--text-muted,/,
    )

    const active = wxss.match(/^\.tabbar__icon--active\s*\{([^}]*)\}/m)
    expect(active, '认不出 .tabbar__icon--active 规则').not.toBeNull()
    expect(active![1], '选中色应当引用 --color-primary 这个 token').toMatch(
      /color:\s*var\(--color-primary,/,
    )
  })
})

/**
 * 字形表。
 *
 * 底栏是**原样复制**的原生组件，用不了 u-icon：u-icon 是编译过的 uni-app
 * 组件，props 只走 u-p 通道（运行时非页面分支取的是 `properties.uP`），
 * 而原生 wxml 发不出 u-p —— `name` 落到组件里是 undefined，图标渲染成
 * 空串且**没有任何报错**。所以 9 个字形码点在 custom-tab-bar/index.js 里
 * 抄了一份，于是有了「抄错」这个新的失败模式，同样无报错、只是空白。
 */
describe('自定义 tabBar 的字形表', () => {
  /** index.js 里 `const GLYPHS = { … }` 那一段 */
  const localGlyphs = (() => {
    const js = readIfExists(join(ROOT, 'custom-tab-bar', 'index.js'))
    const block = js.match(/const\s+GLYPHS\s*=\s*\{([\s\S]*?)\n\}/)
    if (!block) return new Map<string, string>()
    return new Map(
      // 键可能带引号（'home-fill'）也可能不带（home），值必须是 \uXXXX 转义。
      // 值限定成转义形式，才不会把 `text: '首页'` 这类条目也匹配进来。
      [...block[1].matchAll(/'?([a-z0-9-]+)'?:\s*'((?:\\u[0-9a-fA-F]{4})+)'/g)].map((m) => [
        m[1],
        unescapeGlyph(m[2]),
      ]),
    )
  })()

  const hex = (s: string) =>
    [...s].map((c) => 'U+' + c.codePointAt(0)!.toString(16).toUpperCase()).join(' ')

  it('本地码点与 uview-plus 的 icons.js 逐字一致', () => {
    expect(UV_GLYPHS.size, 'uview-plus 的字形表没解析出来，这条会空转').toBeGreaterThan(200)
    expect(localGlyphs.size, 'index.js 里没解析出 GLYPHS，这条会空转').toBeGreaterThanOrEqual(9)

    const bad: string[] = []
    for (const [name, glyph] of localGlyphs) {
      const real = UV_GLYPHS.get(name)
      if (real === undefined) {
        bad.push(`${name}: uview-plus 里没有这个图标名`)
      } else if (real !== glyph) {
        bad.push(`${name}: 本地 ${hex(glyph)} ≠ uview-plus ${hex(real)}`)
      }
    }
    expect(
      bad,
      '字形码点与 uview-plus 漂了，底栏图标会渲染成一片空白且没有任何报错：\n' + bad.join('\n'),
    ).toEqual([])
  })

  it('TABS 用到的每个图标名都在本地字形表里', () => {
    // GLYPHS[name] 取不到 → DISPLAY_TABS 里那个 glyph 是 undefined →
    // wxml 渲染成空串。因为 .tabbar__icon 有固定 height，看布局也正常，
    // 只有那一格没有图标。
    const js = readIfExists(join(ROOT, 'custom-tab-bar', 'index.js'))
    const names = new Set(
      [...js.matchAll(/\bicon(?:Active)?:\s*'([a-z0-9-]+)'/g)].map((m) => m[1]),
    )
    expect(names.size, '一个图标名都没扫到，正则或写法变了').toBeGreaterThanOrEqual(5)

    const missing = [...names].filter((n) => !localGlyphs.has(n))
    expect(
      missing,
      '这些图标名在 GLYPHS 里没有对应码点，底栏那一格会没有图标：\n' + missing.join('\n'),
    ).toEqual([])
  })

  it('码点写成 \\uXXXX 转义，文件里不出现字面 PUA 字符', () => {
    // 字面 PUA 字符在这个手写文件里既看不见，又容易被编辑器或工具链的
    // 编码转换弄坏 —— 弄坏之后同样是「图标没了、但没有报错」。
    const bad: string[] = []
    for (const file of ['index.js', 'index.wxml', 'index.wxss']) {
      const text = readIfExists(join(ROOT, 'custom-tab-bar', file))
      const pua = [...text].filter((c) => {
        const n = c.codePointAt(0)!
        return n >= 0xe000 && n <= 0xf8ff
      })
      if (pua.length) bad.push(`${file}: ${pua.length} 个`)
    }
    expect(bad, '这些文件里出现了字面字形字符，请写成 \\uXXXX 转义：\n' + bad.join('\n')).toEqual(
      [],
    )
  })

  it('底栏不引用 u-icon（它在这里收不到 props）', () => {
    // 这次故障的根因闸。一般规则：本目录是原样复制的，里面的 wxml 不是
    // uni-app 编译产物、发不出 u-p，所以任何编译过的组件在这里都收不到 props。
    // 真要在这个文件里用某个组件，先确认它不依赖 props（那时再放宽这条）。
    const wxml = readIfExists(join(ROOT, 'custom-tab-bar', 'index.wxml'))
    // 先去掉注释：讲解这件事的注释里就写着 `<u-icon>`，不剥会把注释当代码判。
    const code = wxml.replace(/<!--[\s\S]*?-->/g, '')
    expect(
      /<u-icon\b/.test(code),
      'wxml 里又出现了 <u-icon>：它的 props 走 u-p 通道，原生 wxml 传不进去，图标会是空白',
    ).toBe(false)

    const json = readIfExists(join(ROOT, 'custom-tab-bar', 'index.json'))
    const using = (JSON.parse(json || '{}').usingComponents ?? {}) as Record<string, string>
    expect(
      Object.keys(using).filter((k) => k === 'u-icon'),
      'index.json 里又声明了 u-icon —— 底栏拿不到它的 props',
    ).toEqual([])
  })
})

// ── 底栏的图标字体 ────────────────────────────────────────────────────────

/**
 * 图标字体只有两份来源，而**两份都到不了这个组件**：
 *
 *   1. app.wxss 里的 @font-face（来自 styles/uview-iconfont.scss）——
 *      自定义组件有样式隔离，app.wxss 的规则不作用于组件内部节点。
 *   2. uview-plus 运行时的 wx.loadFontFace({ global: true }) ——
 *      它只在 **u-icon 被实例化时**触发（u-icon 源码的 beforeCreate：
 *      `fontUtil.params.loaded || fontUtil.loadFont()`，vendor.js 里没有
 *      第二个调用点）。底栏已经没有任何 u-icon 了，没人替它注册。
 *
 * 2026-10-11 23:49 的开发者工具截图就是这两条同时成立的样子：
 * `.tabbar__icon` 的 44rpx 格子**占住了**（标签被推下去 44rpx，与 spec §6.2
 * 的 18+44+6 吻合），说明 class 与字号都生效，但格子里一点墨迹都没有 ——
 * PUA 码点在系统字体里没有字形，于是渲染成空。同一张图上页面里的 uview
 * 图标正常，因为那些地方有 u-icon，loadFontFace 被触发过。
 *
 * 所以底栏必须把 @font-face 写进**组件自己的**样式表。这一组用例守住两件事：
 * 字体确实在组件里注册了，且与页面用的那份是同一个文件。
 */
describe('底栏的图标字体', () => {
  const ICONFONT = join(ROOT, 'custom-tab-bar', 'iconfont.wxss')
  const UVIEW_SCSS = join(ROOT, 'styles', 'uview-iconfont.scss')

  /** 从一份样式源码里取出内联字体的 base64。 */
  function base64Of(css: string): string {
    return (css.match(/base64,([A-Za-z0-9+/=]+)/) ?? [])[1] ?? ''
  }

  it('底栏自带字体，且与 styles/uview-iconfont.scss 是同一份', () => {
    // 两处各存一份 base64 是无法避免的（组件必须有自己的一份），代价是
    // 可能漂：页面换了字形而底栏没换，表现是**底栏图标与页面图标不是同一套**，
    // 不报错。这里逐字比对，漂了就是 RED。
    const page = base64Of(readIfExists(UVIEW_SCSS))
    const bar = base64Of(readIfExists(ICONFONT))
    // 先证明上面那条不是空转：两份都真的解析出了字体
    expect(page.length, 'styles/uview-iconfont.scss 里没解析出 base64').toBeGreaterThan(10000)
    expect(bar, '底栏没有自带图标字体（custom-tab-bar/iconfont.wxss），或与页面那份不一致').toBe(page)
  })

  it('字体是 base64 内联的，不是远程 URL', () => {
    // 远程 URL 断网或域名没配就是空白方块 —— styles/uview-iconfont.scss
    // 顶部记着这个教训，底栏不该把它重新引进来。
    const css = readIfExists(ICONFONT)
    expect(css, 'custom-tab-bar/iconfont.wxss 不存在').not.toBe('')
    expect(
      /url\(\s*['"]?https?:/i.test(css),
      'iconfont.wxss 里出现了远程字体 URL：断网/域名没配就是空白方块',
    ).toBe(false)
  })

  it('index.wxss 把它 @import 进来，且 @import 是全文件第一行', () => {
    // CSS/WXSS 要求 @import 在所有规则之前；写在中间会被整条忽略，
    // 表现与「没写」完全一样 —— 又是那种没有报错的空白。
    // 这里断言的是**原始文本**就以 @import 开头，不先剥注释：按规范注释
    // 会先被剥掉、不影响 @import，但微信的 WXSS 编译器不保证这么做，
    // 所以干脆不给它这个机会。
    const wxss = readIfExists(join(ROOT, 'custom-tab-bar', 'index.wxss'))
    expect(
      wxss,
      'index.wxss 第一行不是 @import "./iconfont.wxss" —— 底栏的字体不会注册',
    ).toMatch(/^@import\s+["']\.\/iconfont\.wxss["']/)
  })

  it('@font-face 的 family 与 .tabbar__icon 用的是同一个名字', () => {
    // family 名对不上，@font-face 注册了也白注册，同样是静默空白。
    const family = (readIfExists(ICONFONT).match(/font-family:\s*['"]?([A-Za-z0-9_-]+)/) ?? [])[1]
    expect(family, 'iconfont.wxss 里没解析出 font-family').toBeTruthy()
    const wxss = readIfExists(join(ROOT, 'custom-tab-bar', 'index.wxss'))
    expect(
      wxss,
      `.tabbar__icon 用的 family 与字体文件不一致（字体是 ${family}）`,
    ).toContain(`font-family: ${family}`)
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
