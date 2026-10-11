import { describe, it, expect } from 'vitest'
import { readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

/**
 * 设计 token 的**声明位置**。
 *
 * ── 这条用例是为什么来的 ──────────────────────────────────────────
 *
 * 2026-10-11 第一次在微信开发者工具里打开 `dist/build/mp-weixin`，
 * 全站渲染成「像没加载样式」：头图没有橙色渐变、卡片没有圆角阴影、
 * 所有间距塌成 0、内容一直铺到底栏底下。逐层追下来的结论是：
 *
 *   `theme.scss` 把全部 token 声明在 `:root` 上，而 **WXSS 里 `:root`
 *   不落地**。编译产物 `app.wxss` 第一条确实是 `:root{--color-primary:…}`，
 *   它在文件里看得见，但运行时一个自定义属性都读不出来。
 *
 * 全站 18 个 wxss、约 500 处 `var(--…)` 因此同时失去颜色/圆角/间距。
 * 症状是「整屏无样式」而不是某一页错位 —— 这正是这份声明的
 * 「要么全好、要么全崩」形状（见 docs/superpowers/plans/
 * 2026-10-04-visual-regression-checklist.md 的「token 继承面」一节，
 * 当时已经推演出这个形状，只是没有开发者工具可以证实）。
 *
 * 一条佐证把根因锁死在「声明位置」上：全站**唯一渲染正常**的是自定义
 * 底栏，而它是唯一给每个 `var()` 都写了字面兜底值的文件
 * （`var(--tabbar-content-height, 114rpx)` 这种，见 custom-tab-bar/
 * index.wxss 顶部注释）。同一套 token、同一个运行时，写了兜底的活、
 * 没写兜底的全塌 —— 问题不在 `var()` 本身，在 token 没被声明出来。
 *
 * ── 守住的不变量 ──────────────────────────────────────────────────
 *
 * token 必须声明在 `page` 上。`page` 是 WXSS 里真实存在的页面根节点
 * （uni-app 自己注入的 `page{--status-bar-height:25px}` 用的就是它），
 * 自定义属性从 `page` 往下继承进各个自定义组件。
 *
 * `:root` 对应的 `<html>` 在小程序的样式体系里不构成可用的声明位置，
 * 写在那里等于没写。所以这条用例不检查「值对不对」（那是
 * tabbar.test.ts 那条比对兜底值的活），只检查「声明在哪儿」。
 */

const ROOT = join(__dirname, '..', '..')

/**
 * 读文件，不存在就返回空串。
 *
 * 用 statSync + try/catch 而不是 existsSync：本项目的 node:fs 类型只
 * 暴露了 readFileSync / readdirSync / statSync，写 existsSync 会让
 * `vue-tsc --noEmit` 报 TS2305（tabbar.test.ts 顶部有同样的说明）。
 */
function readIfExists(path: string): string {
  try {
    statSync(path)
    return readFileSync(path, 'utf-8')
  } catch {
    return ''
  }
}

/**
 * 先剥掉 `//` 行注释再解析。
 *
 * theme.scss 的头部注释里**引用**了 token 名（正是为了讲清这条约束的来历），
 * 不剥会把注释当规则解析出来，断言就指错地方了。
 */
const THEME = readIfExists(join(ROOT, 'styles', 'theme.scss'))
  .split('\n')
  .filter((line) => !line.trim().startsWith('//'))
  .join('\n')

/**
 * 取「声明了 `--color-primary` 的那条规则」的选择器文本。
 *
 * 从 `--color-primary:` 处往前找最近的 `{`，再往前找到最近的 `}`（或文件
 * 开头）—— 两者之间就是选择器。不整块 parse SCSS：theme.scss 里只有
 * `//` 注释、没有嵌套规则，够用且不引依赖。
 */
function tokenBlockSelector(css: string): string | null {
  const at = css.indexOf('--color-primary')
  if (at === -1) return null
  const open = css.lastIndexOf('{', at)
  if (open === -1) return null
  const close = css.lastIndexOf('}', open)
  return css
    .slice(close + 1, open)
    .split('\n')
    .filter((line) => !line.trim().startsWith('//')) // 文件头注释会跟着进来，去掉
    .join('\n')
    .trim()
}

describe('设计 token 的声明位置', () => {
  it('theme.scss 读得到，且确实声明了 token', () => {
    expect(THEME, 'src/styles/theme.scss 读不到').not.toBe('')
    const count = [...THEME.matchAll(/^\s*--[a-z0-9-]+\s*:/gm)].length
    // 防空转：正则或写法一变，下面几条会一起变成空断言。
    expect(count, 'theme.scss 里没解析出 token，下面的断言会空转').toBeGreaterThanOrEqual(40)
  })

  it('token 块声明在 page 上', () => {
    const selector = tokenBlockSelector(THEME)
    expect(selector, '认不出声明 --color-primary 的那条规则').not.toBeNull()
    expect(
      /\bpage\b/.test(selector!),
      `token 声明在 \`${selector}\` 上 —— WXSS 读不到 \`:root\`，` +
        '全站 500 处 var() 会一起失效，症状是整屏无样式。' +
        '声明到 `page` 上（小程序里真实存在的页面根节点）。',
    ).toBe(true)
  })

  it('只写 :root 不算数', () => {
    const selector = tokenBlockSelector(THEME)
    // 这条与上一条互补：上一条保证「有 page」，这条点名「不能只有 :root」，
    // 失败信息里直接给出这个错误选择，比上一条的泛化提示更好定位。
    expect(
      selector,
      'token 只声明在 `:root` 上。WXSS 里 `:root` 不构成可用的声明位置，' +
        '等于没声明 —— 2026-10-11 开发工具实测的就是这个形态。',
    ).not.toBe(':root')
  })
})
