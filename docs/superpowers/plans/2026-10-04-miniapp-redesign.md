# 小程序视觉改版 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用「品牌色头图 + 悬浮白卡 + 分区大标题 + 满宽横图卡 + 凸起圆 tabBar」这套布局语言重建 5 个 tab 主页面，并把全站图标从 emoji 换成统一的图标字体。

**Architecture:** 设计系统先行，自下而上四层：**token 层**（`theme.scss` 重校准圆角/阴影/新增色板）→ **组件层**（8 个新建 + 5 个改造）→ **外壳层**（自定义 tabBar、演示数据兜底）→ **页面层**（5 个 tab 页）。后续 15 个子页面可以直接复用组件层。图标走 uview-plus 的 `u-icon`，字体 base64 内联——**这是阻塞项，Task 1 必须先过**。

**Tech Stack:** uni-app + Vue 3 + TypeScript + Pinia + uview-plus 3.1，目标平台 `mp-weixin`；测试用 vitest（`environment: 'node'`，只覆盖 `utils/`、`api/`、`stores/`）。

**Spec:** `docs/superpowers/specs/2026-10-04-miniapp-redesign-design.md` — §3 设计语言、§4 组件、§5 页面、§6 tabBar、§7 图标、§8 空状态与演示数据。

**前置依赖：** 本计划假设 `docs/superpowers/plans/2026-10-04-backend-foundation-repair.md` 已完成（案例筛选契约、`/promotions/active` 可用、有种子数据）。若尚未完成，Task 12（案例页）和 Task 10（首页）无法在真机上看到真实数据——但样式开发不受阻，可以用 §Task 9 的演示数据推进。

## Global Constraints

- **品牌主色 `#e16531` 不变。** 只借素材的布局，不借配色。
- 单位统一用 **rpx**。`750rpx = 屏宽`。现有 `theme.scss` 的圆角/阴影写的是 px，本次改为 rpx —— 这是**语义变更**，不是数值微调。
- 前端测试命令：`cd miniapp && npm test`
- 类型检查命令：`cd miniapp && npx vue-tsc --noEmit`
- 新建前端测试文件必须落在 `src/utils/__tests__/`、`src/api/__tests__/` 或 `src/stores/__tests__/` 下，否则 `vitest.config.ts` 的 `include` 不会收集它。
- **没有组件测试环境**（无 `@vue/test-utils` + jsdom）。本次**不引入**。所有 `*.vue` 的验证方式是在微信开发者工具里看，不是单测。
- `EmptyState.vue`（15 个页面引用）和 `PageLoading.vue`（13 个页面引用）的 **props 接口必须保持向后兼容**，否则会波范围外的 15 个子页面。
- **不新增任何依赖。**
- **既有卡片的组件接口（已核实，不要凭印象写）：**
  - `ProductCard`：prop **`product`**，可选 `showStock`；emit **`click: [id: string]`**。所以是 `:product="p" @click="goToProduct"`——`goToProduct` 直接收 id。
  - `CaseCard`：prop **`caseData`**（**不是** `caseItem` / `item` / `data`）；emit **`click: [id]`**。
  - 两者都**不是** `@tap`。`@tap` 是原生元素的事件，组件上的 `click` 监听不到。
  - 本次新建的组件（`SurfaceCard` 等）用 `@tap` 是因为它们自己 `defineEmits` 的是 `tap`；改造既有卡片时**不要**顺手把 `click` 改成 `tap`。
- 本计划**不做**：15 个子页面、积分抽奖、任何业务逻辑变更（除客服页不显示底栏外，页面行为保持现状）。

## Review Focus

Spec 是愿景文档，以下六类它没有逐条写明，但最可能在真机上咬人。每一条都配了对应的验证。

**关于「验证」的形式：** 本项目**没有组件测试环境**（无 `@vue/test-utils` + jsdom），本次也不引入。所以下面除了第 5 条是真正的单测，其余几条的验证是**在微信开发者工具/真机上按具体步骤逐项确认**——不是「看一眼」，是列出要确认的现象。这也意味着计划里的每个页面任务都必须真的打开开发者工具跑一遍，不能只靠 `vue-tsc` 过。

1. **图标字体在真机上不显示** —— 微信小程序 wxss 不支持远程 `@font-face`。若 Task 1 的验证不通过而直接铺开，全站图标会变成空白方块（emoji 已删，图标没出来，比改版前更差）。**Task 1 是唯一的阻塞门。** 验证：真机扫码（模拟器不算），确认三个图标可见。
2. **主题圆角 token 影响范围外的 15 个子页面** —— `--radius-lg` 从 `20px` 改成 `28rpx` 是全站生效的。子页面可能出现压字、错位、圆角吃掉内容。验证：Task 15 逐页走完 20 个页面。
3. **自定义 tabBar 后各页底部留白不足** —— 页面不再自动预留底栏高度，最后一行内容会被凸起圆和底栏盖住。统一用 `.has-custom-tabbar` 的 `calc()` 公式，不允许写死数值。验证：4 个显示底栏的页面各滚到底，确认最后一行可见；真机上再看一次（`env(safe-area-inset-bottom)` 只在真机有非零值）。
4. **横滑区与纵向滚动抢手势** —— `scroll-view scroll-x` 嵌在纵向滚动页里。验证：真机上在推荐/分类/案例横滑区上斜向滑动，确认横滑优先且页面不跟着抖；并确认第二张卡片露边（「还有更多」的天然提示）。
5. **接口返回空集合 vs 请求失败** —— 演示数据只在**空集合**时兜底，**请求失败时不兜底**（保持错误态可见，不掩盖真实故障）。这个判定是纯函数，Task 9 用单测钉死；写反了会让线上故障被假数据盖住。
6. **跳 tabBar 页用了 `navigateTo`** —— 微信里 `navigateTo` 跳 tabBar 页会**静默失败**（不报错、不跳转、点了没反应）。这是既有代码里的真实 bug：首页的 `goToCategory` 就是这么写的。spec 没提，但新首页把分类横滚做成主入口会立刻暴露它。验证：Task 10/11 改成 `switchTab` + storage 传参；点一个分类，确认真的跳到商品页且分类已选中。

---

### Task 1: u-icon 字体内联 + `AppIcon` 组件（**阻塞门**）

Spec §7.1 实测：项目**当前没有使用任何 `u-` 组件**——uview-plus 装了、`main.ts:8` 注册了、`pages.json` 配了 easycom，但从没用起来。`u-icon` 的字体走远程 ttf `https://at.alicdn.com/t/font_2225171_8kdcwk4po24.ttf`（55,940 字节），而**微信小程序 wxss 不支持远程 `@font-face`**。直接上手写 `u-icon` 大概率在真机上显示成空白方块。

**在验证通过前，不要动任何页面的 emoji。**

**Files:**
- Create: `miniapp/src/styles/uview-iconfont.scss`
- Create: `miniapp/src/components/AppIcon.vue`
- Modify: `miniapp/src/App.vue`（`<style lang="scss">` 里加一行 import）
- Reference（只读）: `miniapp/node_modules/uview-plus/components/u-icon/icons.js`（212 个图标名与码点）

**Interfaces:**
- Consumes: 无
- Produces:
  - `AppIcon.vue` 的 props：`name?: string`（u-icon 名，**不带 `uicon-` 前缀**，如 `shopping-cart`）、`emoji?: string`（Task 2 的映射表未接入前先留接口，本任务只透传）、`size?: number | string`（rpx 数字，默认 `32`）、`tone?: 'primary' | 'ink' | 'muted' | 'white' | 'inherit'`（默认 `'inherit'`）、`bold?: boolean`
  - 全站统一从这里出图标。**页面不直接写 `<u-icon>`。**

- [ ] **Step 1: 下载字体并转 base64**

```bash
cd miniapp
mkdir -p src/styles
curl -fsSL -o /tmp/uview-iconfont.ttf \
  https://at.alicdn.com/t/font_2225171_8kdcwk4po24.ttf
ls -l /tmp/uview-iconfont.ttf    # 预期约 55940 字节
base64 -w0 /tmp/uview-iconfont.ttf > /tmp/uview-iconfont.b64
wc -c /tmp/uview-iconfont.b64    # 预期约 74,600 字节
```

若 `curl` 失败（网络或域名不可达），**停下来**并在微信后台把 `at.alicdn.com` 加入 downloadFile 白名单后重试；不要跳到 Step 6 的回退方案，先确认拿得到字体文件。

- [ ] **Step 2: 生成样式文件**

```bash
cd miniapp
{
  printf '%s\n' '// uview-plus u-icon 图标字体 —— base64 内联版'
  printf '%s\n' '//'
  printf '%s\n' '// 为什么内联：微信小程序 wxss 不支持远程 @font-face，'
  printf '%s\n' '// uview-plus 自带的 @font-face 指向 https://at.alicdn.com/...，'
  printf '%s\n' '// 真机上字体会加载失败，图标显示成空白方块。'
  printf '%s\n' '//'
  printf '%s\n' '// 原始 ttf 55,940 字节 → base64 约 74KB。主包上限 2MB，可接受。'
  printf '%s\n' '//'
  printf '%s\n' '// 重新生成：见 docs/superpowers/plans/2026-10-04-miniapp-redesign.md Task 1 Step 1-2'
  printf '\n'
  printf '%s\n' "@font-face {"
  printf '%s\n' "  font-family: 'uicon-iconfont';"
  printf "  src: url('data:font/truetype;charset=utf-8;base64,"
  cat /tmp/uview-iconfont.b64
  printf "%s\n" "') format('truetype');"
  printf '%s\n' "  font-weight: normal;"
  printf '%s\n' "  font-style: normal;"
  printf '%s\n' "  font-display: swap;"
  printf '%s\n' "}"
} > src/styles/uview-iconfont.scss
wc -c src/styles/uview-iconfont.scss   # 预期约 75KB
head -c 300 src/styles/uview-iconfont.scss
```

- [ ] **Step 3: 在 `App.vue` 挂上**

改 `miniapp/src/App.vue` 的 `<style lang="scss">` 块，在既有 import 之后加一行：

```scss
<style lang="scss">
/* Import global styles */
@import '@/styles/global.scss';

/* uview-plus 图标字体（base64 内联，覆盖 uview-plus 自带的远程 @font-face） */
@import '@/styles/uview-iconfont.scss';

/* App-level styles */
page {
```

顺序重要：放在 `global.scss` **之后**，同族 `@font-face` 后声明者胜。

- [ ] **Step 4: 写 `AppIcon` 组件**

创建 `miniapp/src/components/AppIcon.vue`：

```vue
<template>
  <u-icon
    :name="name"
    :size="sizePx"
    :color="resolvedColor"
    :bold="bold"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'

/**
 * 全站唯一的图标出口。
 *
 * 为什么不直接在页面里写 u-icon：尺寸/色板的默认值散在 20 个页面里会立刻失配，
 * 而且以后换图标集时要改 20 个文件。这里收口。
 *
 * 注意 `<u-icon>` 不加 import —— pages.json 的 easycom 规则
 * `"^u-(.*)": "uview-plus/components/u-$1/u-$1.vue"` 会自动解析。
 */
type Tone = 'primary' | 'ink' | 'muted' | 'white' | 'inherit'

const props = withDefaults(defineProps<{
  /** u-icon 名，不带 uicon- 前缀，如 shopping-cart */
  name: string
  /** rpx 数字，与设计稿一致 */
  size?: number | string
  tone?: Tone
  bold?: boolean
}>(), {
  size: 32,
  tone: 'inherit',
  bold: false,
})

const TONE_COLORS: Record<Exclude<Tone, 'inherit'>, string> = {
  primary: '#e16531',
  ink: '#2B2320',
  muted: '#a89a8a',
  white: '#ffffff',
}

/** u-icon 的 size 走 px；我们的设计稿是 rpx。转换后交给它。 */
const sizePx = computed(() => {
  if (typeof props.size === 'string' && props.size.endsWith('rpx')) {
    const n = parseFloat(props.size)
    return `${(n * (uni.getSystemInfoSync().windowWidth || 375)) / 750}px`
  }
  const n = typeof props.size === 'number' ? props.size : parseFloat(props.size)
  if (Number.isNaN(n)) return '16px'
  return `${(n * (uni.getSystemInfoSync().windowWidth || 375)) / 750}px`
})

const resolvedColor = computed(() => {
  if (props.tone === 'inherit') return undefined   // 交给 CSS 的 currentColor
  return TONE_COLORS[props.tone]
})
</script>
```

`tone="inherit"` 时不传 `color`，让图标继承父级 `color` —— 底栏选中态靠这个切色（spec §2 #13）。

- [ ] **Step 5: 在真机上验证（**这一步决定后面所有任务**）**

临时在 `miniapp/src/pages/home/index.vue` 的模板最开头插一行：

```vue
<view style="padding: 40rpx; display: flex; gap: 20rpx; align-items: center;">
  <AppIcon name="home" :size="48" tone="primary" />
  <AppIcon name="shopping-cart" :size="48" tone="ink" />
  <AppIcon name="heart-fill" :size="48" tone="primary" />
</view>
```

并在该文件的 `<script setup>` 顶部加：

```ts
import AppIcon from '../../components/AppIcon.vue'
```

然后：

```bash
cd miniapp && npm run dev:mp-weixin
```

用微信开发者工具打开 `miniapp/dist/dev/mp-weixin`，**点「预览」用真机扫码**（模拟器不加载远程/内联字体的行为与真机不同，必须真机）。

**判定：**

- **三个图标可见** → 通过。删掉这段临时代码，进入 Step 6 的 A 分支。
- **三个位置是空白方块 / 什么都不显示** → 不通过。进入 Step 6 的 B 分支。

- [ ] **Step 6: 分支处理**

**分支 A —— 验证通过：** 删除 Step 5 插入的临时代码，提交：

```bash
git add miniapp/src/styles/uview-iconfont.scss miniapp/src/components/AppIcon.vue miniapp/src/App.vue
git commit -m "$(cat <<'EOF'
feat(miniapp): uview-plus 图标字体 base64 内联 + AppIcon 组件

微信小程序 wxss 不支持远程 @font-face，uview-plus 自带的字体指向
at.alicdn.com，真机上图标会渲染成空白方块。把 ttf 转 base64 内联
（55940 字节 → 约 74KB），在 App.vue 里覆盖同族 @font-face。

AppIcon 收口尺寸与色板：页面不直接写 u-icon，避免 20 个页面各写
各的默认值，也为以后换图标集留一个改动点。

真机预览已验证三个图标可见。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

**分支 B —— 验证不通过：** 按 spec §7.3 的回退顺序处理。

回退 1 —— `wx.loadFontFace` 动态加载。在 `App.vue` 的 `onLaunch` 里加：

```ts
// u-icon 字体回退方案：运行时加载
// 需要先在微信公众平台把 at.alicdn.com 加入 downloadFile 合法域名
wx.loadFontFace({
  family: 'uicon-iconfont',
  source: 'url("https://at.alicdn.com/t/font_2225171_8kdcwk4po24.ttf")',
  global: true,
  success: () => console.log('[App] uicon font loaded'),
  fail: (err: any) => console.error('[App] uicon font failed', err),
})
```

回到 Step 5 重新验证。仍不通过则走回退 2。

回退 2 —— 放弃字体图标，改回 `static/icons/` 的 PNG 方案。此时 **Task 2、Task 11（底栏图标）作废**，`AppIcon` 改成渲染 `<image>` 并从 PNG 路径取图；emoji 替换只做「emoji → PNG」的映射。**回退 2 会显著增加工作量，走这条路之前先和人类搭档确认。**

- [ ] **Step 7: 记录结论**

把最终采用的分支写进 spec 的 §7.3（`docs/superpowers/specs/2026-10-04-miniapp-redesign-design.md`），一行即可：`**验证结果（2026-10-04）：方案 A 通过，真机可见。**`

```bash
git add docs/superpowers/specs/2026-10-04-miniapp-redesign-design.md
git commit -m "docs(design): 记录 u-icon 字体内联的真机验证结果

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 2: 图标映射表 `icon-map.ts`

Spec §7.4：全站实测 **31 种** emoji、**74 处**、分布在 **19 个文件**（统计口径：U+1F000–U+1FAFF 象形 emoji 区段，排除箭头 / ✓ / › 这类装饰字符）。映射表要覆盖全部 31 种——漏一个就是一处跨机型渲染不一致。

**Files:**
- Create: `miniapp/src/utils/icon-map.ts`
- Test: `miniapp/src/utils/__tests__/icon-map.test.ts`

