import { describe, it, expect } from 'vitest'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { heroPaddingTop, NAV_BAR_HEIGHT } from '../index'

/**
 * 头图顶部的两件事：让开微信胶囊按钮，以及下拉越界时露出来的颜色。
 *
 * ── 胶囊按钮 ──────────────────────────────────────────────────────────
 *
 * 微信自己的胶囊按钮（··· 和 ◉）长在状态栏下面那条 44px 导航栏带里，
 * 它自己 87×32、在带内上下居中。头图（BrandHero）是自定义导航页面里的
 * 第一个元素，右上角一摆「登录 / 注册」白胶囊，两个白块就叠在一起。
 *
 * 2026-10-11 开发者工具实测（素材/index2.png 逐像素量的）：
 *   微信胶囊 y 38~69、登录胶囊 y 65~93 —— 上沿被盖住 4px，粘成一块。
 * 当时是 `statusBar + 20`。
 *
 * ── 下拉露出来的颜色 ──────────────────────────────────────────────────
 *
 * 页面内容被拖出边界（iOS 回弹）时，露出来的是**窗口背景色**，不是页面
 * 自己的 CSS 背景 —— wxss 里给 `page` 或 `.page` 上色都盖不到那一块。
 * 这份颜色由 pages.json 的 `backgroundColorTop` 决定，不设就用全局的
 * `backgroundColor`（#FFF8F0）。于是橙色的头图上方会顶出一条白边，
 * 越界越明显 —— 这就是「整个页面下拉时上方出现白色」。
 *
 * pages.json 是标准 JSON、不能写注释（tabbar.test.ts 里点过这一条），
 * 所以「为什么这 5 个页面要设成品牌橙」的来龙去脉只能记在这里。
 */

const ROOT = join(__dirname, '..', '..')

/**
 * 读文件，不存在就返回空串。
 *
 * 用 statSync + try/catch 而不是 existsSync：本项目的 node:fs 类型只暴露
 * readFileSync / readdirSync / statSync，写 existsSync 会让 `vue-tsc --noEmit`
 * 报 TS2305（tabbar.test.ts 顶部有同样的说明）。
 */
function readIfExists(path: string): string {
  try {
    statSync(path)
    return readFileSync(path, 'utf-8')
  } catch {
    return ''
  }
}

/** 微信胶囊按钮的尺寸（px）—— 官方给的 87×32，与实测一致。 */
const CAPSULE_HEIGHT = 32

/** 胶囊按钮下沿距页面顶部的距离（px）：在 44px 导航栏带里上下居中。 */
function capsuleBottom(statusBarHeight: number): number {
  return statusBarHeight + (NAV_BAR_HEIGHT - CAPSULE_HEIGHT) / 2 + CAPSULE_HEIGHT
}

// ── 行为：让位算式 ────────────────────────────────────────────────────────

describe('heroPaddingTop 让开胶囊按钮', () => {
  // 覆盖从小屏到刘海屏的状态栏高度，包括取不到时的兜底。
  const STATUS_BARS = [0, 20, 24, 32, 44, 47, 59]

  it('右上角有内容时，内容的顶边落在胶囊下沿之外', () => {
    for (const statusBar of STATUS_BARS) {
      const top = heroPaddingTop(statusBar, { showLogin: true })
      const bottom = capsuleBottom(statusBar || 20)
      expect(
        top,
        `状态栏 ${statusBar}px 时头图从 ${top}px 开始，胶囊下沿在 ${bottom}px —— 又压上了`,
      ).toBeGreaterThan(bottom)
    }
  })

  it('让开的是整条导航栏，留 6px 余量', () => {
    // 余量固定 6px（胶囊在带内居中留下的半格），不随机型变 —— 这才是
    // 「不管什么机型都不会贴住」的原因。
    for (const statusBar of STATUS_BARS) {
      const gap = heroPaddingTop(statusBar, { showLogin: true }) - capsuleBottom(statusBar || 20)
      expect(gap, `状态栏 ${statusBar}px 时余量是 ${gap}px，不是半格 6px`).toBe(6)
    }
  })

  it('右侧空着的页面不受影响（不然会白掉一大块）', () => {
    // 案例 / 商品页只有左边的品牌块，和右上角的胶囊不在一处。
    // 它们的紧凑间距是设计过的，不能被让位逻辑顺手改掉。
    expect(heroPaddingTop(20, { compact: true })).toBe(28)
    expect(heroPaddingTop(44, { compact: true })).toBe(52)
    expect(heroPaddingTop(20)).toBe(40)
    expect(heroPaddingTop(44)).toBe(64)
  })

  it('状态栏取不到时按 20 兜底，不会算出 0（内容顶到屏幕外）', () => {
    expect(heroPaddingTop(0, { showLogin: true })).toBe(20 + NAV_BAR_HEIGHT)
    expect(heroPaddingTop(NaN, { compact: true })).toBe(28)
  })
})

