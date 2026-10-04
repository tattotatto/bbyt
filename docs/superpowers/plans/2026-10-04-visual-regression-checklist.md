# 全站视觉回归记录（2026-10-04）

> Task 15 产出。对应计划 `docs/superpowers/plans/2026-10-04-miniapp-redesign.md`。

token 重校准（`--radius-lg` 20px → 28rpx 等）会影响全部 20 个页面，其中 15 个在本次改版范围外。
逐页确认无压字/错位/内容被裁。

---

## ⚠️ 结论先行：逐页视觉确认**未执行**

计划 Step 2 要求 `npm run dev:mp-weixin` 后在**微信开发者工具**里把 20 个页面逐个点开、肉眼检查四件事。
**这一步没有做，也无法由我完成** —— 我无法驱动微信开发者工具，也无法观察渲染结果。

因此下表中**每一个页面的「圆角 / 压字 / 空状态 / 加载骨架」四列全部是「未验证」**，
不是「通过」。把它们读成通过会在上线前漏掉本次改版最可能出问题的一类缺陷。

本文件能提供的，是**自动化能证明的部分**（见下方「已验证事实」）与**已经被发现的、确定存在的问题**（见「发现的问题」）。
剩下的逐页肉眼确认，需要人在开发者工具前完成。

bookkeeping 与 Task 1 / 4 / 5 / 6 / 7 / 8 / 10 / 11 / 12 / 13 / 14 的同类门槛一致：记「未验证」，不记「通过」。

---

## 页面清单（20 个）

范围说明：**本次范围** = 计划改动的 5 个 tab 页 + 5 个组件；**范围外** = 15 个子页面（它们的视觉改版是下一轮）。

