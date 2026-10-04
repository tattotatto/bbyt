import { describe, it, expect } from 'vitest'
import { readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

/**
 * 案例页的筛选取数契约。
 *
 * 页面本身没有单元测试的入口（`<script setup>` 里的状态不导出），所以这里
 * 扫源码。扫的不是「代码长什么样」，而是**三种不会报错的失效**：
 *
 *   1. 参数名漂移：把选中值写进 `params.style_tag` 而不是 `params.style`。
 *      后端不认识的 query 参数会被 FastAPI 直接忽略 —— 请求 200，列表照旧，
 *      点 chip 没反应，控制台干净。
 *   2. 「全部」chip 点不亮：chips 用 `undefined` 表示「全部」，而 active 状态
 *      存的是 `''`，`'' === undefined` 恒假 —— 那一格永远不高亮。
 *   3. 分页也走演示兜底：空结果被整份演示列表替换，而不是追加 0 条，
 *      「加载更多」于是无限重复同一批案例。
 *
 * 用 statSync + try/catch 而不是 `existsSync`：本项目的 `node:fs` 类型只暴露
 * readFileSync / readdirSync / statSync，写 existsSync 会让 `vue-tsc --noEmit`
 * 报 TS2305（同 tabbar.test.ts / page-handoff.test.ts）。
 */

const ROOT = join(__dirname, '..', '..')

function readIfExists(path: string): string {
  try {
    statSync(path)
    return readFileSync(path, 'utf-8')
  } catch {
    return ''
  }
}

const src = () => readIfExists(join(ROOT, 'pages/cases/index.vue'))

/**
 * 从 `marker` 之后的第一个 `{` 开始，返回配对括号内的块内容。
 *
 * 不用正则是故意的：块里有嵌套的 if / 对象字面量，
 * `/if \(x\) \{[\s\S]*?\}/` 这类写法遇到嵌套大括号会提前收口，
 * 于是「在这一支里」变成一条时对时错的断言（同 page-handoff.test.ts）。
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

/** `marker` 那一支以及紧随的 `else` 支（没有 else 就是 null）。 */
function ifElseBranches(
  text: string,
  marker: string,
): { then: string; else: string | null } | null {
  const at = text.indexOf(marker)
  if (at < 0) return null
  const open = text.indexOf('{', at)
  if (open < 0) return null

  let depth = 0
  let close = -1
  for (let i = open; i < text.length; i++) {
    if (text[i] === '{') depth++
    else if (text[i] === '}') {
      depth--
      if (depth === 0) {
        close = i
        break
      }
    }
  }
  if (close < 0) return null

  const then = text.slice(open + 1, close)
  const rest = text.slice(close + 1)
  const m = rest.match(/^\s*else\s*\{/)
  if (!m) return { then, else: null }

  const eOpen = close + 1 + m[0].length - 1
  depth = 0
  for (let i = eOpen; i < text.length; i++) {
    if (text[i] === '{') depth++
    else if (text[i] === '}') {
      depth--
      if (depth === 0) return { then, else: text.slice(eOpen + 1, i) }
    }
  }
  return { then, else: null }
}

describe('案例页筛选契约', () => {
  it('页面源码读得到（改名或挪走后这条先炸，免得下面几条假绿）', () => {
    expect(src(), 'pages/cases/index.vue 读不到').not.toBe('')
  })

  // ── 参数名漂移 ────────────────────────────────────────
  // 后端 app/api/cases.py 的 list_cases 收的是 style / area / category_tag。
  // 多写一个它不认识的名字，FastAPI 直接忽略，请求照样 200。
  describe('筛选项真的送到后端', () => {
    /**
     * `loadCases` 的整个函数体。
     *
     * 不能只取 `const params: CaseListParams = {…}` 那一行 —— 那些
     * `params.style = …` 是**独立的语句**，不在那个对象字面量的括号里，
     * 按字面量取到的块永远不含参数名，断言就成了永远为真的死断言。
     * （这条是变异测试发现的：把 style 改成 style_tag，它没红。）
     */
    const loadCasesBody = () => {
      const body = blockAfter(src(), 'async function loadCases')
      expect(body, '没找到 `async function loadCases`').not.toBeNull()
      return body!
    }

    it('风格写进 params.style', () => {
      expect(
        loadCasesBody().includes('params.style = '),
        '没有把选中的风格写进 params.style —— 后端 Query 参数就叫 style',
      ).toBe(true)
    })

    it('类型写进 params.category_tag', () => {
      expect(
        loadCasesBody().includes('params.category_tag = '),
        '没有把选中的类型写进 params.category_tag —— 后端 Query 参数就叫 category_tag',
      ).toBe(true)
    })

    it('params 里不出现 style_tag —— 那是被后端静默忽略的名字', () => {
      // 只看 loadCases，不看整个文件：`res.data.style_tags` 是标签接口
      // 合法的**响应**字段（CaseTags 里就是这么声明的），和这里的**请求**
      // 参数名是两回事，一起禁会把对的东西也判错。
      expect(
        loadCasesBody().includes('style_tag'),
        'params 里出现了 style_tag：后端 list_cases 没有这个参数，FastAPI 会忽略它，' +
          '症状是点 chip 列表不动、控制台没有报错',
      ).toBe(false)
    })

    it('分页响应取 res.data.items，不是 res.data.list', () => {
      const text = src()
      expect(
        text.includes('res.data.items'),
        '没有读 res.data.items —— 分页响应的字段是 items（api/cases.ts 里记着这件事）',
      ).toBe(true)
      expect(
        text.includes('res.data.list'),
        '读了 res.data.list：契约里是 items，写 list 会静默拿到 undefined，' +
          '列表恒空而没有任何报错',
      ).toBe(false)
    })
  })

  // ── 「全部」chip 的选中态 ──────────────────────────────
  describe('「全部」chip 能被点亮', () => {
    it('chips 里「全部」那一项的值是 undefined', () => {
      const text = src()
      expect(
        /label:\s*'全部'[\s\S]{0,60}?value:\s*undefined|value:\s*undefined[\s\S]{0,60}?label:\s*'全部'/.test(
          text,
        ),
        '「全部」chip 的 value 不是 undefined。它和 active 状态必须用同一个值，' +
          '否则空串与 undefined 相比恒不相等，那一格永远不高亮',
      ).toBe(true)
    })

    it('active 标签的初值与类型都是 undefined', () => {
      const text = src()
      expect(
        /activeCategoryTag\s*=\s*ref<string\s*\|\s*undefined>\(\s*undefined\s*\)/.test(text),
        'activeCategoryTag 的初值不是 undefined —— 进页面时「全部」应当是高亮的',
      ).toBe(true)
      expect(
        /activeStyleTag\s*=\s*ref<string\s*\|\s*undefined>\(\s*undefined\s*\)/.test(text),
        'activeStyleTag 的初值不是 undefined —— 进页面时「全部风格」应当是高亮的',
      ).toBe(true)
    })

    it('选中处理函数原样透传，不把 undefined 折成空串', () => {
      const text = src()
      const body = blockAfter(text, 'function onCategoryTagSelect')
      expect(body, '没有 onCategoryTagSelect').not.toBeNull()
      expect(
        body!.includes('activeCategoryTag.value = value'),
        'onCategoryTagSelect 没有把选中的值原样存进 activeCategoryTag',
      ).toBe(true)
      expect(
        body!.includes("?? ''"),
        "onCategoryTagSelect 把 undefined 折成了空串 —— 「全部」chip 会因此永远不高亮",
      ).toBe(false)
    })
  })

  // ── 演示兜底只在第一页 ────────────────────────────────
  describe('演示数据兜底', () => {
    it('只在第一页那一支兜底，分页追加不兜底', () => {
      const text = src()
      expect(text.includes('applyFallback'), '页面没有接演示数据兜底').toBe(true)

      const branches = ifElseBranches(text, 'if (isRefresh || page.value === 1)')
      expect(branches, '没找到「第一页 / 分页追加」这个分支').not.toBeNull()
      expect(
        branches!.then.includes('applyFallback'),
        '第一页没走兜底 —— 后端没数据时页面会只剩空状态',
      ).toBe(true)
      expect(branches!.else, '没有 else 支（分页追加）').not.toBeNull()
      expect(
        branches!.else!.includes('applyFallback'),
        '分页追加也走了兜底：空结果会被替换成整份演示列表而不是追加 0 条，' +
          '「加载更多」会无限重复同一批案例',
      ).toBe(false)
    })
  })
})