// ── 接线：组件真的用了这个算式 ────────────────────────────────────────────

describe('BrandHero 接了这套算法', () => {
  const hero = readIfExists(join(ROOT, 'components', 'BrandHero.vue'))

  it('文件读得到，且真的算了 padding-top', () => {
    // 防空转：读不到文件时下面的 toContain 会变成对空串的断言。
    expect(hero, 'src/components/BrandHero.vue 读不到').not.toBe('')
    expect(hero).toContain('paddingTop')
  })

  it('用的是 utils 的 heroPaddingTop，不是本地又写一遍算式', () => {
    // 本地重算一份就意味着两处会漂：改了 utils 的让位量，页面不跟着走。
    expect(hero, 'BrandHero 没有 import heroPaddingTop').toMatch(
      /import\s*\{[^}]*heroPaddingTop[^}]*\}\s*from\s*'\.\.\/utils'/,
    )
    expect(hero, 'BrandHero 里没有调用 heroPaddingTop').toMatch(/calcHeroPaddingTop\(|heroPaddingTop\(/)
  })

  it('把 showLogin / compact 两个开关都传下去了', () => {
    // showLogin 漏传 = 登录胶囊又压回微信胶囊上（就是这次修的 BUG）；
    // compact 漏传 = 案例/商品页凭空多出 24px 空白。
    // 用 indexOf + 截一段窗口，而不是写多行正则：调用是跨行的，
    // 正则里 `.*` 与花括号的边界很容易写得又长又脆。
    const at = hero.indexOf('calcHeroPaddingTop(')
    expect(at, '认不出 heroPaddingTop 的调用').toBeGreaterThan(-1)
    const call = hero.slice(at, at + 200)
    expect(call, 'showLogin 没传给 heroPaddingTop').toContain('showLogin')
    expect(call, 'compact 没传给 heroPaddingTop').toContain('compact')
  })
})

// ── pages.json：下拉越界露出来的颜色 ──────────────────────────────────────

describe('下拉越界区（backgroundColorTop）', () => {
  const pagesJson = readIfExists(join(ROOT, 'pages.json'))
  const parsed = JSON.parse(pagesJson || '{"pages":[]}') as {
    pages: { path: string; style?: Record<string, unknown> }[]
  }

  /**
   * theme.scss 里的 --color-primary。
   *
   * 先剥掉 `//` 行注释，再只认完整的十六进制值：theme.scss 的头部注释里
   * **引用**了 `:root{--color-primary:…}` 来讲那个坑（theme-tokens.test.ts
   * 顶部同样是这么处理的），不剥会解析到注释里的省略号。
   */
  const theme = readIfExists(join(ROOT, 'styles', 'theme.scss'))
    .split('\n')
    .filter((line) => !line.trim().startsWith('//'))
    .join('\n')
  const primary = (theme.match(/--color-primary\s*:\s*(#[0-9A-Fa-f]{6})/) ?? [])[1]

  const custom = parsed.pages.filter((p) => p.style?.navigationStyle === 'custom')
  const others = parsed.pages.filter((p) => p.style?.navigationStyle !== 'custom')

  it('解析出了页面清单和品牌色（防空转）', () => {
    expect(pagesJson, 'src/pages.json 读不到').not.toBe('')
    expect(parsed.pages.length, 'pages.json 里没解析出页面').toBeGreaterThan(15)
    expect(primary, 'theme.scss 里没解析出 --color-primary').toMatch(/^#[0-9A-Fa-f]{6}$/)
  })

  it('自定义导航的页面，顶部都是自己的橙色头图 —— 必须设 backgroundColorTop', () => {
    // 这 5 个页面顶部都是自己的橙色块（4 个头图 + 客服页的 chat-header），
    // 系统导航栏那条带也是这个橙色。不设 backgroundColorTop 就用全局的
    // #FFF8F0 —— 下拉越界时橙色上面顶出一条白边。
    expect(custom.length, '自定义导航的页面数变了，这条用例的依据要重新看').toBe(5)
    for (const page of custom) {
      expect(
        page.style?.backgroundColorTop,
        `${page.path} 是自定义导航（顶部橙色），但没设 backgroundColorTop —— 下拉会露出白色`,
      ).toBe(primary)
    }
  })

  it('系统导航栏的页面不许设（它们的顶部是 #FFF8F0，露出来本来就对）', () => {
    // 系统导航栏不透明、盖在内容之上，回弹区在它下面看不见；乱设成橙色
    // 只会在某些机型上露出半条橙边。
    const strays = others.filter((p) => p.style?.backgroundColorTop !== undefined)
    expect(strays.map((p) => p.path), '这些页面用了系统导航栏，不该设 backgroundColorTop').toEqual([])
  })
})
