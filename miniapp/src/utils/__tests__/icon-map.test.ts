import { describe, it, expect } from 'vitest'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { EMOJI_TO_ICON, iconForEmoji } from '../icon-map'

// 与统计口径一致：只认象形 emoji 区段，排除箭头(→)、✓、›、★ 之类的装饰字符。
// 统计口径变了这里要同步改，否则测试会因为多认了几个符号而误报。
const EMOJI_RANGES: [number, number][] = [
  [0x1f300, 0x1faff],
  [0x1f000, 0x1f2ff],
]
const SKIP = new Set(['️', '‍'])   // 变体选择符、零宽连接符

function isEmoji(ch: string): boolean {
  const cp = ch.codePointAt(0)!
  return EMOJI_RANGES.some(([a, b]) => cp >= a && cp <= b)
}

function collectEmoji(root: string): Map<string, string[]> {
  const found = new Map<string, string[]>()
  const walk = (dir: string) => {
    for (const entry of readdirSync(dir)) {
      const full = join(dir, entry)
      if (statSync(full).isDirectory()) { walk(full); continue }
      if (!full.endsWith('.vue')) continue
      const text = readFileSync(full, 'utf-8')
      for (const ch of text) {
        if (SKIP.has(ch) || !isEmoji(ch)) continue
        if (!found.has(ch)) found.set(ch, [])
        const files = found.get(ch)!
        if (!files.includes(full)) files.push(full)
      }
    }
  }
  walk(root)
  return found
}

