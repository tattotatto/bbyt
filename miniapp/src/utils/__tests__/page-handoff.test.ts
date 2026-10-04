import { describe, it, expect } from 'vitest'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'

/**
 * 跨页契约：tabBar 页之间传不了 query。
 *
 * `switchTab` 会把 url 上的 query **静默丢掉**（点得动，参数没了），
 * `navigateTo` 又根本跳不到 tabBar 页。所以「首页点了某个分类 / 搜了某个
 * 关键词 → 商品页按它筛」这条链路只能靠 storage 中转。
 *
 * 这条链路有三种错法，**一种都不会报错**：
 *   - 生产者 key 写错或忘了写 → 点了没反应
 *   - 消费者 key 写错或没读   → 同上，而且看起来像是"数据就是这样"
 *   - 消费者读完不删          → 每次从 tabBar 切回来都被重新筛一遍
 *
 * 所以两端一起钉在这里。同理，读取必须发生在 `onShow` 而不是 `onLoad`：
 * 从 tabBar 切回来时页面还在页面栈上，`onLoad` 不会再触发一次 ——
 * 写错了症状是"第一次点分类生效，之后再点就没反应了"。
 */

const ROOT = join(__dirname, '..', '..')

/**
 * 读文件，不存在就返回空串。
 *
 * 用 statSync + try/catch 而不是 `existsSync`：本项目的 `node:fs` 类型
 * 只暴露 readFileSync / readdirSync / statSync 三个成员，写 existsSync
 * 会让 `vue-tsc --noEmit` 报 TS2305（同 tabbar.test.ts）。
 */
function readIfExists(path: string): string {
  try {
    statSync(path)
    return readFileSync(path, 'utf-8')
  } catch {
    return ''
  }
}

function collectSources(dir: string): string[] {
  const out: string[] = []
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry)
    if (statSync(full).isDirectory()) {
      out.push(...collectSources(full))
      continue
    }
    if (full.endsWith('.vue') || full.endsWith('.ts')) out.push(full)
  }
  return out
}

interface Handoff {
  key: string
  producer: string
  consumer: string
  how: string
}

const HANDOFFS: Handoff[] = [
  {
    key: 'products_pending_category',
    producer: 'pages/home/index.vue',
    consumer: 'pages/products/index.vue',
    how: '首页分类横滚 → 商品页按分类筛',
  },
  {
    key: 'products_pending_keyword',
    producer: 'pages/home/index.vue',
    consumer: 'pages/products/index.vue',
    how: '首页头图搜索 → 商品页按关键词筛',
  },
]

const page = (rel: string) => readIfExists(join(ROOT, rel))

/**
 * 取 `call(` 之后第一个 `{...}` 块的**内容**。
 *
 * 不用正则是故意的：块里有嵌套的 if / 对象字面量，
 * `/onShow\(\(\) => \{[\s\S]*?\}\s*\)/` 这类写法遇到嵌套大括号会提前收口，
 * 于是"读到了 onShow 里"变成一条时对时错的断言。
 */
function blockAfterCall(text: string, call: string): string | null {
  const at = text.indexOf(`${call}(`)
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

describe('跨页 storage 交接', () => {
  for (const { key, producer, consumer, how } of HANDOFFS) {
    describe(`${key}（${how}）`, () => {
      it('生产者写入了这个 key', () => {
        const text = page(producer)
        expect(text, `${producer} 读不到`).not.toBe('')
        expect(
          text.includes(`setStorageSync('${key}'`),
          `${producer} 没有写 '${key}' —— 通往商品页的这个入口是死的`,
        ).toBe(true)
      })

      it('消费者读取了这个 key', () => {
        const text = page(consumer)
        expect(text, `${consumer} 读不到`).not.toBe('')
        expect(
          text.includes(`getStorageSync('${key}'`),
          `${consumer} 没有读 '${key}' —— 生产者写了也没人接`,
        ).toBe(true)
      })

      it('消费者读完就删，否则每次从 tabBar 回来都被重新筛一遍', () => {
        const text = page(consumer)
        expect(
          text.includes(`removeStorageSync('${key}'`),
          `${consumer} 读了 '${key}' 却没删：下次再切回商品页会被同一个条件再筛一次，` +
            '而且用户没有任何办法把这个条件去掉',
        ).toBe(true)
      })

      it('读取在 onShow 里，不是 onLoad', () => {
        const text = page(consumer)
        const body = blockAfterCall(text, 'onShow')
        expect(body, `${consumer} 没有 onShow(() => {…})`).not.toBeNull()
        expect(
          body!.includes(`getStorageSync('${key}'`),
          `'${key}' 的读取不写在 onShow 里。从 tabBar 切回来时页面还在栈上，` +
            'onLoad 不会再触发 —— 症状是"第一次点分类生效，之后再点就没反应了"',
        ).toBe(true)
      })
    })
  }

  it('表里列全了源码里所有 products_pending_* 键，新加一个就会被这条拦住', () => {
    const found = new Set<string>()
    for (const file of collectSources(join(ROOT, 'pages'))) {
      for (const m of readIfExists(file).matchAll(/'(products_pending_[a-z_]+)'/g)) {
        found.add(m[1])
      }
    }
    expect(
      [...found].sort(),
      '源码里出现了上表没有登记的 products_pending_* 键：' +
        '请在 HANDOFFS 里补一行，把它的生产者/消费者一起钉住',
    ).toEqual(HANDOFFS.map((h) => h.key).sort())
  })
})