**Interfaces:**
- Consumes: `miniapp/node_modules/uview-plus/components/u-icon/icons.js` 的图标名集合（212 个，以 `uicon-` 开头）
- Produces: `EMOJI_TO_ICON: Record<string, string>`（emoji → **不带** `uicon-` 前缀的图标名）；`iconForEmoji(emoji: string, fallback?: string): string`

- [ ] **Step 1: 写失败测试**

创建 `miniapp/src/utils/__tests__/icon-map.test.ts`。这个测试**扫描真实源码**，所以映射表的完整性是自动维护的，不依赖某个写死的数字。

```ts
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
  it('模板里直接写死的图标名也都存在', () => {
    const iconsSrc = readFileSync(
      join(__dirname, '..', '..', '..', 'node_modules', 'uview-plus',
           'components', 'u-icon', 'icons.js'),
      'utf-8',
    )
    const available = new Set(
      [...iconsSrc.matchAll(/'uicon-([a-z0-9-]+)':/g)].map((m) => m[1]),
    )

    const root = join(__dirname, '..', '..')
    const bad: string[] = []
    const walk = (dir: string) => {
      for (const entry of readdirSync(dir)) {
        const full = join(dir, entry)
        if (statSync(full).isDirectory()) { walk(full); continue }
        if (!full.endsWith('.vue') && !full.endsWith('.ts')) continue
        const text = readFileSync(full, 'utf-8')

        // ① <AppIcon name="xxx" /> —— 静态属性
        //    （:name="expr" 是动态绑定，值来自本映射表，上面已覆盖）
        for (const m of text.matchAll(/<AppIcon\b[^>]*?\bname="([^"]+)"/g)) {
          if (!available.has(m[1])) bad.push(`${full}: <AppIcon name="${m[1]}">`)
        }

        // ② 图标清单里的 icon: 'xxx' / iconActive: 'xxx'
        for (const m of text.matchAll(/\bicon(?:Active)?:\s*'([a-z0-9-]+)'/g)) {
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
```

- [ ] **Step 2: 跑测试，确认失败**

```bash
cd miniapp && npx vitest run src/utils/__tests__/icon-map.test.ts
```

预期：**FAIL** —— `Failed to resolve import "../icon-map"`。

- [ ] **Step 3: 写映射表**

创建 `miniapp/src/utils/icon-map.ts`。31 条，逐条对齐 Step 1 的统计口径：

```ts
/**
 * emoji → uview-plus 图标名。
 *
 * 用途：把现有页面里的 emoji 换成统一图标字体。B2B 母婴场景下，
 * emoji 在不同机型/系统上的字形差异很明显，是「不像成熟产品」的主因。
 *
 * 图标名取自 node_modules/uview-plus/components/u-icon/icons.js（212 个），
 * 不带 uicon- 前缀。测试会验证每个名字都真实存在。
 *
 * 按语义分组，方便以后加。
 */
export const EMOJI_TO_ICON: Record<string, string> = {
  // ── 导航与入口 ────────────────────────────────
  '🧸': 'bag-fill',            // 首页品牌标（图标集里没有玩偶，用购物袋兜）
  '🛒': 'shopping-cart',       // 购物车
  '🏢': 'file-text',           // 企业信息
  '📋': 'order',               // 订单
  '📍': 'map',                 // 收货地址
  '📞': 'phone',               // 联系客服
  '🎫': 'coupon',              // 优惠券
  '👣': 'clock',               // 浏览记录

  // ── 状态与空态 ────────────────────────────────
  '📦': 'empty-data',          // 空数据（EmptyState 默认图）
  '😞': 'empty-list',          // 空列表
  '😵': 'empty-page',          // 页面级空态
  '🔐': 'lock',                // 未登录 / 无权限
  '🔄': 'reload',              // 重试 / 刷新

  // ── 内容与运营 ────────────────────────────────
  '🎨': 'photo',               // 设计案例
  '🏷': 'tags',                // 标签
  '🎁': 'gift',                // 新品 / 礼品
  '🌟': 'star-fill',           // 精选
  '📊': 'grid',                // 数据 / 报表
  '💎': 'level',               // 会员等级
  '🎤': 'mic',                 // 语音输入
  '💬': 'chat',                // 消息 / 客服

  // ── 用户与互动 ────────────────────────────────
  '👤': 'account',             // 用户
  '👁': 'eye',                 // 浏览数
  '🤍': 'heart',               // 未收藏
  '💖': 'heart-fill',          // 已收藏

  // ── 交易与账期 ────────────────────────────────
  '💳': 'rmb-circle',          // 账期额度
  '🏦': 'rmb-circle-fill',     // 银行转账
  '💚': 'weixin-fill',         // 微信支付
  '🚚': 'car',                 // 发货 / 物流

  // ── 操作性 ────────────────────────────────────
  '🗑': 'trash',               // 删除
  '🔍': 'search',              // 搜索
}

/** 查不到映射时的兜底图标。返回图标名，不返回 emoji —— 回落到 emoji 就是漏改。 */
export const FALLBACK_ICON = 'more-circle'

export function iconForEmoji(emoji: string, fallback: string = FALLBACK_ICON): string {
  return EMOJI_TO_ICON[emoji] ?? fallback
}
```

- [ ] **Step 4: 跑测试，确认通过**

```bash
cd miniapp && npx vitest run src/utils/__tests__/icon-map.test.ts
```

预期：6 个用例全 **PASS**。

若第 1 个用例列出了缺映射的 emoji，**照着提示补进映射表**——提示里已经给了 U+ 码点和出现位置。不要为了让它过而放宽统计口径。

第 6 个用例（扫模板里写死的图标名）此刻是**空转通过**的——项目里还没有 `<AppIcon>`。它从 Task 8 起才真正开始干活：`custom-tab-bar/index.vue` 的 `icon:` 数组、Task 10 的 `CATEGORY_ICONS`、Task 14 的 `MENU_GROUPS` 都会被它扫。**那三个任务跑 `npm test` 时如果这条红了，就是图标名写错了，改名字，不要去放宽测试。**

- [ ] **Step 5: 跑全量前端测试**

```bash
cd miniapp && npm test
```

预期：全绿。

- [ ] **Step 6: 提交**

```bash
git add miniapp/src/utils/icon-map.ts miniapp/src/utils/__tests__/icon-map.test.ts
git commit -m "$(cat <<'EOF'
feat(miniapp): emoji → u-icon 映射表

实测 19 个文件里散着 31 种 emoji、74 处，跨机型字形差异明显。

映射表是全量的：测试扫描真实源码，断言每个出现的 emoji 都有映射，
并验证映射到的图标名在 uview-plus 的 212 个图标里真实存在。
漏一个就是一处漏改，所以用测试钉住而不是靠人工核对。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: 主题 token 重校准

Spec §3。现有圆角 token 偏大（`--radius-lg: 20px` = 40rpx），素材实测卡片圆角约 24–28rpx。同时把单位从 px 改成 rpx，并新增凸起圆 tabBar 需要的几个 token。

**Files:**
- Modify: `miniapp/src/styles/theme.scss`（`Border Radius` / `Shadows` / `Primary Colors` / `Component Tokens` 四段）

**Interfaces:**
- Consumes: 无
- Produces: 新增/变更的 CSS 自定义属性 —— `--color-primary-light: #f0916a`、`--color-primary-mid: #f5b28f`、`--color-ink: #2B2320`、`--color-on-primary: #ffffff`；`--radius-sm: 8rpx`、`--radius-md: 16rpx`、`--radius-lg: 28rpx`、`--radius-hero: 32rpx`、`--radius-pill: 999rpx`；`--shadow-card`、`--shadow-hero`、`--shadow-float`；`--tabbar-content-height: 114rpx`、`--tabbar-padding-bottom: 22rpx`、`--tabbar-radius-top: 24rpx`、`--tabbar-raised-size: 128rpx`、`--tabbar-gap: 16rpx`；工具类 `.has-custom-tabbar`

- [ ] **Step 1: 改色板**

`miniapp/src/styles/theme.scss` 的 `── Primary Colors ──` 段，替换成：

```scss
  // ── Primary Colors ──────────────────
  --color-primary: #e16531;
  --color-primary-light: #f0916a;      // 头图渐变终点（原 #f4a97e，加深一档）
  --color-primary-mid: #f5b28f;        // 渐变中段
  --color-ink: #2B2320;                // 横图卡胶囊按钮底色：深棕，比纯黑贴暖调
  --color-on-primary: #ffffff;
  --color-primary-dark: #E05555;
  --color-primary-bg: #FFF0F0;
```

`--color-ink` 的由来（spec §3.1）：素材里横图卡的按钮是纯黑配绿底，很跳；配珊瑚橙粉会发冷，换深棕。

- [ ] **Step 2: 改圆角**

`── Border Radius ──` 段整段替换成：

```scss
  // ── Border Radius ───────────────────
  // 单位是 rpx（750rpx = 屏宽），随机型等比缩放。
  // 原先是 px（--radius-lg: 20px），那是固定值，大屏上显小。
  --radius-sm: 8rpx;         // 标签、小徽章
  --radius-md: 16rpx;        // 输入框
  --radius-lg: 28rpx;        // 内容卡片（原 40rpx 等效值）
  --radius-hero: 32rpx;      // 头图 / 横图大卡
  --radius-pill: 999rpx;     // 胶囊
  --radius-circle: 50%;
  --radius-none: 0;
```

> ⚠️ `--radius-lg` 是全站 token，会同时影响范围外的 15 个子页面。这是**有意为之**（视觉刷新本来就该全站一致），由 Task 15 做视觉回归。

- [ ] **Step 3: 改阴影**

`── Shadows ──` 段，在既有值之后补三条（保留原有的 `--shadow-elevated` / `--shadow-dropdown` / `--shadow-button` / `--shadow-none`，只替换 `--shadow-card` 并新增两条）：

```scss
  // ── Shadows ─────────────────────────
  --shadow-card: 0 4rpx 16rpx rgba(74, 55, 40, 0.06);    // 带暖调，不纯黑
  --shadow-hero: 0 8rpx 24rpx rgba(225, 101, 49, 0.18);  // 凸起圆
  --shadow-float: 0 -2rpx 12rpx rgba(0, 0, 0, 0.05);     // 底栏上沿
  --shadow-elevated: 0 8rpx 30rpx rgba(0, 0, 0, 0.1);
  --shadow-dropdown: 0 6rpx 24rpx rgba(0, 0, 0, 0.08);
  --shadow-button: 0 2rpx 8rpx rgba(225, 101, 49, 0.3);
  --shadow-none: none;
```

- [ ] **Step 4: 加 tabBar token 与底部留白工具类**

`── Component Tokens ──` 段，替换成：

```scss
  // ── Component Tokens ────────────────
  --navbar-height: 44px;

  // 自定义 tabBar 几何（spec §6.2）
  // 内容高 = 18 上内边距 + 44 图标 + 6 间距 + 24 文字行高 + 22 下内边距
  --tabbar-content-height: 114rpx;
  --tabbar-padding-bottom: 22rpx;   // 凸起圆下沿与文字下沿对齐靠它，不要写死数值
  --tabbar-radius-top: 24rpx;
  --tabbar-raised-size: 128rpx;
  --tabbar-gap: 16rpx;              // 页面内容与底栏之间的额外呼吸空间

  --safe-area-bottom: constant(safe-area-inset-bottom);
  --safe-area-bottom-env: env(safe-area-inset-bottom);
```

然后在文件**工具类区域**（`── Position Utilities ──` 之前）插入：

```scss
// ── Page Shell ────────────────────────
// 换成自定义 tabBar 后，页面不再自动预留底栏高度，最后一个分区会被
// 凸起圆和底栏盖住。所有 tab 页的根元素都挂这个类。
//
// 用 calc + 自定义属性而不是写死数值：以后改底栏高度，这里自动跟着走。
.has-custom-tabbar {
  padding-bottom: calc(
    var(--tabbar-content-height) + env(safe-area-inset-bottom) + var(--tabbar-gap)
  );
}
```

- [ ] **Step 5: 确认样式仍能编译**

```bash
cd miniapp && npx sass --no-source-map src/styles/theme.scss /dev/null 2>&1 | head -20
```

预期：无输出（编译成功）。若有 `Undefined variable` 之类，说明替换时漏了引号或分号。

- [ ] **Step 6: 起开发服务，确认页面没崩**

```bash
cd miniapp && npm run dev:mp-weixin
```

用微信开发者工具打开 `dist/dev/mp-weixin`，逐个点开 5 个 tab 页。预期：页面正常渲染。圆角看起来会变小一圈，这是预期的——**但不应出现压字、错位、内容被裁**。若出现，说明某个页面把圆角当尺寸用了，记下来，Task 15 一并处理。

- [ ] **Step 7: 提交**

```bash
git add miniapp/src/styles/theme.scss
git commit -m "$(cat <<'EOF'
style(miniapp): 主题 token 重校准 —— 圆角改 rpx、新增色板与 tabBar 几何

圆角从 px 改成 rpx（--radius-lg 20px → 28rpx）。px 是固定值，
大屏上显小；rpx 随屏宽等比缩放，正是设计稿要的效果。
这是语义变更，不是数值微调。

新增 --color-ink (#2B2320)：横图卡的胶囊按钮底色。素材里是纯黑，
配珊瑚橙粉会发冷，换深棕。

新增 tabBar 几何 token 与 .has-custom-tabbar 工具类。自定义 tabBar 后
页面不再自动预留底栏高度，底部留白用 calc + 自定义属性表达，
不写死数值，以后改底栏高度不会跑偏。

注意：--radius-lg 是全站 token，会波及范围外的 15 个子页面，
需要一次全页面视觉回归（后续任务）。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: `SurfaceCard` + `SectionHeader`

两个基础容器，被所有 5 个页面复用。`SurfaceCard` 是「悬浮白色圆角卡片」，`SectionHeader` 是「分区大标题 + 右侧更多」。

**Files:**
- Create: `miniapp/src/components/SurfaceCard.vue`
- Create: `miniapp/src/components/SectionHeader.vue`

**Interfaces:**
- Consumes: Task 3 的 `--radius-lg`、`--shadow-card`、`--font-xl`、`--space-*`
- Produces:
  - `SurfaceCard` props：`overlap?: boolean`（默认 `false`，`true` 时用负 margin 上叠头图）、`padding?: string`（默认 `'32rpx'`）、`radius?: string`（默认 `'var(--radius-lg)'`）。默认 slot。
  - `SectionHeader` props：`title: string`、`more?: string`（默认 `''`，非空时右侧显示「`more` ›」）、`scrollPadding?: boolean`（默认 `false`，`true` 时左右内边距由调用方负责——横滑区标题要跟卡片对齐）。emit：`more`（无参）

- [ ] **Step 1: 写 `SurfaceCard`**

```vue
<template>
  <view class="surface-card" :class="{ 'surface-card--overlap': overlap }" :style="cardStyle">
    <slot />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

/**
 * 悬浮白色圆角卡片。
 *
 * overlap=true 时用负 margin 上叠到品牌色头图区上 —— 这是整套布局语言里
 * 最关键的一笔（素材里白色内容卡片压在绿色头图下沿）。用负 margin 而不是
 * 绝对定位：卡片高度随内容变化，绝对定位会把它锁死。
 *
 * padding / radius 走 inline style 而不是 scoped class：调用方要能直接覆盖
 * （我的页的菜单卡要 padding: 0 才能让分隔线通到卡片边缘）。
 */
const props = withDefaults(defineProps<{
  overlap?: boolean
  padding?: string
  radius?: string
}>(), {
  overlap: false,
  padding: '32rpx',
  radius: 'var(--radius-lg)',
})

const cardStyle = computed(() => ({
  padding: props.padding,
  borderRadius: props.radius,
}))
</script>

<style scoped>
.surface-card {
  background: var(--bg-white);
  box-shadow: var(--shadow-card);
  position: relative;
}

.surface-card--overlap {
  margin-top: -48rpx;
  margin-left: var(--space-lg);
  margin-right: var(--space-lg);
}
</style>
```

- [ ] **Step 2: 写 `SectionHeader`**

```vue
<template>
  <view class="section-header" :class="{ 'section-header--flush': scrollPadding }">
    <text class="section-header__title">{{ title }}</text>
    <text v-if="more" class="section-header__more" @tap="$emit('more')">{{ more }} ›</text>
  </view>
</template>