describe('icon-map 覆盖度', () => {
  it('源码里出现的每一个 emoji 都有对应图标', () => {
    const found = collectEmoji(join(__dirname, '..', '..'))
    const missing = [...found.keys()].filter((e) => !(e in EMOJI_TO_ICON))
    expect(
      missing,
      `这 ${missing.length} 个 emoji 没有映射，页面上会漏改回落到 emoji：\n` +
        missing.map((e) => `  ${e} U+${e.codePointAt(0)!.toString(16).toUpperCase()} ` +
          `出现在 ${found.get(e)!.join(', ')}`).join('\n'),
    ).toEqual([])
  })

  it('映射到的图标名都在 uview-plus 图标集里', () => {
    const iconsSrc = readFileSync(
      join(__dirname, '..', '..', '..', 'node_modules', 'uview-plus',
           'components', 'u-icon', 'icons.js'),
      'utf-8',
    )
    const available = new Set(
      [...iconsSrc.matchAll(/'uicon-([a-z0-9-]+)':/g)].map((m) => m[1]),
    )
    expect(available.size).toBeGreaterThan(200)   // 图标集没被解析出来就冒烟

    const bad = Object.entries(EMOJI_TO_ICON)
      .filter(([, icon]) => !available.has(icon))
      .map(([e, icon]) => `${e} -> "${icon}"（uview-plus 里没有这个名）`)
    expect(bad).toEqual([])
  })

  it('映射表没有重复的图标名', () => {
    // 同一个图标服务两个不同语义的 emoji 说明有一处选错了
    const counts = new Map<string, string[]>()
    for (const [emoji, icon] of Object.entries(EMOJI_TO_ICON)) {
      if (!counts.has(icon)) counts.set(icon, [])
      counts.get(icon)!.push(emoji)
    }
    const dupes = [...counts.entries()]
      .filter(([, list]) => list.length > 1)
      .map(([icon, list]) => `${icon} 被 ${list.join(' ')} 共用`)
    expect(dupes).toEqual([])
  })

  // 前面两条只管映射表。但页面模板里也会直接写图标名
  // （<AppIcon name="home-fill" />、tabBar 的图标数组、菜单项数组），
  // 写错一个不会有任何编译错误，真机上只是一块空白 —— 这条把它们也扫了。
  //
  // 注意这条是 **lint，不是证明**：正则匹配证明不了数据流真的流进 <u-icon>。
  // 为了不把噪声当信号，它只扫「会渲染图标的文件」，并跳过 uni API 自带的
  // icon 取值。两处限定各自的理由见下，它们排掉的都不是漏改的图标名。
  it('模板里直接写死的图标名也都存在', () => {
    const iconsSrc = readFileSync(
      join(__dirname, '..', '..', '..', 'node_modules', 'uview-plus',
           'components', 'u-icon', 'icons.js'),
      'utf-8',
    )
    const available = new Set(
      [...iconsSrc.matchAll(/'uicon-([a-z0-9-]+)':/g)].map((m) => m[1]),
    )

    // uni.showToast / showModal 等 API 的 icon 选项（'none' | 'success' | ...），
    // 与 uview 图标集是两套互不相干的词汇表。不排掉的话，全项目 70 多处
    // uni.showToast({ icon: 'none' }) 会全部被误报成「图标名不存在」。
    const UNI_API_ICON_TYPES = new Set([
      'none', 'success', 'error', 'loading', 'fail', 'warn', 'info', 'exception',
    ])

    const root = join(__dirname, '..', '..')
    const bad: string[] = []
    const walk = (dir: string) => {
      for (const entry of readdirSync(dir)) {
        const full = join(dir, entry)
        if (statSync(full).isDirectory()) {
          // 跳过测试目录：本文件自己的正则字面量和断言消息里就写着
          // `name="xxx"` / `icon: 'xxx'`，扫自己必然自伤。
          if (entry === '__tests__') continue
          walk(full)
          continue
        }
        if (!full.endsWith('.vue') && !full.endsWith('.ts')) continue
        const text = readFileSync(full, 'utf-8')

        // 文件不渲染图标，其 icon 字段就不是图标名 —— 只是同名的普通数据。
        // 已核实的两个例子：CertBadge.vue 声明了 `icon` prop 却从未在模板里用；
        // constants.ts 的 SAFETY_CERTS / PAYMENT_METHODS 全仓库零消费者。
        // 它们的取值（'shield' / 'wechat-fill' / 'alipay'）在 uview 里确实不存在，
        // 但既然从不渲染，就不是本用例要抓的漏改。
        if (!text.includes('AppIcon')) continue

        // ① <AppIcon name="xxx" /> —— 静态属性
        //    （:name="expr" 是动态绑定，值来自本映射表，上面已覆盖）
        for (const m of text.matchAll(/<AppIcon\b[^>]*?\bname="([^"]+)"/g)) {
          if (!available.has(m[1])) bad.push(`${full}: <AppIcon name="${m[1]}">`)
        }

        // ② 图标清单里的 icon: 'xxx' / iconActive: 'xxx'
        for (const m of text.matchAll(/\bicon(?:Active)?:\s*'([a-z0-9-]+)'/g)) {
          if (UNI_API_ICON_TYPES.has(m[1])) continue
          if (!available.has(m[1])) bad.push(`${full}: icon: '${m[1]}'`)
        }

        // ③ 图标名数组常量，如首页的 CATEGORY_ICONS = ['bag', 'coupon', ...]
        for (const arr of text.matchAll(/\b[A-Z][A-Z_]*ICONS\s*=\s*\[([^\]]*)\]/g)) {
          for (const s of arr[1].matchAll(/'([a-z0-9-]+)'/g)) {
            if (!available.has(s[1])) bad.push(`${full}: ICONS 数组里的 '${s[1]}'`)
          }
        }
      }
    }
    walk(root)

    expect(bad, '这些图标名在 uview-plus 里不存在，真机上会渲染成空白：\n' +
      bad.join('\n')).toEqual([])
  })
})

describe('iconForEmoji', () => {
  it('查得到时返回对应图标名', () => {
    expect(iconForEmoji('🛒')).toBe('shopping-cart')
  })

  it('查不到时返回兜底图标，而不是原样返回 emoji', () => {
    expect(iconForEmoji('🦄')).toBe('more-circle')
    expect(iconForEmoji('🦄', 'info')).toBe('info')
  })
})
