import { describe, it, expect } from 'vitest'
import { readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

/**
 * 蓓贝客服页（pages/ai-assistant/index）的契约。
 *
 * 这个页面的状态在 `<script setup>` 里不导出，所以扫源码。扫的是四条
 * **不会报错**的规格要求 —— spec §5.4 的每一条改错了，页面看起来都"正常"：
 *
 *   1. 标题还叫「小暖AI」（spec §2 #8 要求改成「蓓贝客服」）
 *   2. 没有退出口 —— 这一页底栏是隐藏的，而 `switchTab` 不保留页面栈，
 *      用户点进来就出不去了，且没有任何报错
 *   3. 快捷问题自己另开一条发送路径 —— 发出去了，但漏了滚动/清空
 *   4. 气泡直角方向反了（spec §5.4 ②：客服左上直角、用户右上直角）
 *
 * 用 statSync + try/catch 而不是 `existsSync`：本项目的 `node:fs` 类型只暴露
 * readFileSync / readdirSync / statSync，写 existsSync 会让 `vue-tsc --noEmit`
 * 报 TS2305（同 tabbar.test.ts / page-handoff.test.ts）。
 */

const ROOT = join(__dirname, '..', '..')
const PAGE = 'pages/ai-assistant/index.vue'

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
 *
 * 不用正则是故意的：函数体里有嵌套的 if / 对象字面量，
 * `/function onSend\(\)[\s\S]*?\}/` 这类写法遇到嵌套大括号会提前收口，
 * 于是断言时对时错（同 page-handoff.test.ts / cases-page-contract.test.ts）。
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

describe('蓓贝客服页', () => {
  it('页面源码读得到（改名或挪走后这条先炸，免得下面几条假绿）', () => {
    expect(src(), `${PAGE} 读不到`).not.toBe('')
  })

  it('pages.json 里这一页的标题是「蓓贝客服」', () => {
    const cfg = JSON.parse(readIfExists(join(ROOT, 'pages.json')))
    const page = (cfg.pages ?? []).find(
      (p: { path: string }) => p.path === 'pages/ai-assistant/index',
    )
    expect(page, 'pages.json 里没有注册 pages/ai-assistant/index').toBeDefined()
    expect(
      page.style?.navigationBarTitleText,
      '标题还是旧的 —— spec §2 #8 要求「小暖AI」改成「蓓贝客服」',
    ).toBe('蓓贝客服')
  })

  it('页面自己给了退出口', () => {
    // 底栏在这一页按 spec §2 #12 隐藏，而 switchTab 会清空页面栈：
    // 聊天页是 tabBar 页，栈里永远只有它自己，左滑返回也无效。
    // 所以这个出口不是锦上添花，是用户唯一的出路 —— 少了它，
    // 点进客服页就出不来，而且没有任何报错。
    const text = src()
    expect(
      /switchTab\s*\(\s*\{[^}]*url:\s*['"]\/pages\/home\/index['"]/.test(text),
      '客服页没有回到 tabBar 页的出口。底栏在这一页隐藏，switchTab 又不留页面栈 —— ' +
        '用户会被困在聊天页里',
    ).toBe(true)
  })

  it('快捷问题与输入框走同一条发送路径', () => {
    const text = src()
    const onSend = blockAfter(text, 'function onSend')
    const sendQuick = blockAfter(text, 'function sendQuick')
    expect(onSend, '没有 onSend').not.toBeNull()
    expect(sendQuick, '没有 sendQuick（快捷问题 chips 的点击处理）').not.toBeNull()

    // 快捷问题不能自己另开一条发送路径
    expect(
      /sendMessage\s*\(/.test(sendQuick!),
      'sendQuick 自己调了 sendMessage —— 另开一条路径最容易漏掉滚动到底、清空输入这些配套，' +
        '漏了也只是"消息发出去了但没滚到最新一条"',
    ).toBe(false)

    // 两边必须共用一个「真正发送」的函数：把各自调用的函数名取出来求交集。
    // allowlist 里是一次性工具 —— 共用一个滚动工具不算共用发送逻辑。
    const callsOf = (body: string) =>
      new Set([...body.matchAll(/\b([A-Za-z_$][\w$]*)\s*\(/g)].map((m) => m[1]))
    const ALLOW = new Set(['scrollToBottom', 'nextTick', 'trim', 'setTimeout'])
    const shared = [...callsOf(onSend!)].filter(
      (n) => callsOf(sendQuick!).has(n) && !ALLOW.has(n),
    )
    expect(
      shared,
      'onSend 与 sendQuick 没有共用的发送函数 —— 两条路径早晚会漂',
    ).not.toEqual([])
  })

  it('快捷问题取自 DEMO_QUICK_QUESTIONS', () => {
    expect(
      src().includes('DEMO_QUICK_QUESTIONS'),
      '没有用 Task 9 产出的 DEMO_QUICK_QUESTIONS',
    ).toBe(true)
  })

  it('气泡的直角方向对：客服左上、用户右上', () => {
    // spec §5.4 ②。border-radius 四角顺序是 上左 / 上右 / 下右 / 下左。
    const style = src().slice(src().indexOf('<style'))
    const radiusOf = (cls: string) => {
      const at = style.indexOf(`.${cls} {`)
      expect(at, `样式里没有 .${cls}`).toBeGreaterThanOrEqual(0)
      const m = style.slice(at).match(/border-radius:\s*([^;]+);/)
      expect(m, `.${cls} 没有 border-radius`).not.toBeNull()
      return m![1].trim().split(/\s+/)
    }

    const agent = radiusOf('chat-bubble--ai')
    expect(agent[0], '客服气泡的左上角应当是直角（0）').toBe('0')
    expect(agent[1], '客服气泡的上右角不应当是直角').not.toBe('0')

    const user = radiusOf('chat-bubble--user')
    expect(user[0], '用户气泡的左上角不应当是直角').not.toBe('0')
    expect(user[1], '用户气泡的右上角应当是直角（0）').toBe('0')
  })

  it('页面里不再有 emoji（都换成了 AppIcon）', () => {
    const text = src()
    const found = ['☀', '💬', '⚠', '🏷', '🛒', '✅', '📦', '🎨'].filter((e) =>
      text.includes(e),
    )
    expect(
      found,
      '这些 emoji 还在页面里。B2B 母婴场景下 emoji 跨机型字形差异明显，' +
        'brief Step 3 要求全部换成 AppIcon',
    ).toEqual([])
  })
})