<script setup lang="ts">
/**
 * 分区大标题。
 *
 * 刻意没有装饰条 —— 旧版的「│ 小暖推荐」（4px 竖色条）被删掉了。
 * 层级靠字号(36rpx)和字重(700)建立，这是素材的做法（spec §3.5）。
 *
 * scrollPadding=true 时不加左右内边距，交给调用方 —— 横滑区的标题
 * 要和卡片左对齐，而卡片的滚动容器自带 padding。
 */
defineProps<{
  title: string
  more?: string
  scrollPadding?: boolean
}>()

defineEmits<{ more: [] }>()
</script>

<style scoped>
.section-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: var(--space-xl) var(--space-lg) var(--space-md);
}

.section-header--flush {
  padding-left: 0;
  padding-right: 0;
}

.section-header__title {
  font-size: var(--font-xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  line-height: var(--leading-tight);
}

.section-header__more {
  font-size: var(--font-sm);
  color: var(--text-muted);
}
</style>
```

- [ ] **Step 3: 起开发服务，肉眼确认**

在 `pages/home/index.vue` 模板最前面临时加：

```vue
<SectionHeader title="蓓贝推荐" more="查看更多" @more="goToMoreProducts" />
<SurfaceCard>
  <text>卡片内容</text>
</SurfaceCard>
```

`npm run dev:mp-weixin`，在开发者工具里确认：标题比正文明显大一级、没有竖色条、右侧「查看更多 ›」靠右对齐、白卡有圆角和淡阴影且左右有边距。

确认后**删掉这段临时代码**（页面正式结构在 Task 10 写）。

- [ ] **Step 4: 提交**

```bash
git add miniapp/src/components/SurfaceCard.vue miniapp/src/components/SectionHeader.vue
git commit -m "$(cat <<'EOF'
feat(miniapp): SurfaceCard 与 SectionHeader 基础容器

SurfaceCard 的 overlap 变体用负 margin（不是绝对定位）把白卡叠到
品牌色头图上——卡片高度随内容变化，绝对定位会把它锁死。

SectionHeader 刻意去掉旧版的 4px 竖色条，层级改由 36rpx/700 建立，
这是素材的做法。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: `BrandHero` + `BannerCard`

`BrandHero` 是品牌色头图区（5 个页面都用），`BannerCard` 是满宽横图卡（首页、案例页）。

**Files:**
- Create: `miniapp/src/components/BrandHero.vue`
- Create: `miniapp/src/components/BannerCard.vue`
- Modify: `miniapp/src/components/SearchBar.vue`（加 `variant` prop + 换掉三个 emoji）

**Interfaces:**
- Consumes: `AppIcon`（Task 1）、`SearchBar`、Task 3 的 `--color-primary-light` / `--color-ink` / `--radius-hero`
- Produces:
  - `BrandHero` props：`title: string`、`slogan?: string`、`showSearch?: boolean`（默认 `false`）、`showLogin?: boolean`（默认 `false`）、`compact?: boolean`（默认 `false`，`true` 时用较矮的头图，给商品/案例页用）。emits：**`search: [keyword: string]`**（搜索框回车/点击，带回关键词）、`login: []`
  - `BannerCard` props：`title: string`、`subtitle?: string`、`image?: string`、`action?: string`（默认 `'查看详情'`）、`width?: string`（默认 `'100%'`）。emits：`tap`
  - `SearchBar` 新增可选 prop **`variant?: 'standalone' | 'inline'`**（默认 `'standalone'`）；其余 props/emits 一字不动

- [ ] **Step 1: 写 `BrandHero`**

```vue
<template>
  <view class="brand-hero" :class="{ 'brand-hero--compact': compact }" :style="{ paddingTop: heroPaddingTop }">
    <view class="brand-hero__row">
      <view class="brand-hero__brand">
        <view class="brand-hero__mark">
          <AppIcon name="bag-fill" :size="40" tone="primary" />
        </view>
        <view class="brand-hero__text">
          <text class="brand-hero__title">{{ title }}</text>
          <text v-if="slogan" class="brand-hero__slogan">{{ slogan }}</text>
        </view>
      </view>
      <view v-if="showLogin" class="brand-hero__login" @tap="$emit('login')">
        <text class="brand-hero__login-text">登录 / 注册</text>
      </view>
    </view>

    <view v-if="showSearch" class="brand-hero__search">
      <SearchBar
        v-model="keyword"
        variant="inline"
        placeholder="搜索商品 / 案例"
        :show-voice="true"
        @search="$emit('search', $event)"
        @voice="$emit('search', keyword)"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import AppIcon from './AppIcon.vue'
import SearchBar from './SearchBar.vue'
import { useAppStore } from '../stores/app'

/**
 * 品牌色头图区。
 *
 * 搜索框用 SearchBar 的 inline 变体嵌在头图里（白胶囊），而不是悬在
 * 头图下沿 —— 素材里搜索框是头图的一部分（spec §4.2）。复用它而不是
 * 在这里另写一个 input：SearchBar 已经有 v-model、清除、语音全套逻辑，
 * 重写一遍就是两处要维护。
 *
 * 品牌标用 AppIcon 而不是 emoji：旧版首页是 🧸，跨机型字形差异明显。
 */
const props = withDefaults(defineProps<{
  title: string
  slogan?: string
  showSearch?: boolean
  showLogin?: boolean
  compact?: boolean
}>(), {
  slogan: '',
  showSearch: false,
  showLogin: false,
  compact: false,
})

defineEmits<{
  search: [keyword: string]
  login: []
}>()

/**
 * 让开状态栏。
 *
 * 头图是全站第一个元素，所以它必须自己扛状态栏高度 —— 用了这个组件的
 * 页面都在 pages.json 里设了 navigationStyle: "custom"（见 Task 8），
 * 没有系统导航栏帮忙撑开顶部。若哪天有页面忘了设 custom，这里会多出
 * 一块空白而不是顶到状态栏下面，是安全的那种失败。
 *
 * statusBarHeight 来自 stores/app（单位 px，是设备度量，不要转 rpx）。
 */
const appStore = useAppStore()

const heroPaddingTop = computed(() => {
  const base = appStore.statusBarHeight || 20
  return `${base + (props.compact ? 8 : 20)}px`
})

const keyword = ref('')
</script>

<style scoped>
.brand-hero {
  background: linear-gradient(160deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  /* padding-top 不在这里写 —— 它要读状态栏高度，由 heroPaddingTop 内联给出 */
  padding: 0 var(--space-lg) var(--space-4xl);
  position: relative;
}

.brand-hero--compact {
  padding-bottom: var(--space-3xl);
}

.brand-hero__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand-hero__brand {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.brand-hero__mark {
  width: 72rpx;
  height: 72rpx;
  border-radius: var(--radius-circle);
  background: var(--bg-white);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.brand-hero__text {
  display: flex;
  flex-direction: column;
}

.brand-hero__title {
  font-size: var(--font-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-white);
  line-height: var(--leading-tight);
}

.brand-hero__slogan {
  font-size: var(--font-sm);
  color: rgba(255, 255, 255, 0.85);
  margin-top: var(--space-2xs);
}

.brand-hero__login {
  background: var(--bg-white);
  border-radius: var(--radius-pill);
  padding: 12rpx 28rpx;
  flex-shrink: 0;
}

.brand-hero__login-text {
  font-size: var(--font-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
}

/* 白胶囊由头图这边提供；SearchBar 的 inline 变体自己不画背景和阴影 */
.brand-hero__search {
  margin-top: var(--space-xl);
  background: var(--bg-white);
  border-radius: var(--radius-pill);
  height: 72rpx;
  display: flex;
  align-items: center;
  padding: 0 var(--space-lg);
}
</style>
```

- [ ] **Step 2: 写 `BannerCard`**

```vue
<template>
  <view class="banner" :style="{ width: width }" @tap="$emit('tap')">
    <image v-if="image" class="banner__img" :src="image" mode="aspectFill" />
    <!-- 无图兜底：品牌色几何底纹。案例图目前还没有，这个兜底是常态而非例外。 -->
    <view v-else class="banner__img banner__img--placeholder">
      <AppIcon name="photo" :size="72" tone="white" />
    </view>

    <view class="banner__mask" />

    <view class="banner__content">
      <text class="banner__title">{{ title }}</text>
      <text v-if="subtitle" class="banner__subtitle">{{ subtitle }}</text>
      <view v-if="action" class="banner__pill">
        <text class="banner__pill-text">{{ action }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import AppIcon from './AppIcon.vue'

/**
 * 满宽横图卡：图 + 左深右浅的渐变遮罩 + 左下标题区 + 深棕胶囊按钮。
 *
 * 胶囊用 --color-ink(#2B2320) 而不是纯黑：素材里是纯黑配绿底，很跳；
 * 配珊瑚橙粉的暖调背景会发冷，换深棕。
 *
 * 遮罩从左上深到右浅（90deg），保证左下角文字在任何底图上都可读。
 */
withDefaults(defineProps<{
  title: string
  subtitle?: string
  image?: string
  action?: string
  width?: string
}>(), {
  subtitle: '',
  image: '',
  action: '查看详情',
  width: '100%',
})

defineEmits<{ tap: [] }>()
</script>

<style scoped>
.banner {
  position: relative;
  height: 260rpx;
  border-radius: var(--radius-hero);
  overflow: hidden;
  flex-shrink: 0;
}

.banner__img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.banner__img--placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(115deg, var(--color-primary-light), var(--color-primary-mid));
  opacity: 0.9;
}

.banner__mask {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.05));
}

.banner__content {
  position: absolute;
  left: var(--space-lg);
  right: var(--space-lg);
  bottom: var(--space-lg);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.banner__title {
  color: var(--text-white);
  font-size: var(--font-lg);
  font-weight: var(--font-weight-bold);
  line-height: var(--leading-tight);
}

.banner__subtitle {
  color: rgba(255, 255, 255, 0.9);
  font-size: var(--font-sm);
  margin-top: var(--space-2xs);
}

.banner__pill {
  background: var(--color-ink);
  border-radius: var(--radius-pill);
  padding: 8rpx 24rpx;
  margin-top: var(--space-sm);
}

.banner__pill-text {
  color: var(--text-white);
  font-size: var(--font-xs);
  font-weight: var(--font-weight-semibold);
}
</style>
```

- [ ] **Step 3: 改 `SearchBar` —— 加 `variant`，换掉三个 emoji**

现有 `SearchBar.vue` 是正经的 v-model 组件（props：`placeholder` / `modelValue` / `showVoice` / `autoFocus`；emits：`update:modelValue` / `search` / `voice` / `focus` / `blur` / `clear`）。**这些签名一个都不要动**——两处菜单页在用。

**① 加 `variant` prop。** 在 `Props` 接口里追加，并给 `withDefaults` 加默认值：

```ts
interface Props {
  placeholder?: string
  modelValue?: string
  showVoice?: boolean
  autoFocus?: boolean
  /** standalone = 自带背景阴影，独立使用；inline = 透明，由外层容器（如 BrandHero 的白胶囊）提供背景 */
  variant?: 'standalone' | 'inline'
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '搜索儿童产品...',
  modelValue: '',
  showVoice: true,
  autoFocus: false,
  variant: 'standalone',
})
```

根元素加 class：

```vue
<view class="search-bar" :class="{ 'search-bar--inline': variant === 'inline' }">
```

样式追加（`inline` 时外层已经有白胶囊，自己不能再画一层）：

```css
.search-bar--inline {
  background: transparent;
  box-shadow: none;
  border: none;
  padding: 0;
  flex: 1;
}
```

**② 三个 emoji 换 `AppIcon`。** 🔍 → `<AppIcon name="search" :size="30" tone="muted" />`；✕ → `<AppIcon name="close" :size="28" tone="muted" />`；🎤 → `<AppIcon name="mic" :size="30" tone="muted" />`。在 `<script setup>` 里 `import AppIcon from './AppIcon.vue'`。

- [ ] **Step 4: 起开发服务肉眼确认**

在 `pages/home/index.vue` 顶部临时加：

```vue
<BrandHero title="蓓贝婴童" slogan="源头工厂 · 一件代发" show-login show-search />
<SurfaceCard>
  <BannerCard title="北欧风儿童房整体方案" subtitle="0-3 岁 · 含 12 件套柜体" />
</SurfaceCard>
```

确认：

- 头图是珊瑚橙到浅橙的渐变；顶部**不顶到状态栏**（`heroPaddingTop` 生效）
- 白色品牌圆标里有一个珊瑚色图标
- 右侧白胶囊「登录 / 注册」
- 下方白胶囊搜索框，**只有一层白底**（若出现双层白底，说明 `SearchBar` 的 `inline` 变体没生效）
- 搜索框里能打字、有放大镜图标、有麦克风图标
- 横图卡左深右浅、左下标题白色可读、深棕胶囊按钮

确认后删掉临时代码。

- [ ] **Step 5: 提交**

```bash
git add miniapp/src/components/BrandHero.vue miniapp/src/components/BannerCard.vue miniapp/src/components/SearchBar.vue
git commit -m "$(cat <<'EOF'
feat(miniapp): BrandHero 品牌头图区与 BannerCard 满宽横图卡

BrandHero 把搜索框嵌进头图里（白胶囊），照素材的做法。复用
SearchBar 的 inline 变体而不是另写一个 input —— 它已经有 v-model、
清除、语音全套逻辑，重写就是两处要维护。

BrandHero 自己扛状态栏高度（读 appStore.statusBarHeight）：它用
navigationStyle: custom 的页面里是全站第一个元素，没有系统导航栏
帮忙撑开顶部。

SearchBar 新增 variant prop，默认 standalone 保持旧观感（两处菜单页
在用，签名未动）；inline 时不画背景阴影，由外层白胶囊提供。
三个 emoji 换成 AppIcon。

BannerCard 的胶囊按钮用新增的 --color-ink 深棕，不用纯黑：
纯黑配珊瑚橙粉的暖调背景会发冷。遮罩从左深到右浅，保证左下角
文字在任何底图上都可读。无图时用品牌色几何底纹兜底——案例图
目前还没有，这是常态而非例外。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: `EntryGrid` + `CircleEntryRow` + `BenefitCard`

首页专用的三件套，都装在负 margin 上叠的 `SurfaceCard` 里。

**Files:**
- Create: `miniapp/src/components/EntryGrid.vue`
- Create: `miniapp/src/components/CircleEntryRow.vue`
- Create: `miniapp/src/components/BenefitCard.vue`

**Interfaces:**
- Consumes: `AppIcon`（Task 1）、`SurfaceCard`（Task 4）
- Produces:
  - `EntryGrid` props：`items: { icon: string; title: string; subtitle?: string }[]`。emit：`select`（`index: number`）。3 列布局。
  - `CircleEntryRow` props：`items: { icon: string; label: string; id?: string }[]`。emit：`select`（`index: number`）。横向可滚，4 个以上才露边。
  - `BenefitCard` props：`main: { title: string; desc: string; action?: string }`、`side: { icon: string; title: string; desc?: string }[]`（**恰好 2 个**）。emits：`mainTap`、`sideTap`（`index: number`）

- [ ] **Step 1: 写 `EntryGrid`**

```vue
<template>
  <view class="entry-grid">
    <view
      v-for="(item, i) in items"
      :key="i"
      class="entry-grid__item"
      @tap="$emit('select', i)"
    >
      <view class="entry-grid__icon">
        <AppIcon :name="item.icon" :size="44" tone="primary" />
      </view>
      <text class="entry-grid__title">{{ item.title }}</text>
      <text v-if="item.subtitle" class="entry-grid__subtitle">{{ item.subtitle }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import AppIcon from './AppIcon.vue'

/** 快捷服务入口，3 列。图标居中、主标题加粗、副标题弱化。 */
defineProps<{
  items: { icon: string; title: string; subtitle?: string }[]
}>()

defineEmits<{ select: [index: number] }>()
</script>

<style scoped>
.entry-grid {
  display: flex;
  justify-content: space-around;
}

.entry-grid__item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.entry-grid__icon {
  width: 88rpx;
  height: 88rpx;
  border-radius: var(--radius-circle);
  background: var(--color-primary-bg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.entry-grid__title {
  font-size: var(--font-base);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-top: var(--space-sm);
}

.entry-grid__subtitle {
  font-size: var(--font-xs);
  color: var(--text-muted);
  margin-top: var(--space-2xs);
}
</style>
```

- [ ] **Step 2: 写 `CircleEntryRow`**

```vue
<template>
  <scroll-view class="circle-row" scroll-x :show-scrollbar="false" enhanced>
    <view class="circle-row__inner">
      <view
        v-for="(item, i) in items"
        :key="item.id ?? i"
        class="circle-row__item"
        @tap="$emit('select', i)"
      >
        <view class="circle-row__circle">
          <AppIcon :name="item.icon" :size="40" tone="primary" />
        </view>
        <text class="circle-row__label">{{ item.label }}</text>
      </view>
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
import AppIcon from './AppIcon.vue'

/**
 * 圆形图标入口行，横向可滚（接后端 categories）。
 *
 * 用 enhanced + show-scrollbar=false：微信默认会在横滑区底部压一条
 * 滚动条，视觉上很脏。
 *
 * inner 用 inline-flex + 两端 padding：横滑内容的首尾要和页面边距对齐，
 * 但内容本身要能滑到边缘以外，所以 padding 加在内层而不是 scroll-view 上。
 */
defineProps<{
  items: { icon: string; label: string; id?: string }[]
}>()

defineEmits<{ select: [index: number] }>()
</script>

<style scoped>
.circle-row {
  width: 100%;
  white-space: nowrap;
}

.circle-row__inner {
  display: inline-flex;
  gap: var(--space-xl);
  padding: 0 var(--space-xs);
}

.circle-row__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 104rpx;
}

.circle-row__circle {
  width: 96rpx;
  height: 96rpx;
  border-radius: var(--radius-circle);
  background: var(--color-primary-bg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.circle-row__label {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  margin-top: var(--space-xs);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 104rpx;
}
</style>
```

- [ ] **Step 3: 写 `BenefitCard`**

```vue
<template>
  <view class="benefit">
    <view class="benefit__main" @tap="$emit('mainTap')">
      <text class="benefit__main-title">{{ main.title }}</text>
      <text class="benefit__main-desc">{{ main.desc }}</text>
      <view v-if="main.action" class="benefit__main-pill">
        <text class="benefit__main-pill-text">{{ main.action }}</text>
      </view>
    </view>

    <view class="benefit__side">
      <view
        v-for="(item, i) in side"
        :key="i"
        class="benefit__side-card"
        @tap="$emit('sideTap', i)"
      >
        <AppIcon :name="item.icon" :size="36" tone="primary" />
        <text class="benefit__side-title">{{ item.title }}</text>
        <text v-if="item.desc" class="benefit__side-desc">{{ item.desc }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import AppIcon from './AppIcon.vue'

/**
 * 会员权益双栏卡：左侧一张大卡（品牌色渐变），右侧两张小卡。
 *
 * side 要求恰好 2 个 —— 三张会挤，一张会让右栏塌。用 CSS 让它自己
 * 撑成一列两行，不写死高度。
 */
defineProps<{
  main: { title: string; desc: string; action?: string }
  side: { icon: string; title: string; desc?: string }[]
}>()

defineEmits<{ mainTap: []; sideTap: [index: number] }>()
</script>

<style scoped>
.benefit {
  display: flex;
  gap: var(--space-md);
}

.benefit__main {
  flex: 1.35;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 200rpx;
}

.benefit__main-title {
  color: var(--text-white);
  font-size: var(--font-lg);
  font-weight: var(--font-weight-bold);
}

.benefit__main-desc {
  color: rgba(255, 255, 255, 0.9);
  font-size: var(--font-xs);
  margin-top: var(--space-xs);
  line-height: var(--leading-normal);
}

.benefit__main-pill {
  align-self: flex-start;
  background: var(--bg-white);
  border-radius: var(--radius-pill);
  padding: 6rpx 20rpx;
  margin-top: var(--space-sm);
}

.benefit__main-pill-text {
  font-size: var(--font-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
}

.benefit__side {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.benefit__side-card {
  flex: 1;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.benefit__side-title {
  font-size: var(--font-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-top: var(--space-xs);
}

.benefit__side-desc {
  font-size: var(--font-xs);
  color: var(--text-muted);
  margin-top: var(--space-2xs);
}
</style>
```

- [ ] **Step 4: 起开发服务肉眼确认**

在首页临时拼一个 `SurfaceCard` 装这三个组件，确认：

- 三个服务入口等宽、图标圆底居中、主副标题层次分明
- 分类圆图标行能横滑，滑动条**不显示**，首尾与页面边距对齐
- 权益双栏：左大卡是品牌色渐变、右边两张小卡一列两行、高度对齐不塌

确认后删掉临时代码。

- [ ] **Step 5: 提交**

```bash
git add miniapp/src/components/EntryGrid.vue miniapp/src/components/CircleEntryRow.vue miniapp/src/components/BenefitCard.vue
git commit -m "$(cat <<'EOF'
feat(miniapp): 首页三件套 EntryGrid / CircleEntryRow / BenefitCard

CircleEntryRow 用 enhanced + show-scrollbar=false 关掉微信默认压在
横滑区底部的滚动条；内层 inline-flex 加两端 padding，让内容首尾
与页面边距对齐但仍可滑出边缘。

BenefitCard 的右栏用 CSS 撑成一列两行，不写死高度。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: 改造复用组件——`EmptyState` / `PageLoading` / `ProductCard` / `CaseCard`

Spec §4.2。`EmptyState`（15 个页面引用）和 `PageLoading`（13 个页面引用）被大面积复用，**props 接口必须向后兼容**——只改内部实现，不加必填 prop、不改既有 prop 的名字和语义。

（`SearchBar` 不在这里——它的消费方 `BrandHero` 在 Task 5，所以它的改造已经并进 Task 5 了。）

**Files:**
- Modify: `miniapp/src/components/EmptyState.vue`
- Modify: `miniapp/src/components/PageLoading.vue`
- Modify: `miniapp/src/components/ProductCard.vue`
- Modify: `miniapp/src/components/CaseCard.vue`

**Interfaces:**
- Consumes: `AppIcon`（Task 1）、`EMOJI_TO_ICON`（Task 2）
- Produces: 四个组件的**现有 props 与 emits 全部不变**（`ProductCard` 仍是 `product` + `click`，`CaseCard` 仍是 `caseData` + `click`）。`EmptyState` 新增一个可选 prop `illustration?: string`（默认 `'empty-data'`）

- [ ] **Step 1: 先看清现有接口，不要凭印象改**

```bash
cd miniapp/src/components
for f in EmptyState.vue PageLoading.vue ProductCard.vue CaseCard.vue; do
  echo "════════ $f ════════"
  awk '/<script setup/,/<\/script>/' "$f"
done
```

把每个组件的 `defineProps` / `defineEmits` 原样抄到一张纸上。**改完之后要逐项核对这四个组件的 props / emits 没有增删改。**这一步是整个任务的安全带——`EmptyState` 有 15 个调用方，改坏一个 prop 名字会静默影响 15 个页面。

已经核实过、**不要改**的两个：
- `ProductCard`：`{ product: Product; showStock?: boolean }`，`emit('click', id)`
- `CaseCard`：`{ caseData: DesignCase }`，`emit('click', id)`

- [ ] **Step 2: 改 `EmptyState`**

把 emoji 换成 u-icon 空状态插画，并把文案改成「说清下一步」（spec §8.1）。**`text` / `description` 之类的现有 prop 保持原名与语义**，只新增可选的 `illustration`。

模板里的图标部分改成：

```vue
<view class="empty-state__icon">
  <AppIcon :name="illustration" :size="140" tone="muted" />
</view>
```

`<script setup>` 里新增（放在既有 props 之后）：

```ts
import AppIcon from './AppIcon.vue'

withDefaults(defineProps<{
  // ……既有的 props 原样保留，一个都不要动……
  /** u-icon 空状态插画名。图标集里有 13 个 uicon-empty-*：
   *  empty-address / empty-car / empty-coupon / empty-data / empty-favor /
   *  empty-history / empty-list / empty-news / empty-order / empty-page /
   *  empty-permission / empty-search / empty-wifi */
  illustration?: string
}>(), {
  illustration: 'empty-data',
})
```

样式里把图标容器改成居中、去掉旧的 emoji 字号设定：

```css
.empty-state__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-lg);
}
```

> 如果现有 `EmptyState` 的 props 里已经有一个 emoji 相关的 prop（很可能有），**保留它但不再使用**，加一行注释说明它已废弃、将在子页面铺开时移除。删掉它会让 15 个调用方报类型错。

- [ ] **Step 3: 改 `PageLoading`**

骨架色改暖调、圆角对齐新 token。只动 `<style>`：

```css
.skeleton-block {
  background: var(--bg-muted);        /* 暖调，不是纯灰 */
  border-radius: var(--radius-lg);    /* 跟随重校准后的 token */
}
```

若文件里用了 `--radius-lg` 之外的写死圆角（`border-radius: 20px` 之类），一并换成 token。

- [ ] **Step 4: 改 `ProductCard`**

只动样式与图标，**不动 props 与数据字段**：

- 卡片圆角用 `var(--radius-lg)`，阴影用 `var(--shadow-card)`
- 无图兜底从 emoji 换成 `<AppIcon name="photo" />`
- 价格排版加强：现价用 `--color-primary` + `--font-xl` + `700`，「¥」符号用 `--font-sm`；起批量的「xx 件起」放价格右侧，用 `--text-muted` + `--font-xs`

- [ ] **Step 5: 改 `CaseCard`**

组件当前的接口（已核实）：prop 是 **`caseData`**，emit 是 **`click: [id]`**，内部有一个**局部** `DesignCase` 接口 `{ id, title, images, style_tags, category_tags }`。

三处改动：

**① 局部接口补字段。** 标签行要用 `store_area_range`，而局部接口里没有它——不补就是类型错误。在后端 `CaseListOut` 里这个字段是存在的（`str | null`）：

```ts
interface DesignCase {
  id: string | number
  title: string
  images: string[]
  style_tags: string[]
  category_tags: string[]
  /** 门店面积区间，如 "50-100㎡"。后端 CaseListOut 里是 str | null */
  store_area_range?: string | null
}
```

**注意不要加 `age_range`** —— 后端 `app/schemas/case.py` 的 `CaseListOut` 根本没有这个字段，加了就是又一个 phantom field。

**② 标签行模板。** 插到封面图下方：

```vue
<view v-if="tags.length" class="case-card__tags">
  <text v-for="t in tags" :key="t" class="case-card__tag">{{ t }}</text>
</view>
```

**③ 标签计算。** 用的是真实 prop 名 `caseData`：

```ts
const tags = computed(() => {
  const c = props.caseData
  const out: string[] = []
  if (c.store_area_range) out.push(c.store_area_range)
  for (const t of (c.style_tags || []).slice(0, 2)) out.push(t)
  return out
})
```

样式：

```css
.case-card__tags { display: flex; flex-wrap: wrap; gap: var(--space-2xs); margin-top: var(--space-xs); }
.case-card__tag {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  padding: 4rpx 12rpx;
}
```

- 另：圆角、阴影、无图兜底（`AppIcon name="photo"`）同 `ProductCard`。

- [ ] **Step 6: 类型检查 + 全量测试**

```bash
cd miniapp && npx vue-tsc --noEmit && npm test
```

预期：类型检查**无错误**。这是本任务的关键验证——`EmptyState` 的 15 个调用方、`PageLoading` 的 13 个调用方只要有一个 prop 签名对不上，`vue-tsc` 就会报出来（没有组件单测，类型检查就是唯一的安全网）。

若报错，**改组件的接口去适配调用方**，不要改调用方——它们大多在范围外的 15 个子页面里。

- [ ] **Step 7: 起开发服务，抽查三个页面**

打开首页、商品列表、案例列表，确认卡片观感和加载骨架正常。再随手打开一个范围外页面（比如「我的收藏」），确认它的空状态还正常——那是 `EmptyState` 的 15 个调用方之一。

- [ ] **Step 8: 提交**

```bash
git add miniapp/src/components/EmptyState.vue miniapp/src/components/PageLoading.vue miniapp/src/components/ProductCard.vue miniapp/src/components/CaseCard.vue
git commit -m "$(cat <<'EOF'
refactor(miniapp): 复用组件改用图标字体并对齐新 token

EmptyState(15 个调用方) 和 PageLoading(13 个调用方) 只改内部实现，
props 接口一字未动——它们被范围外的 15 个子页面共用，改签名会
静默波及那些页面。

EmptyState 的 emoji 换成 u-icon 的空状态插画，新增可选
illustration prop。

CaseCard 新增标签行，数据取自 style_tags 与 store_area_range
（后端 CaseListOut 没有 age_range 字段，不要加）。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: 自定义 tabBar

Spec §6。原生 tabBar 画不出凸起圆，也无法给**单个** tab 去掉文字（微信只支持统一配置），所以必须换成 `"custom": true`。

**几何（spec §6.2，实测素材换算）：**

| 项 | 取值 | 说明 |
|---|---|---|
| 底栏内容高 | 114rpx | = 18 上内边距 + 44 图标 + 6 间距 + 24 文字行高 + 22 下内边距 |
| 凸起圆直径 | 128rpx | |
| 圆高出栏顶 | 36rpx | = 128 − (114 − 22) |
| 圆下沿距栏底 | 22rpx | **= 文字下沿**，两者对齐 |
| 顶角圆角 | 24rpx | 底栏顶部两角 |
| 描边 | 无 | 圆直接压在白色底栏上 |

**Files:**
- Create: `miniapp/src/custom-tab-bar/index.vue`
- Modify: `miniapp/src/pages.json`（tabBar 段）
- Modify: 5 个 tab 页的 `onShow`（本任务只需加选中态同步；页面重写在各页任务里做）

**Interfaces:**
- Consumes: `AppIcon`（Task 1）、Task 3 的 `--tabbar-*` token
- Produces: `custom-tab-bar/index.vue` —— 无 props。内部读 `uni.getStorageSync('tabbar_selected')` 决定选中项。

- [ ] **Step 1: 改 `pages.json`**

`tabBar` 段替换成：

```json
  "tabBar": {
    "custom": true,
    "color": "#7a6a5a",
    "selectedColor": "#e16531",
    "backgroundColor": "#FFFFFF",
    "borderStyle": "white",
    "list": [
      { "pagePath": "pages/home/index", "text": "首页" },
      { "pagePath": "pages/cases/index", "text": "案例" },
      { "pagePath": "pages/ai-assistant/index", "text": "蓓贝客服" },
      { "pagePath": "pages/products/index", "text": "商品" },
      { "pagePath": "pages/mine/index", "text": "我的" }
    ]
  },
```

三处变化：

1. 加 `"custom": true`
2. `list` 的**顺序改成 spec §2 #9 的顺序**：首页 / 案例 / 蓓贝客服 / 商品 / 我的——客服居中
3. **删掉全部 `iconPath` / `selectedIconPath`**。旧值本身就是坏的（spec §1：`static/icons/` 下 10 个 PNG 都齐全，但 `selectedIconPath` 全指向非选中图标）。自定义 tabBar 不读这两个字段，留着只会误导。

> `list` 仍要保留 5 项是**必须的**：`uni.switchTab` 靠它做路径校验。顺序也必须与 `custom-tab-bar/index.vue` 里的数组顺序一致——两处不一致会导致点 A 跳到 B。

**同一处还要改 4 个页面的 `navigationStyle`。** 现在只有客服页是 `custom`，另外 4 个用系统导航栏——那会变成「系统标题栏 + 珊瑚色头图」的双头。设计稿（`.superpowers/redesign-preview.html`）顶部直接是头图，没有系统导航栏；参考素材的首页也是这样。spec 没写这一条，是规划阶段发现的空白。

给这 4 个页面各加一行：

```json
{ "path": "pages/home/index",     "style": { "navigationStyle": "custom", "navigationBarTitleText": "蓓贝婴童" } },
{ "path": "pages/cases/index",    "style": { "navigationStyle": "custom", "navigationBarTitleText": "设计案例" } },
{ "path": "pages/products/index", "style": { "navigationStyle": "custom", "navigationBarTitleText": "商品列表" } },
{ "path": "pages/mine/index",     "style": { "navigationStyle": "custom", "navigationBarTitleText": "我的" } },
```

（只加 `navigationStyle`，其余 style 字段保持原样。`navigationBarTitleText` 在 custom 模式下不显示，但保留它无害，且下拉刷新等场景可能用到。）

顶部让位由 `BrandHero` 自己处理——它读 `appStore.statusBarHeight` 并内联 `padding-top`（Task 5 已实现）。**所以这 4 个页面的模板第一行必须是 `BrandHero`**；若某页把别的元素放在头图之前，那一块会顶到状态栏下面。

- [ ] **Step 2: 写 `custom-tab-bar/index.vue`**

```vue
<template>
  <view class="tabbar">
    <view class="tabbar__bar">
      <view
        v-for="(item, i) in tabs"
        :key="item.pagePath"
        class="tabbar__item"
        :class="{ 'tabbar__item--placeholder': item.raised }"
        @tap="switchTo(i)"
      >
        <template v-if="!item.raised">
          <AppIcon
            :name="selected === i ? item.iconActive : item.icon"
            :size="44"
            :tone="selected === i ? 'primary' : 'muted'"
          />
          <text class="tabbar__label" :class="{ 'tabbar__label--active': selected === i }">
            {{ item.text }}
          </text>
        </template>
      </view>
    </view>

    <!-- 凸起圆：绝对定位压在白底栏上，无描边 -->
    <view class="tabbar__raised" @tap="switchTo(raisedIndex)">
      <AppIcon :name="tabs[raisedIndex].iconActive" :size="56" tone="white" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'

/**
 * 自定义 tabBar。
 *
 * 为什么必须自定义：原生 tabBar 画不出凸起圆，也没法只给一个 tab 去文字。
 *
 * 顺序必须与 pages.json 的 tabBar.list 完全一致 —— switchTab 按索引跳转，
 * 两处不一致会导致点 A 跳到 B。改顺序时两个文件一起改。
 */
const SELECTED_KEY = 'tabbar_selected'

const tabs = [
  { pagePath: '/pages/home/index',         text: '首页',     icon: 'home',          iconActive: 'home-fill',          raised: false },
  { pagePath: '/pages/cases/index',        text: '案例',     icon: 'photo',         iconActive: 'photo-fill',         raised: false },
  { pagePath: '/pages/ai-assistant/index', text: '',         icon: 'kefu-ermai',    iconActive: 'kefu-ermai',         raised: true  },
  { pagePath: '/pages/products/index',     text: '商品',     icon: 'bag',           iconActive: 'bag-fill',           raised: false },
  { pagePath: '/pages/mine/index',         text: '我的',     icon: 'account',       iconActive: 'account-fill',       raised: false },
]

const raisedIndex = tabs.findIndex((t) => t.raised)

const selected = ref(Number(uni.getStorageSync(SELECTED_KEY) ?? 0) || 0)

function switchTo(index: number) {
  selected.value = index
  uni.setStorageSync(SELECTED_KEY, index)
  uni.switchTab({ url: tabs[index].pagePath })
}
</script>

<style scoped>
.tabbar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: var(--z-sticky);
}

.tabbar__bar {
  display: flex;
  align-items: flex-start;
  height: var(--tabbar-content-height);
  padding-bottom: var(--tabbar-padding-bottom);
  box-sizing: content-box;
  background: var(--bg-white);
  border-radius: var(--tabbar-radius-top) var(--tabbar-radius-top) 0 0;
  box-shadow: var(--shadow-float);
  /* 底部安全区：iPhone 的 home indicator */
  padding-bottom: calc(var(--tabbar-padding-bottom) + env(safe-area-inset-bottom));
}

.tabbar__item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  padding-top: 18rpx;
  position: relative;
  z-index: 2;   /* 压在凸起圆之上，避免圆盖住相邻 tab 的点击区 */
}

/* 凸起圆占一个专属位置，但不渲染任何内容 */
.tabbar__item--placeholder {
  pointer-events: none;
}

.tabbar__label {
  font-size: var(--font-xs);
  line-height: 24rpx;
  margin-top: 6rpx;
  color: var(--text-muted);
}

.tabbar__label--active {
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

/* 圆下沿与其它 tab 的文字下沿对齐：用定位表达，不写死数值。
   以后改底栏高度或字号，两者不会跑偏。（spec §6.3） */
.tabbar__raised {
  position: absolute;
  left: 50%;
  bottom: calc(var(--tabbar-padding-bottom) + env(safe-area-inset-bottom));
  transform: translateX(-50%);
  width: var(--tabbar-raised-size);
  height: var(--tabbar-raised-size);
  border-radius: var(--radius-circle);
  background: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-hero);
  z-index: 1;
}
</style>
```

- [ ] **Step 3: 给 5 个 tab 页加选中态同步**

自定义 tabBar 是每个页面各自渲染的一份实例，不共享状态。每个 tab 页的 `onShow` 里写一行：

```ts
onShow(() => {
  uni.setStorageSync('tabbar_selected', 2)   // 各页写自己的索引
})
```

索引：首页 `0`、案例 `1`、客服 `2`、商品 `3`、我的 `4`。

**客服页（`pages/ai-assistant/index`）例外**：spec §2 #12 定的是客服页**不显示**底栏（输入栏占住底部，聊天页保持沉浸）。它的处理见 Task 13，本任务只要保证其余 4 页写对索引。

若某页已有 `onShow`，把这一行加进去；没有就从 `@dcloudio/uni-app` 引入 `onShow` 再写。

- [ ] **Step 4: 给 4 个显示底栏的 tab 页加底部留白**

给首页、案例、商品、我的这 4 个页面的**根元素**挂上 Task 3 定义的 `.has-custom-tabbar` 类。例如首页模板最外层：

```vue
<view class="page has-custom-tabbar">
```

（若根元素已有别的 class，追加即可；不要另起一个包裹层。）

- [ ] **Step 5: 起开发服务，逐项确认**

`npm run dev:mp-weixin`，在开发者工具里确认：

1. 底栏两角有 24rpx 圆角，上沿有一条向上的淡阴影
2. 中间是珊瑚色的凸起圆，白色客服图标，**没有白色描边**，只高出栏顶一点点
3. 圆的**下沿与其它 tab 的文字下沿齐平**
4. 点第 1 / 2 / 4 / 5 个 tab 都能正确切换，选中项图标变珊瑚色实心、文字加粗变珊瑚色
5. 点凸起圆进入客服页
6. **每个 tab 页滚到底，最后一行内容不被底栏盖住**（这是 `.has-custom-tabbar` 在起作用）
7. 滑动手势：底栏固定在底部不跟着滚

真机上再扫一次码，重点看第 2 条和第 6 条——`env(safe-area-inset-bottom)` 在真机上才有非零值，模拟器看不出来。

- [ ] **Step 6: 提交**

```bash
git add miniapp/src/custom-tab-bar/index.vue miniapp/src/pages.json \
        miniapp/src/pages/home/index.vue miniapp/src/pages/cases/index.vue \
        miniapp/src/pages/products/index.vue miniapp/src/pages/mine/index.vue
git commit -m "$(cat <<'EOF'
feat(miniapp): 自定义 tabBar 与凸起客服入口

原生 tabBar 画不出凸起圆，也无法只给单个 tab 去文字，所以换
"custom": true。tab 顺序按设计定为 首页/案例/[蓓贝客服]/商品/我的，
客服居中做成凸起圆。

顺带清掉 list 里全部 iconPath/selectedIconPath：旧值本身就是坏的
（10 个 PNG 齐全，但 selectedIconPath 全指向非选中图标），
自定义 tabBar 也不读它们。

凸起圆的下沿用 bottom: calc(--tabbar-padding-bottom + safe-area)
表达，不写死数值——圆下沿要对齐其它 tab 的文字下沿，以后改底栏
高度或字号时两者不会跑偏。

各 tab 页根元素挂 .has-custom-tabbar 预留底栏高度，否则最后一行
内容会被凸起圆和底栏盖住。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: 演示数据层

Spec §8.2。生产库数据稀薄，5 个 tab 页的真实效果无法验收；同时空状态是用户真实会看到的状态，两种都要能看。

**Files:**
- Create: `miniapp/src/mock/demo-data.ts`
- Create: `miniapp/src/mock/fallback.ts`
- Create: `miniapp/.env`、`miniapp/.env.production`
- Test: `miniapp/src/utils/__tests__/fallback.test.ts`

> 测试放在 `utils/__tests__/` 而不是 `mock/__tests__/`——`vitest.config.ts` 的 `include` 只收 `src/{utils,api,stores}/__tests__/`。放进 `mock/` 会被静默跳过。

**Interfaces:**
- Consumes: `ProductListItem`（`api/products.ts`）、`DesignCase`（`api/cases.ts`）、`Category`（`api/types.ts`）
- Produces:
  - `demo-data.ts`：`DEMO_CATEGORIES: Category[]`、`DEMO_PRODUCTS: ProductListItem[]`、`DEMO_CASES: DesignCase[]`、`DEMO_PROMOTIONS: { id: string; title: string; type: string; rules: Record<string, unknown> }[]`、`DEMO_QUICK_QUESTIONS: string[]`
  - `fallback.ts`：`isFallbackEnabled(): boolean`、`applyFallback<T>(data: T[] | null | undefined, demo: T[]): T[]`

- [ ] **Step 1: 写失败测试**

创建 `miniapp/src/utils/__tests__/fallback.test.ts`：

```ts
import { describe, it, expect, vi, afterEach } from 'vitest'
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

  // 这条是本模块存在的主要理由：请求失败时兜底会掩盖真实故障。
  // 失败在调用方表现为 catch 分支，不会走到这里 —— 见下面「失败不替换」的说明用例。
  it('请求失败时调用方走 catch，不会调用本函数', () => {
    const calls: unknown[] = []
    const page = async (fetch: () => Promise<any[]>) => {
      try {
        const list = await fetch()
        return applyFallback(list, DEMO_PRODUCTS)
      } catch {
        return []          // 失败保持空 -> 页面渲染错误态，不盖假数据
      }
    }
    return Promise.all([
      page(async () => { throw new Error('network') }).then((r) => {
        expect(r).toEqual([])
        expect(calls).toHaveLength(0)
      }),
      page(async () => []).then((r) => {
        expect(r).toBe(DEMO_PRODUCTS)
      }),
    ])
  })
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
```

- [ ] **Step 2: 跑测试，确认失败**

```bash
cd miniapp && npx vitest run src/utils/__tests__/fallback.test.ts
```

预期：**FAIL** —— `Failed to resolve import "../../mock/fallback"`。

- [ ] **Step 3: 写 `demo-data.ts`**

创建 `miniapp/src/mock/demo-data.ts`。数据形态必须与真实接口一致（字段名、类型），否则 `vue-tsc` 会报错，而它正是这里唯一的类型安全网。

```ts
/**
 * 开发期演示数据。
 *
 * 生产库目前基本是空的（商品 total = 0、分类 = []、案例 total = 0），
 * 设计在「满负荷」下长什么样根本没法验收。这份数据只解决验收问题，
 * 由 VITE_DEMO_FALLBACK 控制，生产构建默认关闭。
 *
 * 字段与真实接口一一对应，类型由 api/ 下的接口约束 —— 对不上会编译报错。
 */
import type { Category } from '../api/types'
import type { ProductListItem } from '../api/products'
import type { DesignCase } from '../api/cases'

export const DEMO_CATEGORIES: Category[] = [
  { id: 'demo-c1', parent_id: null, name: '婴童服饰', icon: null, sort_order: 1, status: 'active', children: [] },
  { id: 'demo-c2', parent_id: null, name: '喂养用品', icon: null, sort_order: 2, status: 'active', children: [] },
  { id: 'demo-c3', parent_id: null, name: '寝居出行', icon: null, sort_order: 3, status: 'active', children: [] },
  { id: 'demo-c4', parent_id: null, name: '洗护用品', icon: null, sort_order: 4, status: 'active', children: [] },
  { id: 'demo-c5', parent_id: null, name: '玩具早教', icon: null, sort_order: 5, status: 'active', children: [] },
]

function product(
  id: string, name: string, age: string, minQty: number,
  priceMin: number, priceMax: number,
): ProductListItem {
  return {
    id, name, images: [], age_range: age, safety_certifications: [{ name: '3C认证' }],
    is_virtual: false, stock: 999, min_order_qty: minQty, status: 'on_sale',
    price_min: priceMin, price_max: priceMax,
  }
}

export const DEMO_PRODUCTS: ProductListItem[] = [
  product('demo-p1', '纯棉长袖连体衣 新生儿爬服', '0-3岁', 10, 33.44, 38),
  product('demo-p2', '宽口径玻璃奶瓶 240ml', '0-3岁', 12, 35.7, 42),
  product('demo-p3', '硅胶辅食碗勺套装', '0-3岁', 24, 13.6, 16),
  product('demo-p4', '实木多功能婴儿床', '0-3岁', 3, 187.2, 260),
  product('demo-p5', '超薄透气纸尿裤 L 码', '0-3岁', 30, 46.4, 58),
  product('demo-p6', '大颗粒益智积木 80 粒', '3-6岁', 20, 41.6, 52),
  product('demo-p7', '轻便折叠婴儿推车', '0-3岁', 4, 288, 380),
  product('demo-p8', '婴儿洗发沐浴二合一 500ml', '0-3岁', 24, 17.6, 22),
]

function designCase(
  id: string, title: string, area: string, styles: string[], categories: string[],
  featured: boolean,
): DesignCase {
  return {
    id, title, description: '', images: [],
    category_tags: categories, style_tags: styles,
    store_area_range: area, is_featured: featured, created_at: null,
  }
}

export const DEMO_CASES: DesignCase[] = [
  designCase('demo-k1', '北欧风儿童房整体方案', '50-100㎡', ['ins风', '自然原木'], ['儿童房'], true),
  designCase('demo-k2', '蒙氏游戏区动线设计', '50-100㎡', ['ins风', '卡通童趣'], ['游戏区'], true),
  designCase('demo-k3', '连锁母婴生活馆标准店', '200㎡+', ['简约现代'], ['母婴生活馆'], true),
  designCase('demo-k4', '婴童游泳馆空间方案', '100-200㎡', ['简约现代'], ['婴童游泳馆'], true),
  designCase('demo-k5', '童趣儿童乐园主题店', '200㎡+', ['卡通童趣'], ['儿童乐园'], false),
  designCase('demo-k6', '自然原木系亲子空间', '50-100㎡', ['自然原木'], ['儿童房'], false),
]

/** 形状对齐 GET /promotions/active 的返回 */
export const DEMO_PROMOTIONS = [
  { id: 'demo-a1', title: '春季订货会 · 全场满减', type: 'full_reduction',
    rules: { threshold: 500000, reduce: 80000 } },
  { id: 'demo-a2', title: '奶粉纸尿裤专享折扣', type: 'discount',
    rules: { rate: 0.85 } },
  { id: 'demo-a3', title: '新品首发 · 连体衣限时价', type: 'flash_sale',
    rules: { price: 3200, limit_qty: 500 } },
]

export const DEMO_QUICK_QUESTIONS = [
  '起订量是多少？',
  '多久能发货？',
  '可以定制 LOGO 吗？',
]
```

> 已核实的类型（`api/types.ts` 与 `api/products.ts`），不要凭印象改：
> - `Category = { id, parent_id: string|null, name, icon: string|null, sort_order, status, children }`
> - `ProductListItem = { id, name, images, age_range: string|null, safety_certifications, is_virtual, stock: number|null, min_order_qty, status, price_min, price_max }` —— `product()` 辅助函数逐字段对齐了这个形状
> - `DesignCase = { id, title, description: string|null, images, category_tags, style_tags, store_area_range: string|null, is_featured, created_at: string|null }` —— **注意没有 `age_range`**，后端 `CaseListOut` 里也没有

- [ ] **Step 4: 写 `fallback.ts`**

```ts
/**
 * 演示数据兜底判定。
 *
 * 两条规则，都很要紧：
 *
 * 1. **只在空集合时兜底。** 请求失败时不兜底 —— 失败在调用方表现为
 *    catch 分支，页面渲染错误态。用假数据盖住真实故障，会让线上问题
 *    一直看不见。
 * 2. **开关缺失时按关闭处理。** 上线漏配的后果是「页面空」（用户看到
 *    空状态），比「线上展示假数据」轻得多。
 */
import { DEMO_CASES, DEMO_PRODUCTS } from './demo-data'

export function isFallbackEnabled(): boolean {
  // 只认严格的字符串 'true'。'1' / 'TRUE' / 'yes' 一律当关闭 ——
  // 这个开关决定线上要不要展示假数据，宁可漏开也不要误开。
  return import.meta.env.VITE_DEMO_FALLBACK === 'true'
}

/**
 * 空集合时用演示数据替换。纯函数，无副作用。
 *
 * @param data 接口返回的数组（可能是空数组 / null / undefined）
 * @param demo 对应的演示数据
 */
export function applyFallback<T>(data: T[] | null | undefined, demo: T[]): T[] {
  if (!isFallbackEnabled()) return data ?? []
  if (!data || data.length === 0) return demo
  return data
}

/** 各分区常用组合，省得每个页面都 import 一遍演示数据。 */
export const fallbackFor = {
  products: (data: unknown[] | null | undefined) => applyFallback(data as any, DEMO_PRODUCTS),
  cases: (data: unknown[] | null | undefined) => applyFallback(data as any, DEMO_CASES),
}
```

- [ ] **Step 5: 加环境变量文件**

创建 `miniapp/.env`：

```
# 开发期：接口返回空集合时用演示数据兜底，方便验收设计的满负荷状态
VITE_DEMO_FALLBACK=true
```

创建 `miniapp/.env.production`：

```
# 生产：关闭兜底。线上绝不展示假数据。
VITE_DEMO_FALLBACK=false
```

- [ ] **Step 6: 跑测试，确认通过**

```bash
cd miniapp && npx vitest run src/utils/__tests__/fallback.test.ts
```

预期：7 个用例全 **PASS**。

- [ ] **Step 7: 类型检查 + 全量测试**

```bash
cd miniapp && npx vue-tsc --noEmit && npm test
```

预期：都通过。演示数据的字段名只要和真实接口差一个，`vue-tsc` 就会报出来。

- [ ] **Step 8: 确认 `.env` 没被 git 忽略掉**

```bash
cd miniapp && git check-ignore -v .env .env.production || echo "两个文件都会被提交（预期如此）"
```

若被忽略，在 `miniapp/.gitignore` 里加例外。**注意**：这两个文件里没有密钥，只有开关，所以提交是安全的；如果以后有人往里面加密钥，要立刻移出去。

- [ ] **Step 9: 提交**

```bash
git add miniapp/src/mock/ miniapp/src/utils/__tests__/fallback.test.ts miniapp/.env miniapp/.env.production
git commit -m "$(cat <<'EOF'
feat(miniapp): 开发期演示数据兜底层

生产库基本是空的（商品 total=0、分类=[]、案例 total=0），设计在
满负荷下长什么样没法验收。

两条规则钉在单测里：
1. 只在「空集合」时兜底。请求失败不兜底——失败在调用方是 catch
   分支，保持错误态可见。用假数据盖住真实故障会让线上问题
   一直看不见。
2. 开关缺失时按关闭处理。上线漏配的后果是「页面空」（用户看到
   空状态），比「线上展示假数据」轻得多。

演示数据字段与真实接口一一对应，靠 vue-tsc 兜住漂移。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 10: 首页

Spec §5.1。首页改动最大（现 802 行），结构从「banner 轮播 + 分类 + 推荐 + 案例 + 热门」换成「品牌头图 + 上叠白卡（入口/分类/权益）+ 推荐 + 案例横滑 + 品牌活动 + 热门」。

**Files:**
- Modify: `miniapp/src/pages/home/index.vue`（重写模板与样式；`<script setup>` 按下面的清单增删）

**Interfaces:**
- Consumes: `BrandHero`、`SurfaceCard`、`SectionHeader`、`EntryGrid`、`CircleEntryRow`、`BenefitCard`、`BannerCard`、`ProductCard`、`PageLoading`、`EmptyState`（Task 4/5/6/7）；`applyFallback`（Task 9）；`iconForEmoji`（Task 2）；`getCategories` / `getHotProducts` / `getNewProducts` / `getProductList`（`api/products.ts`）；`getCaseList`（`api/cases.ts`）
- Produces: 无对外接口

- [ ] **Step 1: 模板重写成这个结构**

自上而下六个分区。`SectionHeader` 的 `more` 事件接到既有的 `goToMoreProducts` / `goToMoreCases`。

```vue
<template>
  <view class="page has-custom-tabbar">
    <BrandHero
      title="蓓贝婴童"
      slogan="源头工厂 · 一件代发"
      show-login
      show-search
      @login="onLogin"
      @search="onHeroSearch"
    />

    <!-- ② 上叠白卡：入口 / 分类 / 权益 -->
    <SurfaceCard overlap>
      <EntryGrid :items="ENTRY_ITEMS" @select="onEntrySelect" />

      <view class="home__divider" />

      <CircleEntryRow :items="categoryEntries" @select="onCategorySelect" />

      <view class="home__divider" />

      <BenefitCard
        :main="BENEFIT_MAIN"
        :side="BENEFIT_SIDE"
        @main-tap="goToMember"
        @side-tap="onBenefitSide"
      />
    </SurfaceCard>

    <!-- ③ 蓓贝推荐 -->
    <SectionHeader title="蓓贝推荐" more="查看更多" @more="goToMoreProducts" />
    <view v-if="sectionErrors.recommend" class="home__section-error" @tap="fetchRecommendProducts">
      <AppIcon name="reload" :size="30" tone="muted" />
      <text class="home__section-error-text">加载失败，点击重试</text>
    </view>
    <scroll-view v-else class="home__scroll" scroll-x :show-scrollbar="false" enhanced>
      <view class="home__scroll-inner">
        <view v-for="p in recommendProducts" :key="p.id" class="home__scroll-item">
          <ProductCard :product="p" @click="goToProduct" />
        </view>
      </view>
    </scroll-view>

    <!-- ④ 设计案例：横滑横图卡 -->
    <SectionHeader title="设计案例" more="查看更多" @more="goToMoreCases" />
    <scroll-view class="home__scroll" scroll-x :show-scrollbar="false" enhanced>
      <view class="home__scroll-inner">
        <BannerCard
          v-for="c in caseItems"
          :key="c.id"
          :title="c.title"
          :subtitle="[c.store_area_range, (c.style_tags || [])[0]].filter(Boolean).join(' · ')"
          :image="c.images?.[0]"
          width="520rpx"
          @tap="goToCase(c.id)"
        />
      </view>
    </scroll-view>

    <!-- ⑤ 品牌活动：满宽横图卡 -->
    <SectionHeader title="品牌活动" />
    <view class="home__banners">
      <BannerCard
        v-for="promo in promotions"
        :key="promo.id"
        :title="promo.title"
        :subtitle="promoSubtitle(promo)"
        action="立即参与"
        @tap="onPromotionTap"
      />
    </view>

    <!-- ⑥ 热门商品 2 列瀑布流 -->
    <SectionHeader title="热门商品" />
    <view class="home__grid">
      <ProductCard
        v-for="p in hotProducts"
        :key="p.id"
        class="home__grid-item"
        :product="p"
        @click="goToProduct"
      />
    </view>

    <EmptyState v-if="!hotLoadingMore && hotProducts.length === 0 && !sectionErrors.hot"
      text="暂无商品" description="换个分类看看，或联系客服获取最新货源" />
    <view v-if="hotLoadingMore" class="home__loading-more">加载中…</view>
    <view v-if="hotNoMore && hotProducts.length" class="home__loading-more">已经到底了</view>

    <PageLoading v-if="pageState === 'loading'" />
    <EmptyState v-if="pageState === 'error'" text="加载失败" description="检查网络后点击重试"
      @tap="retryAll" />
  </view>
</template>
```

- [ ] **Step 2: `<script setup>` 的增删**

**删掉**：

- banner 轮播相关：`BANNER_GRADIENTS`、`BANNER_EMOJIS`、`Banner` 接口、`banners`、`fetchBanners`，以及 `loadAllData` / `onPullDownRefresh` 里对 `fetchBanners()` 的调用
- `goToCategory(cat)` —— 被上面的 `onCategorySelect` 取代（它用 `navigateTo` 跳 tabBar 页，本来就点不动）
- `goToSearch()` —— 被上面的 `onHeroSearch(kw)` 取代（同样是 `navigateTo` 跳 tabBar 页）
- `categoryBgColor(index)` —— 旧分类块用的，新模板不再需要
- `statusBarHeight` / `safeBottom` —— 头图自己读 `appStore.statusBarHeight`（Task 5），页面不用管

**保留不动**（已核实存在）：`pageState`、`searchKeyword`、`onSearch`、`onCartTap`、`categories`、`fetchCategories`、`recommendProducts`、`fetchRecommendProducts`、`caseItems`、`fetchCases`、`hotProducts` / `hotPage` / `hotTotal` / `hotLoadingMore` / `hotNoMore` / `fetchHotProducts` / `loadMoreHot`、`loadAllData`、`retryAll`、`onLoad` / `onPullDownRefresh` / `onReachBottom`、`goToProduct(id)` / `goToCase(id)` / `goToMoreProducts` / `goToMoreCases`。

`statusBarHeight` / `safeBottom` 现在没有消费者了——头图自己读 `appStore.statusBarHeight`（Task 5），页面不用管。这两个 computed 直接删掉。该页的 `navigationStyle` 由 Task 8 改成 `custom`。

**新增**：

```ts
import AppIcon from '../../components/AppIcon.vue'
import BrandHero from '../../components/BrandHero.vue'
import SurfaceCard from '../../components/SurfaceCard.vue'
import SectionHeader from '../../components/SectionHeader.vue'
import EntryGrid from '../../components/EntryGrid.vue'
import CircleEntryRow from '../../components/CircleEntryRow.vue'
import BenefitCard from '../../components/BenefitCard.vue'
import BannerCard from '../../components/BannerCard.vue'
import { onShow } from '@dcloudio/uni-app'
import { applyFallback } from '../../mock/fallback'
import { DEMO_PROMOTIONS } from '../../mock/demo-data'
import http from '../../api/request'
import { iconForEmoji } from '../../utils/icon-map'

// 自定义 tabBar 是每页各渲染一份实例，不共享状态 —— 进页面时同步选中项
onShow(() => {
  uni.setStorageSync('tabbar_selected', 0)
})

// ── 固定文案（不依赖后端） ──────────────────────────────────────────────
const ENTRY_ITEMS = [
  { icon: 'bag-fill',   title: '一件代发', subtitle: '无起批压力' },
  { icon: 'rmb-circle', title: '批量询价', subtitle: '量大更优' },
  { icon: 'photo',      title: '定制打样', subtitle: '专属 LOGO' },
]

const BENEFIT_MAIN = { title: '会员权益', desc: '等级越高折扣越低\n账期最长 60 天', action: '查看权益' }
const BENEFIT_SIDE = [
  { icon: 'integral', title: '积分抽奖', desc: '即将上线' },
  { icon: 'gift',     title: '新品首发', desc: '优先订货' },
]

// ── 分类入口：后端 categories -> CircleEntryRow 的 items 形状 ────────────
// 后端 Category 没有 icon 字段值（icon 为 null），图标按索引轮换一组
// 通用品类图标，比让所有分类共用一个图标更有信息量。
const CATEGORY_ICONS = ['bag', 'coupon', 'home', 'photo', 'integral']

const categoryEntries = computed(() =>
  (categories.value || []).map((c, i) => ({
    id: c.id,
    icon: CATEGORY_ICONS[i % CATEGORY_ICONS.length],
    label: c.name,
  })),
)

function onEntrySelect(index: number) {
  uni.showToast({ title: ENTRY_ITEMS[index].title, icon: 'none' })
}

function onCategorySelect(index: number) {
  const cat = categoryEntries.value[index]
  if (!cat) return
  // /pages/products/index 是 tabBar 页。既有的 goToCategory 用的是
  // navigateTo，而 navigateTo 跳 tabBar 页在微信里会**静默失败**——
  // 点了没反应。只能 switchTab，但 switchTab 不支持 query 传参，
  // 所以把 category_id 写进 storage，由商品页在 onShow 里取。
  //
  // 这个 bug 与改版无关，但新首页把分类横滚做成了主入口，留着它会
  // 立刻暴露。商品页本任务之后也会重写（Task 11），顺手修掉。
  uni.setStorageSync('products_pending_category', cat.id)
  uni.switchTab({ url: '/pages/products/index' })
}

function goToMember() { uni.navigateTo({ url: '/pages/mine/member/index' }) }

function onBenefitSide(index: number) {
  uni.showToast({ title: index === 0 ? '积分抽奖即将上线' : '新品首发敬请期待', icon: 'none' })
}

// /pages/mine/index 是 tabBar 页，同样只能用 switchTab（navigateTo 会静默失败）
function onLogin() { uni.switchTab({ url: '/pages/mine/index' }) }

// 原有的 goToSearch 也是 navigateTo('/pages/products/index?focus=1') —— 同样
// 跳不动 tabBar 页。新头图的搜索框带回关键词，一并走 storage + switchTab。
function onHeroSearch(kw: string) {
  if (kw.trim()) uni.setStorageSync('products_pending_keyword', kw.trim())
  uni.switchTab({ url: '/pages/products/index' })
}

// ── 品牌活动 ────────────────────────────────────────────────────────────
const promotions = ref<typeof DEMO_PROMOTIONS>([])

async function fetchPromotions() {
  try {
    const res: any = await http.get('/promotions/active')
    // 空集合兜底；请求失败走 catch，保持空 -> 该分区不渲染，但不盖假数据
    promotions.value = applyFallback(res.data, DEMO_PROMOTIONS)
  } catch {
    promotions.value = []
  }
}

function promoSubtitle(promo: { type: string; rules: any }): string {
  const r = promo.rules || {}
  if (promo.type === 'full_reduction') {
    return `满 ${Math.round(r.threshold / 100)} 减 ${Math.round(r.reduce / 100)}`
  }
  if (promo.type === 'discount') return `${(r.rate * 10).toFixed(1)} 折`
  if (promo.type === 'flash_sale') return `限时价 ¥${(r.price / 100).toFixed(0)}`
  return ''
}

function onPromotionTap() { goToMoreProducts() }
```

把 `fetchPromotions()` 加进 `loadAllData` 和 `onPullDownRefresh` 的 `Promise.all` 里（`fetchBanners` 已经删掉，用它腾出的位置）。

两个分区接演示数据兜底：

```ts
// fetchRecommendProducts 里
recommendProducts.value = applyFallback(res.data, DEMO_PRODUCTS)

// fetchCases 里
caseItems.value = applyFallback(res.data.list, DEMO_CASES)
```

（对应 import 补 `DEMO_PRODUCTS` / `DEMO_CASES`。）

- [ ] **Step 3: `<style scoped>` 新增这些类**

```scss
.page {
  min-height: 100vh;
  background: var(--bg-primary);
}

.home__divider {
  height: 1rpx;
  background: var(--border-light);
  margin: var(--space-lg) 0;
}

/* 横滑容器：内层 inline-flex + 首尾 padding，让卡片能滑出屏幕边缘 */
.home__scroll {
  width: 100%;
  white-space: nowrap;
}

.home__scroll-inner {
  display: inline-flex;
  gap: var(--space-md);
  padding: 0 var(--space-lg);
}

.home__scroll-item {
  width: 260rpx;
  flex-shrink: 0;
}

.home__banners {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: 0 var(--space-lg);
}

.home__grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  padding: 0 var(--space-lg);
}

.home__grid-item {
  width: calc((100% - var(--space-md)) / 2);
}

.home__section-error {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
  padding: var(--space-xl);
  color: var(--text-muted);
}

.home__section-error-text {
  font-size: var(--font-sm);
}

.home__loading-more {
  text-align: center;
  padding: var(--space-lg);
  font-size: var(--font-sm);
  color: var(--text-muted);
}
```

- [ ] **Step 4: 类型检查**

```bash
cd miniapp && npx vue-tsc --noEmit
```

预期：无错误。重点看 `ProductCard` 的 prop 名（Task 7 Step 1 抄下来的真实名字）和 `Category` 的字段。

- [ ] **Step 5: 在两种数据状态下各看一遍**

```bash
cd miniapp && npm run dev:mp-weixin
```

- **演示数据态**（`.env` 里 `VITE_DEMO_FALLBACK=true`，且后端为空）：头图上叠白卡、三个入口、分类圆行、权益双栏、推荐横滑、案例横滑（第二张露边）、品牌活动满宽卡、热门两列瀑布流
- **真实数据态**：接上已完成 Task 5（后端种子）的环境，把 `.env` 改成 `VITE_DEMO_FALLBACK=false` 重新构建，确认真实数据能渲染

两种状态都要滚到底，确认**最后一行不被底栏盖住**。

- [ ] **Step 6: 提交**

```bash
git add miniapp/src/pages/home/index.vue
git commit -m "$(cat <<'EOF'
feat(miniapp): 首页按新布局语言重建

结构改为 品牌头图 -> 上叠白卡(入口/分类/权益) -> 蓓贝推荐 ->
设计案例横滑 -> 品牌活动 -> 热门商品，照素材的入口聚合型信息架构。

删掉原来的 banner 轮播（渐变块 + emoji 拼的假 banner），
品牌活动改由 /promotions/active 驱动，接口挂掉时该分区不渲染。

横滑区用 scroll-view + 内层 inline-flex，首尾 padding 加在内层，
让卡片能滑出屏幕边缘从而露出第二张，是「还有更多」的天然提示。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 11: 商品页

Spec §5.2。现 445 行，结构从「搜索 + 分类 + 排序 + 瀑布流」换成「品牌头图（含搜索）+ 上叠白卡（分类横滚）+ 排序条 + 瀑布流」。

**Files:**
- Modify: `miniapp/src/pages/products/index.vue`

**Interfaces:**
- Consumes: `BrandHero`（`show-search`）、`SurfaceCard`、`ProductCard`、`PageLoading`、`EmptyState`、`applyFallback`、`getProductList` / `getCategories`
- Produces: 无

- [ ] **Step 1: 模板重写**

```vue
<template>
  <view class="page has-custom-tabbar">
    <BrandHero
      title="商品"
      :compact="true"
      show-search
      @search="onSearchConfirm"
    />

    <!-- 分类横滚，选中态：品牌色文字 + 下划短线
         注：spec §4.1 的组件表把 CircleEntryRow 的使用页面写成「首页、商品」，
         但 §5.2 的页面设计写的是「品牌色文字 + 下划短线」。两处不一致时以
         §5.2 为准 —— 它是页面级的、更具体。商品页的分类是文字 tab 条，
         不用圆形图标（圆形入口在首页已经用过了，重复会显得单调）。 -->
    <SurfaceCard overlap :padding="'0'">
      <scroll-view class="cat" scroll-x :show-scrollbar="false" enhanced>
        <view class="cat__inner">
          <view
            v-for="c in categoryTabs"
            :key="c.id ?? 'all'"
            class="cat__item"
            @tap="onCategorySelect(c.id)"
          >
            <text class="cat__label" :class="{ 'cat__label--active': activeCategoryId === c.id }">
              {{ c.name }}
            </text>
            <view v-if="activeCategoryId === c.id" class="cat__underline" />
          </view>
        </view>
      </scroll-view>
    </SurfaceCard>

    <!-- 排序条 -->
    <view class="sort">
      <view
        v-for="s in SORTS"
        :key="s.value"
        class="sort__item"
        @tap="onSortSelect(s.value)"
      >
        <text class="sort__label" :class="{ 'sort__label--active': sort === s.value }">
          {{ s.label }}
        </text>
        <AppIcon v-if="s.value === 'price_asc' || s.value === 'price_desc'"
          name="arrow-downward" :size="24"
          :tone="sort === s.value ? 'primary' : 'muted'"
          :class="{ 'sort__arrow--asc': s.value === 'price_asc' }" />
      </view>
    </view>

    <view class="grid">
      <ProductCard
        v-for="p in products"
        :key="p.id"
        class="grid__item"
        :product="p"
        @click="goToProduct"
      />
    </view>

    <EmptyState v-if="!loading && !loadingMore && products.length === 0 && !errorMsg"
      text="没有找到商品" description="换个分类或关键词试试" />
    <view v-if="loadingMore" class="list-foot">加载中…</view>
    <view v-else-if="!hasMore && products.length" class="list-foot">已经到底了</view>

    <PageLoading v-if="loading" />
    <EmptyState v-if="errorMsg" :text="errorMsg" description="检查网络后点击重试" @tap="loadProducts(true)" />
  </view>
</template>
```

- [ ] **Step 2: `<script setup>` 增删**

**保留不动**：现有的 `loading` / `loadingMore` / `hasMore` / `page` / `keyword` / `errorMsg` / `products` / `loadProducts` / 触底加载 / `goToProduct` 等全部既有逻辑。

**新增**：

```ts
import { onShow } from '@dcloudio/uni-app'
import AppIcon from '../../components/AppIcon.vue'
import BrandHero from '../../components/BrandHero.vue'
import SurfaceCard from '../../components/SurfaceCard.vue'

onShow(() => {
  uni.setStorageSync('tabbar_selected', 3)

  // 首页的分类横滚和搜索框用 storage 传参（switchTab 不支持 query）。
  // 取完立刻删，否则用户下次从 tabBar 进来会又被筛一次。
  const pendingCat = uni.getStorageSync('products_pending_category')
  const pendingKw = uni.getStorageSync('products_pending_keyword')
  if (pendingCat || pendingKw) {
    if (pendingCat) {
      uni.removeStorageSync('products_pending_category')
      activeCategoryId.value = pendingCat
    }
    if (pendingKw) {
      uni.removeStorageSync('products_pending_keyword')
      keyword.value = pendingKw
    }
    loadProducts(true)
  }
})

const SORTS = [
  { label: '综合',  value: undefined },
  { label: '销量',  value: 'sales_desc' },
  { label: '价格',  value: 'price_desc' },
  { label: '最新',  value: 'newest' },
] as const

const sort = ref<'newest' | 'sales_desc' | 'price_asc' | 'price_desc' | undefined>(undefined)
const activeCategoryId = ref<string | undefined>(undefined)
const categories = ref<CategoryType[]>([])

const categoryTabs = computed(() => [{ id: undefined, name: '全部' }, ...categories.value])

async function fetchCategories() {
  try {
    const res = await getCategories()
    categories.value = res.data || []
  } catch {
    categories.value = []
  }
}

function onSortSelect(value: typeof sort.value) {
  // 重复点「价格」在升降序之间切换
  if (value === 'price_desc' && sort.value === 'price_desc') {
    sort.value = 'price_asc'
  } else {
    sort.value = value
  }
  loadProducts(true)
}

function onCategorySelect(id: string | undefined) {
  activeCategoryId.value = id
  loadProducts(true)
}

// BrandHero 的 search 事件带回关键词（SearchBar 的 confirm 才触发，
// 输入过程中不触发——避免每敲一个字打一次接口）
function onSearchConfirm(kw: string) {
  keyword.value = kw
  loadProducts(true)
}
```

把 `sort` / `activeCategoryId` 接进 `loadProducts` 的 params（它们已经是既有的 `ProductListParams` 字段）：

```ts
    if (sort.value) params.sort = sort.value
    if (activeCategoryId.value) params.category_id = activeCategoryId.value
```

`onLoad` 里补 `fetchCategories()`。若页面已有分类加载逻辑，改造成上面这个形状而不是并存两套。

- [ ] **Step 3: 样式**

```scss
.page { min-height: 100vh; background: var(--bg-primary); }

.cat { width: 100%; white-space: nowrap; }
.cat__inner { display: inline-flex; gap: var(--space-xl); padding: var(--space-lg); }
.cat__item { display: flex; flex-direction: column; align-items: center; }
.cat__label { font-size: var(--font-base); color: var(--text-secondary); }
.cat__label--active { color: var(--color-primary); font-weight: var(--font-weight-semibold); }
.cat__underline {
  width: 32rpx; height: 4rpx; border-radius: 2rpx;
  background: var(--color-primary); margin-top: var(--space-xs);
}

.sort {
  display: flex; align-items: center; justify-content: space-around;
  padding: var(--space-lg); margin-top: var(--space-lg);
}
.sort__item { display: flex; align-items: center; gap: var(--space-2xs); }
.sort__label { font-size: var(--font-base); color: var(--text-secondary); }
.sort__label--active { color: var(--color-primary); font-weight: var(--font-weight-semibold); }
.sort__arrow--asc { transform: rotate(180deg); }

.grid { display: flex; flex-wrap: wrap; gap: var(--space-md); padding: 0 var(--space-lg); }
.grid__item { width: calc((100% - var(--space-md)) / 2); }

.list-foot { text-align: center; padding: var(--space-lg); font-size: var(--font-sm); color: var(--text-muted); }
```

- [ ] **Step 4: 类型检查 + 真机确认**

```bash
cd miniapp && npx vue-tsc --noEmit
```

然后起服务，确认：头图较矮且带搜索框、白卡上叠且分类可横滑、选中分类有珊瑚色下划短线、点「价格」能切换升降序（箭头翻转）、商品两列瀑布流、触底加载正常、滚到底不被底栏盖住。

- [ ] **Step 5: 提交**

```bash
git add miniapp/src/pages/products/index.vue
git commit -m "$(cat <<'EOF'
feat(miniapp): 商品页按新布局语言重建

品牌头图（含搜索）-> 上叠白卡分类横滚 -> 排序条 -> 两列瀑布流。

分类选中态用品牌色文字 + 下划短线，替换原来的实心胶囊。

价格排序在同一按钮上切换升降序，箭头翻转。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 12: 案例页

Spec §5.3。现 305 行。**注意**：本页依赖地基修复计划的 Task 2（标签接口契约），在那之前筛选器只有「全部」。

**Files:**
- Modify: `miniapp/src/pages/cases/index.vue`

**Interfaces:**
- Consumes: `BrandHero`（`show-search`）、`SurfaceCard`、`SectionHeader`、`CaseCard`、`EmptyState`、`applyFallback`、`getCaseList` / `getCaseTags`（地基修复计划 Task 2 产出的 `getCaseTags`）
- Produces: 无

- [ ] **Step 1: 模板重写**

```vue
<template>
  <view class="page has-custom-tabbar">
    <BrandHero
      title="设计案例"
      :compact="true"
      show-search
      @search="onSearchConfirm"
    />

    <!-- 标签筛选 chips -->
    <SurfaceCard overlap>
      <view class="chips">
        <view
          v-for="c in categoryChips"
          :key="c.value ?? 'all'"
          class="chips__item"
          :class="{ 'chips__item--active': activeCategoryTag === c.value }"
          @tap="onCategoryTagSelect(c.value)"
        >
          <text class="chips__label" :class="{ 'chips__label--active': activeCategoryTag === c.value }">
            {{ c.label }}
          </text>
        </view>
      </view>

      <view v-if="styleTags.length" class="chips chips--sub">
        <view
          v-for="s in styleChips"
          :key="s.value ?? 'all-style'"
          class="chips__item chips__item--sm"
          :class="{ 'chips__item--active': activeStyleTag === s.value }"
          @tap="onStyleTagSelect(s.value)"
        >
          <text class="chips__label" :class="{ 'chips__label--active': activeStyleTag === s.value }">
            {{ s.label }}
          </text>
        </view>
      </view>
    </SurfaceCard>

    <SectionHeader title="精选案例" />

    <view class="grid">
      <CaseCard
        v-for="c in cases"
        :key="c.id"
        class="grid__item"
        :caseData="c"
        @click="goToCase"
      />
    </view>

    <EmptyState v-if="!loading && !loadingMore && cases.length === 0 && !errorMsg"
      text="暂无案例" description="我们正在整理更多门店案例，先看看商品吧" />
    <view v-if="loadingMore" class="list-foot">加载中…</view>
    <view v-else-if="!hasMore && cases.length" class="list-foot">已经到底了</view>

    <PageLoading v-if="loading" />
    <EmptyState v-if="errorMsg" :text="errorMsg" description="检查网络后点击重试" @tap="loadCases(true)" />
  </view>
</template>
```

- [ ] **Step 2: `<script setup>` 增删**

**保留不动**：`loading` / `loadingMore` / `hasMore` / `page` / `keyword` / `errorMsg` / `cases` / `loadCases` / 触底加载 / `goToCase`。

**改掉**：`loadTags` 已经在地基修复计划 Task 2 里改成调 `getCaseTags()`。本任务只需把它的两个数组接进 chips。

**新增**：

```ts
import { onShow } from '@dcloudio/uni-app'
import BrandHero from '../../components/BrandHero.vue'
import SurfaceCard from '../../components/SurfaceCard.vue'
import SectionHeader from '../../components/SectionHeader.vue'
import { applyFallback } from '../../mock/fallback'
import { DEMO_CASES } from '../../mock/demo-data'

onShow(() => {
  uni.setStorageSync('tabbar_selected', 1)
})

const categoryChips = computed(() => [
  { value: undefined, label: '全部' },
  ...categoryTags.value.map((t) => ({ value: t, label: t })),
])

const styleChips = computed(() => [
  { value: undefined, label: '全部风格' },
  ...styleTags.value.map((t) => ({ value: t, label: t })),
])

function onCategoryTagSelect(value: string | undefined) {
  activeCategoryTag.value = value ?? ''
  loadCases(true)
}

function onStyleTagSelect(value: string | undefined) {
  activeStyleTag.value = value ?? ''
  loadCases(true)
}

function onSearchConfirm(kw: string) {
  keyword.value = kw
  loadCases(true)
}
```

在 `loadCases` 拿到结果后接演示数据兜底：

```ts
    const list = res.data.list || []
    if (isRefresh || page.value === 1) {
      // 只有第一页兜底。分页追加时若也兜底，「加载更多」会无限重复
      // 同一批演示案例——因为空结果会被替换成完整列表而不是追加 0 条。
      cases.value = applyFallback(list, DEMO_CASES)
    } else {
      cases.value = [...cases.value, ...list]
    }
```

- [ ] **Step 3: 样式**

```scss
.page { min-height: 100vh; background: var(--bg-primary); }

.chips { display: flex; flex-wrap: wrap; gap: var(--space-sm); }
.chips--sub { margin-top: var(--space-md); }

.chips__item {
  background: var(--bg-secondary);
  border-radius: var(--radius-pill);
  padding: 12rpx 28rpx;
}
.chips__item--sm { padding: 8rpx 22rpx; }
.chips__item--active { background: var(--color-primary); }

.chips__label { font-size: var(--font-sm); color: var(--text-secondary); }
.chips__label--active { color: var(--text-white); font-weight: var(--font-weight-semibold); }

.grid { display: flex; flex-wrap: wrap; gap: var(--space-md); padding: 0 var(--space-lg); }
.grid__item { width: calc((100% - var(--space-md)) / 2); }

.list-foot { text-align: center; padding: var(--space-lg); font-size: var(--font-sm); color: var(--text-muted); }
```

- [ ] **Step 4: 真机确认筛选真的生效**

```bash
cd miniapp && npx vue-tsc --noEmit && npm run dev:mp-weixin
```

重点确认：**点一个分类 chip 后列表真的变少了**。这是整个改版里唯一一处「看着正常但实际没生效」的陷阱——`style_tag` 参数名漂移就是这种静默失效。若点了没变化，回去查地基修复计划的 Task 2 Step 7。

- [ ] **Step 5: 提交**

```bash
git add miniapp/src/pages/cases/index.vue
git commit -m "$(cat <<'EOF'
feat(miniapp): 案例页按新布局语言重建

品牌头图（含搜索）-> 上叠白卡双层筛选 chips -> 精选案例瀑布流。

分类与风格分成两行 chips，风格行在无风格标签时不渲染。

演示数据兜底只在第一页做，分页追加不走兜底——否则「加载更多」
会无限重复同一批演示案例。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 13: 蓓贝客服页

Spec §5.4、§2 #8/#12。`pages/ai-assistant/index` 现 419 行，命名从「小暖AI」改成「蓓贝客服」，**且不显示 tabBar**（输入栏占住底部，聊天页保持沉浸）。

**Files:**
- Modify: `miniapp/src/pages/ai-assistant/index.vue`
- Modify: `miniapp/src/pages.json`（该页 `navigationBarTitleText` 改为「蓓贝客服」）

**Interfaces:**
- Consumes: `AppIcon`、`DEMO_QUICK_QUESTIONS`（Task 9）、既有的聊天接口
- Produces: 无

- [ ] **Step 1: 改 `pages.json` 的标题**

`pages/ai-assistant/index` 的 `navigationBarTitleText` 从 `"小暖AI"` 改为 `"蓓贝客服"`。

- [ ] **Step 2: 模板改造**

该页已有 `navigationStyle: "custom"`，保留。四处改动：

1. 自定义导航栏改成「客服头像 + 蓓贝客服 + ● 在线 · 通常 1 分钟内回复」
2. 消息气泡分左右：客服白底、**左上角直角**；用户品牌色底、**右上角直角**
3. 底部加一行快捷问题 chips（`DEMO_QUICK_QUESTIONS`），点击直接发送
4. 输入栏固定在底部——因为有输入栏，**不要**挂 `.has-custom-tabbar`，也不要加自定义 tabBar

气泡样式：

```scss
.bubble {
  max-width: 70%;
  padding: var(--space-md) var(--space-lg);
  font-size: var(--font-base);
  line-height: var(--leading-normal);
}

/* border-radius 四角顺序：上左 / 上右 / 下右 / 下左。
   客服气泡在左，尖角在左上 -> 上左置 0；用户气泡在右，尖角在右上 -> 上右置 0。 */
.bubble--agent { border-radius: 0 var(--radius-md) var(--radius-md) var(--radius-md); }
.bubble--user  { border-radius: var(--radius-md) 0 var(--radius-md) var(--radius-md); }
```

快捷问题 chips：

```vue
<scroll-view class="quick" scroll-x :show-scrollbar="false" enhanced>
  <view class="quick__inner">
    <view v-for="q in quickQuestions" :key="q" class="quick__item" @tap="sendQuick(q)">
      <text class="quick__label">{{ q }}</text>
    </view>
  </view>
</scroll-view>
```

```scss
.quick { width: 100%; padding: var(--space-sm) 0; }
.quick__inner { display: inline-flex; gap: var(--space-sm); padding: 0 var(--space-lg); }
.quick__item { background: var(--bg-white); border-radius: var(--radius-pill); padding: 10rpx 24rpx; }
.quick__label { font-size: var(--font-sm); color: var(--text-secondary); }
```

`sendQuick(q)` 复用该页既有的发送逻辑（不要新写一条发送路径），并 `import { DEMO_QUICK_QUESTIONS } from '../../mock/demo-data'` 后 `const quickQuestions = ref(DEMO_QUICK_QUESTIONS)`。

- [ ] **Step 3: 把页面里的 emoji 换掉**

该页有 3 处 emoji（💬 📦 等）。用 `AppIcon` 替换，图标名查 `iconForEmoji` 或直接写 `EMOJI_TO_ICON` 里对应的名字。

- [ ] **Step 4: 真机确认**

`npm run dev:mp-weixin`，确认：

1. 标题是「蓓贝客服」
2. **页面底部没有 tabBar**，输入栏贴底
3. 客服消息左上角直角、用户消息右上角直角
4. 快捷问题 chips 可横滑、点击能发出消息
5. 用键盘弹起时输入栏不被顶飞

- [ ] **Step 5: 提交**

```bash
git add miniapp/src/pages/ai-assistant/index.vue miniapp/src/pages.json
git commit -m "$(cat <<'EOF'
feat(miniapp): 小暖AI 改为蓓贝客服，重做聊天界面

命名统一为「蓓贝客服」（首页的「小暖推荐」同步改为「蓓贝推荐」）。

页面刻意不显示 tabBar：输入栏占住底部，聊天页保持沉浸。
因此它不挂 .has-custom-tabbar。

气泡的直角用 border-radius 四角顺序表达：客服左上直角、
用户右上直角。emoji 换成 AppIcon。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 14: 我的页

Spec §5.5。现 451 行，是全站 emoji 最多的页面（12 处）。

**Files:**
- Modify: `miniapp/src/pages/mine/index.vue`

**Interfaces:**
- Consumes: `BrandHero`、`SurfaceCard`、`SectionHeader`、`BenefitCard`、`AppIcon`、`useUserStore`（`stores/user.ts`）、`applyFallback`
- Produces: 无

- [ ] **Step 1: 模板重写**

```vue
<template>
  <view class="page has-custom-tabbar">
    <BrandHero
      :title="userStore.isLoggedIn ? (userStore.nickname || '蓓贝会员') : '点击登录'"
      :slogan="userStore.isLoggedIn ? (companyName || '完善企业信息可开通账期') : '登录后查看专属价格'"
      :show-login="!userStore.isLoggedIn"
      @login="handleLogin"
    />

    <!-- 我的订单五宫格 -->
    <SurfaceCard overlap>
      <SectionHeader title="我的订单" more="全部订单" @more="goToOrderList('')" />
      <view class="orders">
        <view v-for="o in ORDER_ENTRIES" :key="o.status" class="orders__item" @tap="goToOrderList(o.status)">
          <view class="orders__icon">
            <AppIcon :name="o.icon" :size="40" tone="primary" />
          </view>
          <text class="orders__label">{{ o.label }}</text>
        </view>
      </view>
    </SurfaceCard>

    <!-- 我的权益 -->
    <view class="benefit-wrap">
      <BenefitCard :main="benefitMain" :side="benefitSide"
        @main-tap="goToMember" @side-tap="goToCoupons" />
    </view>

    <!-- 分组菜单 -->
    <SurfaceCard :padding="'0'">
      <view v-for="(group, gi) in MENU_GROUPS" :key="gi" class="menu">
        <view v-if="gi > 0" class="menu__divider" />
        <view v-for="item in group" :key="item.label" class="menu__item" @tap="item.action()">
          <AppIcon :name="item.icon" :size="34" tone="primary" />
          <text class="menu__label">{{ item.label }}</text>
          <text class="menu__value" v-if="item.value">{{ item.value }}</text>
          <AppIcon name="arrow-right" :size="26" tone="muted" />
        </view>
      </view>
    </SurfaceCard>

    <view v-if="userStore.isLoggedIn" class="logout" @tap="handleLogout">
      <text class="logout__text">退出登录</text>
    </view>
  </view>
</template>
```

- [ ] **Step 2: `<script setup>` 增加的部分**

```ts
import { computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import AppIcon from '../../components/AppIcon.vue'
import BrandHero from '../../components/BrandHero.vue'
import SurfaceCard from '../../components/SurfaceCard.vue'
import SectionHeader from '../../components/SectionHeader.vue'
import BenefitCard from '../../components/BenefitCard.vue'

onShow(() => {
  uni.setStorageSync('tabbar_selected', 4)
})

const companyName = computed(() => userStore.userInfo?.retailer_profile?.company_name || '')

const ORDER_ENTRIES = [
  { status: 'pending_payment', label: '待付款', icon: 'rmb-circle' },
  { status: 'paid',            label: '待发货', icon: 'bag' },
  { status: 'shipped',         label: '已发货', icon: 'car' },
  { status: 'completed',       label: '已完成', icon: 'checkmark-circle' },
  { status: 'refunding',       label: '退款售后', icon: 'server-man' },
]

const benefitMain = computed(() => ({
  title: '我的权益',
  desc: `当前折扣 ${(userStore.discountRate * 10).toFixed(1)} 折`,
  action: '查看权益',
}))
const benefitSide = ref([
  { icon: 'coupon',   title: '优惠券', desc: '可用 0 张' },
  { icon: 'integral', title: '积分',   desc: '即将上线' },
])

const MENU_GROUPS = [
  [
    { icon: 'file-text', label: '企业信息',   action: () => uni.navigateTo({ url: '/pages/mine/company/index' }) },
    { icon: 'map',       label: '收货地址',   action: () => uni.navigateTo({ url: '/pages/mine/address/index' }) },
    { icon: 'level',     label: '会员中心',   action: () => uni.navigateTo({ url: '/pages/mine/member/index' }) },
  ],
  [
    { icon: 'heart',     label: '我的收藏',   action: () => uni.navigateTo({ url: '/pages/mine/favorites/index' }) },
    { icon: 'clock',     label: '浏览记录',   action: () => uni.navigateTo({ url: '/pages/mine/history/index' }) },
    { icon: 'coupon',    label: '优惠券',     action: () => goToCoupons() },
  ],
  [
    { icon: 'phone',     label: '联系客服',   action: () => uni.switchTab({ url: '/pages/ai-assistant/index' }) },
    { icon: 'setting',   label: '设置',       action: () => uni.navigateTo({ url: '/pages/mine/settings/index' }) },
  ],
]

function goToOrderList(status: string) {
  uni.navigateTo({ url: `/pages/order/list${status ? `?status=${status}` : ''}` })
}
function goToMember()  { uni.navigateTo({ url: '/pages/mine/member/index' }) }
function goToCoupons() { uni.navigateTo({ url: '/pages/mine/coupons/index' }) }
```

**保留不动**：`handleLogin`（该页 171 行的既有函数，走 `userStore.login()` 并弹 toast）、`handleLogout`（它调的 `userStore.logout()` 已经是纯本地清 token，不发请求，见地基修复计划 Task 4）、既有的用户信息拉取逻辑。

**把 `goToLogin` 一律换成既有的 `handleLogin`** —— 模板里 `@login="goToLogin"` 改成 `@login="handleLogin"`，不要新写一个函数。上面的 `<script setup>` 新增代码里**没有** `goToLogin`，那是刻意的：该页已经有登录入口了，再写一个就是两条登录路径。

- [ ] **Step 3: 把 12 处 emoji 换成 `AppIcon`**

该页是全站 emoji 最密集的（12 处）。逐个替换，图标名查 `EMOJI_TO_ICON`。**不要留下任何一个 emoji**——Task 2 的测试会扫出来。

- [ ] **Step 4: 样式**

```scss
.page { min-height: 100vh; background: var(--bg-primary); }

.orders { display: flex; }
.orders__item { flex: 1; display: flex; flex-direction: column; align-items: center; }
.orders__icon {
  width: 72rpx; height: 72rpx; border-radius: var(--radius-circle);
  background: var(--color-primary-bg);
  display: flex; align-items: center; justify-content: center;
}
.orders__label { font-size: var(--font-xs); color: var(--text-secondary); margin-top: var(--space-xs); }

.benefit-wrap { padding: var(--space-lg) var(--space-lg) 0; }

.menu__divider { height: 1rpx; background: var(--border-light); margin-left: var(--space-2xl); }
.menu__item { display: flex; align-items: center; gap: var(--space-md); padding: 28rpx var(--space-lg); }
.menu__label { flex: 1; font-size: var(--font-base); color: var(--text-primary); }
.menu__value { font-size: var(--font-sm); color: var(--text-muted); }

.logout {
  margin: var(--space-xl) var(--space-lg) 0;
  background: var(--bg-white); border-radius: var(--radius-lg);
  padding: 28rpx; text-align: center;
}
.logout__text { font-size: var(--font-base); color: var(--color-primary); }
```

- [ ] **Step 5: 类型检查 + 真机确认**

```bash
cd miniapp && npx vue-tsc --noEmit && npm run dev:mp-weixin
```

确认：未登录时头图显示「点击登录」+ 白胶囊；登录后显示昵称 + 公司名；订单五宫格图标居中；权益双栏正常；三组菜单有分隔线；退出登录能跳回首页且 token 被清（退出后再进「我的」，应当回到未登录态）。

- [ ] **Step 6: 提交**

```bash
git add miniapp/src/pages/mine/index.vue
git commit -m "$(cat <<'EOF'
feat(miniapp): 我的页按新布局语言重建

品牌头图（未登录显示「点击登录」+ 白胶囊）-> 上叠白卡订单五宫格 ->
权益双栏 -> 三组菜单 -> 退出登录。

全站 emoji 最密集的页面（12 处），全部换成 AppIcon。

退出登录走 store 的 logout()，纯本地清 token，不发请求
（后端没有 logout 接口）。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 15: 全站视觉回归

Spec §11 的风险项：`--radius-lg` 等全局 token 变更会**间接影响范围外的 15 个子页面**。这是有意为之（视觉刷新本来就该全站一致），但必须确认没有压字、错位、内容被裁。

**Files:**
- 只读检查；发现问题才改

**Interfaces:**
- Consumes: Task 3 的 token 变更、Task 7 的组件改造
- Produces: `docs/superpowers/plans/2026-10-04-visual-regression-checklist.md`（检查结果记录）

- [ ] **Step 1: 列全需要过一遍的页面**

```bash
cd miniapp && python -c "
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
d = json.load(open('src/pages.json', encoding='utf-8'))
for i, p in enumerate(d['pages'], 1):
    print(f\"{i:2d}. {p['path']}  — {p['style'].get('navigationBarTitleText','')}\")
"
```

预期 20 个页面。

- [ ] **Step 2: 逐页在开发者工具里走一遍**

`npm run dev:mp-weixin`，把 20 个页面**全部点开**。每个页面检查四件事：

1. **圆角有没有吃掉内容** —— 卡片/输入框的圆角变大后，靠近边角的小图标或文字可能被裁
2. **有没有压字** —— token 变更不该影响字号，但如果某个元素的高度是配合旧圆角算的，换行可能变
3. **空状态是否正常** —— `EmptyState` 的 props 接口虽然没改，但内部从 emoji 换成了 `AppIcon`；确认图标能显示、文案没有跑版
4. **加载骨架是否正常** —— 同上，`PageLoading` 的骨架色和圆角变了

其中**重点看这 15 个**（本次范围外的）：

```
pages/products/detail        商品详情
pages/cases/detail           案例详情
pages/cart/index             购物车
pages/order/checkout         确认订单
pages/order/list             订单列表
pages/order/detail           订单详情
pages/mine/company/index     企业信息
pages/mine/address/index     收货地址
pages/mine/member/index      会员中心
pages/mine/favorites/index   我的收藏
pages/mine/history/index     浏览记录
pages/mine/coupons/index     优惠券
pages/mine/settings/index    设置
pages/mine/help/index        帮助中心
pages/mine/contact/index     联系客服
```

- [ ] **Step 3: 全局搜一遍漏改的 emoji**

```bash
cd /d/2026/hxmall/miniapp && python /d/2026/hxmall/.superpowers/count_emoji.py src
```

预期：**文件数 0**（或只剩本次范围外、且有正当理由保留的）。

本次改了 5 个 tab 页 + 5 个组件。范围外的 15 个子页面**仍会有 emoji**——这是预期的，它们的视觉改版是下一轮。但**本次改过的文件里不应残留 emoji**：

```bash
cd /d/2026/hxmall/miniapp && python - <<'PY'
import pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')
RANGES = [(0x1F300,0x1FAFF),(0x1F000,0x1F2FF)]
SCOPE = [
 'src/pages/home/index.vue','src/pages/products/index.vue','src/pages/cases/index.vue',
 'src/pages/ai-assistant/index.vue','src/pages/mine/index.vue',
 'src/components/EmptyState.vue','src/components/PageLoading.vue','src/components/ProductCard.vue',
 'src/components/CaseCard.vue','src/components/SearchBar.vue',
]
bad = False
for f in SCOPE:
    txt = pathlib.Path(f).read_text(encoding='utf-8')
    hits = [c for c in txt if c not in '️‍' and any(a<=ord(c)<=b for a,b in RANGES)]
    if hits:
        bad = True
        print(f"{f}: 残留 {''.join(hits)}")
print('干净' if not bad else '有残留，需要清理')
PY
```

- [ ] **Step 4: 记录结果**

创建 `docs/superpowers/plans/2026-10-04-visual-regression-checklist.md`，把 20 个页面逐个打勾或记问题：

```markdown
# 全站视觉回归记录（2026-10-04）

token 重校准（--radius-lg 20px → 28rpx 等）会影响全部 20 个页面，
其中 15 个在本次改版范围外。逐页确认无压字/错位/内容被裁。

| # | 页面 | 圆角 | 压字 | 空状态 | 加载骨架 | 备注 |
|---|---|---|---|---|---|---|
| 1 | pages/home/index | | | | | 本次范围 |
| … | | | | | | |

## 发现的问题

（逐条记录：页面、现象、是否本次修复）
```

发现问题就**当场修**——多数会是某个元素写死了配合旧圆角的高度，改成 `auto` 或 token 即可。修完单独提交：

```bash
git add -A
git commit -m "$(cat <<'EOF'
fix(miniapp): 修正 token 重校准在范围外页面造成的视觉问题

--radius-lg 从 20px 改为 28rpx 后，以下页面出现压字/错位，
逐个修正。详见 docs/superpowers/plans/2026-10-04-visual-regression-checklist.md。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5: 提交回归记录**

```bash
git add docs/superpowers/plans/2026-10-04-visual-regression-checklist.md
git commit -m "docs(miniapp): 全站视觉回归记录

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

## 验收

全部任务完成后逐条核对：

- [ ] `cd miniapp && npm test` 全绿，`npx vue-tsc --noEmit` 无错误
- [ ] Task 1 的真机验证结论已记进 spec §7.3
- [ ] 5 个 tab 页在**真机**上：图标正常显示（不是空白方块）
- [ ] 5 个 tab 页在**两种数据状态**下各看过一遍：演示数据（满）+ 真实空数据（空）
- [ ] 自定义 tabBar：凸起圆下沿与其它 tab 文字下沿齐平；4 个显示底栏的页面滚到底，最后一行不被遮挡
- [ ] 客服页底部**没有** tabBar，输入栏贴底
- [ ] 案例页点分类 chip 后**列表真的变少**（不是静默失效）
- [ ] 20 个页面视觉回归完成，结果记入 checklist
- [ ] 本次改过的 10 个文件里搜不到 emoji
- [ ] `.env.production` 里 `VITE_DEMO_FALLBACK=false`——**上线前必须确认这一条**