| # | 页面 | 圆角 | 压字 | 空状态 | 加载骨架 | 范围 / 备注 |
|---|---|---|---|---|---|---|
| 1 | `pages/home/index.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 本次范围（tab 1） |
| 2 | `pages/ai-assistant/index.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 本次范围（tab 3，客服，无 tabBar） |
| 3 | `pages/cases/index.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 本次范围（tab 2） |
| 4 | `pages/cases/detail.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 范围外 |
| 5 | `pages/products/index.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 本次范围（tab 4） |
| 6 | `pages/products/detail.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 范围外 |
| 7 | `pages/order/list.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 范围外 |
| 8 | `pages/order/detail.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 范围外 |
| 9 | `pages/cart/index.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 范围外 |
| 10 | `pages/order/checkout.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 范围外 |
| 11 | `pages/mine/index.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 本次范围（tab 5） |
| 12 | `pages/mine/company/index.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 范围外 |
| 13 | `pages/mine/address/index.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 范围外 |
| 14 | `pages/mine/member/index.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 范围外 |
| 15 | `pages/mine/favorites/index.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 范围外 |
| 16 | `pages/mine/history/index.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 范围外 |
| 17 | `pages/mine/coupons/index.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 范围外 |
| 18 | `pages/mine/contact/index.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 范围外 |
| 19 | `pages/mine/settings/index.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 范围外 |
| 20 | `pages/mine/help/index.vue` | 未验证 | 未验证 | 未验证 | 未验证 | 范围外 |

tabBar 页（`tabBar.custom: true`）：home / cases / ai-assistant / products / mine。
其中 `ai-assistant` 在 `custom-tab-bar/index.js` 的 `HIDDEN_ROUTES` 里，本页底部**不应有** tabBar。

---

## 已验证事实（自动化能证明的部分）

以下均为本次实际运行、读到输出后记录：

| 项 | 命令 / 依据 | 结果 |
|---|---|---|
| 单元测试 | `npm test` | **14 个测试文件，125/125 通过，exit 0** |
| 类型检查 | `npx vue-tsc --noEmit` | **无输出（无错误）** |
| 小程序构建 | `npm run build:mp-weixin` | **exit 0，`DONE Build complete.`**（仅有既存的 Sass `@import` 弃用告警） |
| 图标字体内联 | `app.wxss` 计数 | `data:font/truetype` **×1**，`at.alicdn.com` **×0** —— 远程 `@font-face` 已被 base64 内联覆盖 |
| AppIcon 产出 | `dist/build/mp-weixin/components/` | `AppIcon.{js,json,wxml}` 均存在 |
| 页面数 | `src/pages.json` | **20**（与本文件表格一致） |
| 上线开关 | `.env.production` | `VITE_DEMO_FALLBACK=false`（**工作区与 HEAD 均已确认**） |
| 品牌色 | `app.wxss` L1 | `:root{--color-primary: #e16531;` |
| token 继承面 | 见下 | **17 个 wxss 完全依赖 `:root` 继承** |

### token 继承面（本次新测）

编译产出的 18 个 wxss 里，**17 个**引用了 `var(--…)` 却在本地**一个都不定义**，全部依赖 `:root` 上的自定义属性继承进来：

```
components/BannerCard · BenefitCard · BrandHero · CaseCard · CircleEntryRow
components/EmptyState · EntryGrid · PageLoading · ProductCard · SectionHeader · SurfaceCard
custom-tab-bar/index
pages/ai-assistant(28) · cases(12) · home(8) · mine(18) · products(18)
```

**含义：** 如果微信小程序的自定义组件不继承 `:root` 上的自定义属性，**全站 17 个样式文件会同时失去颜色/圆角/间距** —— 症状是整屏无样式，不是某一页错位。
这是一种「要么全好、要么全崩」的依赖，不可能在真机上被误判成局部问题。

**但这一点仍然无法在没有真机/开发者工具的情况下证实。**
需要说明的是：`--color-primary` 定义在 `:root` 上**并不是本分支引入的** —— `master` 上就已经如此（`theme.scss` 的 `:root` 块）。所以这是**既存假设**，不是本次改版新增的风险。
反过来说，它也意味着：真机验证一旦失败，**锅不在本分支**，但本分支会一样崩。

---

## 发现的问题

### 1. 【已修复】HEAD 曾经不可构建 —— 缺 Task 1 的三个文件

**现象：** Task 1 创建了 `AppIcon.vue`、`uni.scss`、`styles/uview-iconfont.scss`，但因为计划里的提交信息含有「真机预览已验证三个图标可见」这类**尚未验证的陈述**，当时刻意没有提交。
Task 2–14 随后提交的代码全都依赖它们，于是 **HEAD 上有 18 个文件 import 一个不存在的组件**。

**证据：** `git archive HEAD | tar -x -C /tmp/headcheck` 后，快照里 18 个文件 import `../../components/AppIcon.vue`，而 `/tmp/headcheck/src/components/AppIcon.vue` 不存在；`uni.scss` 与 `uview-iconfont.scss` 同样缺失；HEAD 的 `App.vue` 也没有那三行字体 `@import`。

**修复：** 提交 `b0bfd26`（`fix(miniapp): 补提交 Task 1 的图标字体产出（此前一直未入库）`），只暂存这 4 个路径，提交信息里**如实写明真机验证仍未完成**。
复验：`git archive HEAD` 现在包含 `AppIcon.vue`(1754B)、`uni.scss`(776B)、`uview-iconfont.scss`(75247B)，且 `App.vue` 的 `@import` 在位。

**是否本次修复：** 是。

### 2. 【未动】工作区里有一处 `#FF7B7B → #e16531` 的品牌色迁移没有提交

**现象：** 工作区有 23 个文件的改动（+69/−61），是一处连贯的品牌色替换：`#FF7B7B → #e16531`、`#FF9B9B → #f39a6d`、`rgba(255,123,123,0.3) → rgba(225,101,49,0.3)`、`HXMall_KF → 蓓贝婴童KF`，覆盖范围外的子页面、`PriceTable.vue` 和 `App.vue`。

**判断：** 这是有意的，但**在本计划范围之外**（计划写明「本计划不做：15 个子页面」），因此**没有提交**。

**后果（必须知道）：** **在 HEAD 上，范围外的 15 个子页面仍然渲染旧品牌色 `#FF7B7B`。**
所以如果现在拿 HEAD 去做真机视觉回归，会看到**两种品牌色并存**（5 个 tab 页是新色 `#e16531`，15 个子页面是旧色 `#FF7B7B`）——这是**预期现象，不是缺陷**，工作区里已经修好了。

**是否本次修复：** 否（刻意不修，超出范围）。

### 3. 【保留，已裁定】`EmptyState.vue` 的 5 处 emoji 是**查找键**，不是渲染字形

**现象：** Step 3 的 SCOPE 扫描判定 10 个文件里 9 个干净，`EmptyState.vue` 残留 💖📍📦🔐🛒 共 5 处。

**分析：** 这 5 处都不是会渲染到屏幕上的字符 ——

- `icon: '📦'`（L55）是 `withDefaults` 里那个 **`@deprecated` prop 的默认值**，只作为 `iconForEmoji()` 的**输入键**使用
- L74–75 是**文档注释**，列举调用方会传哪些 emoji

模板本身渲染的是 `<AppIcon :name="illustrationName" :size="140" tone="muted" />`，**从不渲染 emoji**。
28 个调用点里 **22 个**（含 11 个范围外页面）依赖 `iconForEmoji` 这层 emoji→图标桥接；把这个 prop 删掉会连带打挂范围外的页面。

`src/utils/__tests__/icon-map.test.ts` 已经**证明**了该性质：它遍历所有 `.vue` 文件断言出现的每个 emoji 都在 `EMOJI_TO_ICON` 里；`describe('iconForEmoji')` 断言它**永远不返回 emoji**（`iconForEmoji('🦄')` → `'more-circle'`、`iconForEmoji('⚠️')` → `'empty-wifi'`）。125 条测试为后盾。

**裁定：** 计划要求「本次改过的 10 个文件里搜不到 emoji」，而计划自己的措辞允许「只剩本次范围外、且有正当理由保留的」。
此处实质满足：**无 emoji 进入渲染**，且残留物是接口的一部分。
**不改代码，不加测试** —— 该性质已由既有测试证明。

因此验收项「本次改过的 10 个文件里搜不到 emoji」只能以 **9/10 + 一处有据可查的例外** 关闭。

**是否本次修复：** 否（无需修复）。

### 4. 【记录】`BrandHero.vue` 的 🧸 在注释里

同一个扫描把它算进了「全局 17 个文件 / 84 处」，但它在**文档注释**里，解释为什么该处改用 `AppIcon`。不渲染。

### 5. 【记录】`products/detail.vue` 传的是 HTML 实体 `&#x1F4E6;`

范围外页面，传 `&#x1F4E6;`（📦 的实体写法）给 `EmptyState`。
实体写法**不匹配 `EMOJI_TO_ICON` 的键**（键是真实字符），所以它会走 `iconForEmoji` 的兜底分支。
不至于崩，但会拿到兜底图标而不是 📦 对应的图标。属于范围外页面的下一轮工作。

### 6. 【待复核】Task 14 交接过来、必须在真机上确认的三项

Task 14 的 ledger 明确交接了下面几件**静态检查做不到、必须真机看**的事，本次**无法执行**，在此登记以免遗漏：

- **Ruling F —— 头像消失。** 改造后 `BrandHero` 没有头像位，原来头图上的头像不再渲染。需要确认这是可接受的取舍，而不是漏做。
- **Ruling H —— 帮助中心变成孤儿页。** `pages/mine/help/index.vue` 现在**没有任何入口**指向它（菜单里没有这一项）。需要确认是否补入口，或确认它已废弃。
- **Ruling G —— 退款售后落到「全部」。** 我的页「退款售后」入口传 `status=refunding`，而订单页 tabs 里没有 `refunding`（它是契约测试里 `allowed` 额外放行的值）。需要确认订单页对该值的处理符合预期，而不是静默落到「全部」列表。
- 另有 3 项视觉细节（图标居中、分隔线、退出登录后回到未登录态）同样待真机确认。

---

## 待人工完成（移交）

要让本文件从「未验证」变成「已确认」，需要在微信开发者工具里做：

1. `cd miniapp && npm run dev:mp-weixin`，用开发者工具打开 `dist/dev/mp-weixin`
2. 逐个点开上表 20 个页面，每页检查四件事：圆角是否裁掉内容 / 是否压字 / 空状态是否正常 / 加载骨架是否正常
3. 重点看 15 个范围外页面（token 变更是全局的，它们不在本次改动范围但会受影响）
4. **第一优先确认第 1 项**：如果整屏无样式，说明 `:root` 自定义属性没有继承进自定义组件 —— 这一个现象就能解释全部 17 个 wxss 的问题
5. 对照「发现的问题」第 6 条，确认 Task 14 交接的三项
6. 把结果填回本表，「未验证」改为「✓」或具体问题描述

同时仍未完成、且**上线前必须确认**的验收项（与本文档相关部分）：

- [ ] 5 个 tab 页在**真机**上图标正常显示（不是空白方块）—— Task 1 留下的门槛，**仍然开着**
- [ ] 5 个 tab 页在**两种数据状态**下各看过一遍（演示数据满 / 真实空数据空）
- [ ] 自定义 tabBar：凸起圆下沿与其它 tab 文字下沿齐平；4 个显示底栏的页面滚到底最后一行不被遮挡
- [ ] 客服页底部**没有** tabBar，输入栏贴底
- [ ] 案例页点分类 chip 后**列表真的变少**（不是静默失效）
- [x] `.env.production` 里 `VITE_DEMO_FALLBACK=false` —— 已确认
