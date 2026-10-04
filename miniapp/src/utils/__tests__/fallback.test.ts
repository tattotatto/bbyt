import { describe, it, expect, vi, afterEach } from 'vitest'
import { readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
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

  // 「请求失败时不兜底」这一半**不在这里测**：它取决于调用方把 applyFallback
  // 放在 try 里还是 catch 里，而这个文件之前用一段本地重写的 page() 去"证明"它 ——
  // 那段代码根本不碰真实页面，三个页面哪天全把 catch 删掉也照样绿。
  // 真正钉住它的是文件末尾对 pages/**/*.vue 的结构扫描。
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

// ── 调用方：兜底只能在成功分支 ────────────────────────────────────────────
// 这一段和上面的纯函数用例互补。上面证明 `applyFallback` 本身"只在空集合时
// 替换"；下面证明**调用方**没有把它写进 catch —— 写进 catch 的话，请求失败
// 会被演示数据盖住，线上真故障看起来像"只是没数据"，这是本模块存在的主要风险。

const ROOT = join(__dirname, '..', '..')
const readPage = (rel: string) => {
  try {
    statSync(join(ROOT, rel))
    return readFileSync(join(ROOT, rel), 'utf-8')
  } catch {
    return ''
  }
}

/**
 * 取出所有 catch 块的**内容**（大括号配对，不吃嵌套）。
 *
 * 不用正则是故意的：catch 块里有嵌套的 if / 对象字面量，
 * `/catch[^{]*\{[\s\S]*?\}/` 会在第一个 `}` 就收口，断言看着绿、其实只看了一行。
 */
function catchBlocks(text: string): string[] {
  const out: string[] = []
  const re = /\bcatch\b/g
  let m: RegExpExecArray | null
  while ((m = re.exec(text))) {
    let i = m.index + 'catch'.length
    while (i < text.length && /\s/.test(text[i])) i++
    if (text[i] === '(') {
      let d = 0
      for (; i < text.length; i++) {
        if (text[i] === '(') d++
        else if (text[i] === ')') {
          d--
          if (d === 0) {
            i++
            break
          }
        }
      }
    }
    while (i < text.length && text[i] !== '{') i++
    if (i >= text.length) break
    let d = 0
    const start = i
    for (; i < text.length; i++) {
      if (text[i] === '{') d++
      else if (text[i] === '}') {
        d--
        if (d === 0) {
          out.push(text.slice(start + 1, i))
          break
        }
      }
    }
  }
  return out
}

/** 用了演示数据兜底的页面。 */
const FALLBACK_PAGES = ['pages/home/index.vue', 'pages/cases/index.vue']

describe('调用方把兜底写在成功分支，不写进 catch', () => {
  for (const rel of FALLBACK_PAGES) {
    it(`${rel}：catch 里没有 applyFallback`, () => {
      const text = readPage(rel)
      expect(text, `${rel} 读不到`).not.toBe('')

      // 先证明真的看到了调用点 —— 否则下面那条会在"页面里根本没有兜底"时
      // 也通过（空集合断言是死断言）。
      expect(
        text.includes('applyFallback'),
        `${rel} 里没有 applyFallback：要么兜底被删了，要么改用了别的写法`,
      ).toBe(true)

      const blocks = catchBlocks(text)
      expect(blocks.length, `${rel} 里一个 catch 块都没解析到 —— 解析器失灵了`).toBeGreaterThan(
        0,
      )

      const leaked = blocks.filter((b) => b.includes('applyFallback'))
      expect(
        leaked,
        `${rel} 在 catch 里调了 applyFallback。请求失败会被演示数据盖住 ——\n` +
          '线上真故障看起来像"只是没有数据"，错误态永远不出现。',
      ).toEqual([])
    })
  }
})
