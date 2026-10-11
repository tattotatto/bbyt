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

> **2026-10-11/12 补记：** 开发者工具里跑起来了（`dist/build/mp-weixin`），
> 上面这份「未执行」的逐页确认仍然只做了**局部**（tab 页 + 我的页），
> 但已经足够暴露出三条静态检查全都抓不到的问题 ——
> 见文末「第二轮」。其中一条正是本文第 7 条悬案的答案。

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
| 图标字体内联 | `app.wxss` 计数 | `data:font/truetype` **×1**，`at.alicdn.com` **×0** —— 只证明**样式表里**没有远程字体 URL。**不等于**运行时不会去拉远程字体，见下方问题 7 |
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

### 7. 【更正上面的表格】图标字体「已内联覆盖远程」这个说法，证据不足

表格里那行「远程 `@font-face` 已被 base64 内联覆盖」是**我写的，写过头了**。
`app.wxss` 里 `at.alicdn.com` 计数为 0，只能证明**样式表**里没有远程字体 URL；
它证明不了运行时不拉远程字体 —— 那个 URL 仍然在 `common/vendor.js` 里，
且 `uview-plus/components/u-icon/util.js` 在 `MP-WEIXIN` 下创建 u-icon 时会调
`uni.loadFontFace({ family: 'uicon-iconfont', source: 'url(https://at.alicdn.com/…)' })`。

大概率没问题（没有 `downloadFile` 白名单时那次加载会静默失败，而内联的 base64
字体应该仍然生效），但**这正是 Task 1 的真机闸门要盯的那条路径** ——
用「计数为 0」当成「已解决」是把未验证读成了已验证，与本文件开头的自我要求相悖。

### 8. 【已修】最终评审发现：自定义 tabBar 调用了不存在的全局 `uni`

**现象：** `src/custom-tab-bar/index.js` 的点击处理里调 `uni.setStorageSync` /
`uni.switchTab`。这个文件是**原样复制**到产物里的（uni-app 不编译它），
所以 `uni` 按微信运行时的原样解析 —— 而微信只提供 `wx`。

**证据：** 全产物里 `globalThis.X` 的赋值只有 `wx` / `document` / `harmonyChannel`，
**没有** `globalThis.uni`；编译过的页面会把 `uni.switchTab` 重写成
`e.index.switchTab`（走 import），这个文件没有这一步。

**后果：** 点底栏会抛 `ReferenceError`，且因为它在点击回调里 ——
表现为「高亮闪一下、页面不动」，没有任何报错。**整个底部导航是死的。**

**修复：** 改用 `wx.setStorageSync` / `wx.switchTab`（同一个存储区，语义相同）。
新增结构性测试钉住它（`utils/__tests__/tabbar.test.ts`）。

---

## 第二轮：2026-10-11/12 开发者工具实测

第一次真的在微信开发者工具里跑起来之后，冒出三条**静态检查全都抓不到**的问题。
三条是同一个形状，值得单独记：**全是静默失败** —— 不报错、不崩、控制台干净，只是"没显示"。
这也解释了为什么第一轮"数 `data:font`、数 `at.alicdn.com`、看 `:root{…}`"全都读成了通过。

### 9. 【已修】token 声明位置的推演应验了：整站无样式

「token 继承面」一节推演的「要么全好、要么全崩」**原样发生**，但机制比推演更彻底：

- **现象：** 整站像没加载样式 —— 头图没橙色渐变、卡片没圆角阴影、间距全塌、内容一直铺到底栏底下。
- **原因：** 不是"自定义组件不继承"，而是 **WXSS 里 `:root` 根本不是一个可用的声明位置**。
  编译产物 `app.wxss` 第一条确实写着 `:root{--color-primary: …}` —— 所以它**在文件里看得见**
  （上一轮的静态检查看它是正常的），但运行时一个自定义属性都读不出来。
  全站 18 个 wxss、约 500 处 `var(--…)` 因此同时失效。
- **佐证：** 当时全站唯一渲染正常的是自定义底栏，而它是唯一给每个 `var()` 都写了字面兜底值的文件。
  同一套 token、同一个运行时，写了兜底的活、没写兜底的全塌 —— 问题不在 `var()`，在 token 没被声明出来。
- **修复：** `theme.scss` 的 token 块 `:root` → `page`（uni-app 自己注入的 `page{--status-bar-height:…}` 用的就是它）。
  上面表格里 `app.wxss L1 = :root{--color-primary: #e16531;` 那一行因此**已失效**，
  现在是 `page{--color-primary: #e16531; …}`。
- **钉住：** 新增 `utils/__tests__/theme-tokens.test.ts`（只检查"声明在 `page` 上、不能只有 `:root`"，不检查值）。

### 10. 【已修】底栏图标空白：两个先后暴露的静默失败

底栏一开始走 `<u-icon>`，然后是原生 `<text>`，两条路各有一个坑：

**① `<u-icon>` 在自定义 tabBar 里永远收不到 props。**
它是**编译过的** uni-app 组件，props 只走私有通道（编译产物里写作 `u-p="{{…}}"`）；
运行时非页面组件读的是 `properties.uP`，**原生 wxml 的 `name` / `size` / `color` 一个都不读**。
而 `src/custom-tab-bar/` 是 uni-app **原样复制、不编译**的目录（见 `vite.copyOptions.targets`）——
传进去的 `name` 是 `undefined`，`icons['uicon-undefined']` 取不到字形，
`{{f}}` 渲染成空串，高度还塌成 0。不报错，图标就是不见了。
**修复：** 改成原生 `<text>` + 本地字形表（`index.js` 的 `GLYPHS`，码点抄自 uview-plus 的 `icons.js`）。

**② 换掉 u-icon 之后**仍然**空白 —— 字体没有在组件里注册。**
图标字体本来只有两个来源，而**两个都到不了这个组件**：

- `app.wxss` 里的 `@font-face`（来自 `styles/uview-iconfont.scss` 的内联 base64）：**自定义组件有样式隔离**，进不去；
- uview-plus 运行时的 `wx.loadFontFace({ global: true })`：**只在 u-icon 被实例化时触发**
  （`beforeCreate(){ fontUtil.params.loaded || fontUtil.loadFont() }`；`vendor.js` 里没有第二个调用点）。
  底栏已经没有 u-icon 了，没有谁替它注册。

于是 `.tabbar__icon` 的 44rpx 格子**占得住**（标签被推下去 44rpx，与 spec §6.2 的 18+44+6 吻合），
但格子里**一点墨迹都没有** —— PUA 码点在系统字体里没有字形。
同一张图上页面里的 u-icon 图标正常，因为那些地方有 u-icon。

**修复：** 新增 `custom-tab-bar/iconfont.wxss`（与 `styles/uview-iconfont.scss` **逐字相同**的 base64），
在 `index.wxss` 的**第一行** `@import` 进来 —— 放第一行是有意的：按 CSS 规范注释会先被剥掉、
不影响 `@import`，但微信那套 WXSS 编译器不保证这么做，而这一整类失效都是静默的。
新增 4 条用例钉住（两份 base64 逐字一致、不得用远程 URL、`@import` 必须是全文件第一行、family 名一致）。

**这一条同时是本文第 7 条悬案的答案：** 远程 `at.alicdn.com` 那条路是**死的** ——
没有 `downloadFile` 白名单时静默失败（问题 7 猜的就是这个），所以底栏在修复前不可能显示出来。
页面和编译组件的图标能显示，靠的是 `app.wxss` 里那份 base64；底栏必须自己带一份同样的。

**2026-10-12 用户确认：底栏 5 个图标正常显示。** 但这是**开发者工具**，不是真机。

### 11. 【已修】登录胶囊压住微信胶囊按钮；下拉越界露出白色

用 `素材/index2.png` **逐像素**量的，不是推算：

- 微信自己的胶囊按钮 y **38–69**（87×32，正是官方尺寸），头图右上角的「登录 / 注册」白胶囊
  y **65–93** —— 上沿被盖住 4px，两个白块视觉上粘成一块。
- **原因：** 头图顶部留白只有 `statusBar + 20`，正落在胶囊按钮所在的那条 **44px 导航栏带**里
  （胶囊在带内上下居中，占 `statusBar+6 ~ statusBar+38`）。
- **修复：** 几何抽成 `utils/index.ts` 的 `heroPaddingTop()`，右上角有内容时让开**整条**导航栏：
  `statusBar + 44`，离胶囊下沿固定余 6px —— 6px 是胶囊居中留下的半格，**任意状态栏高度下都成立**，
  不用按机型配数值。案例/商品页（compact、右上角空着）的紧凑间距不变。
  `stores/app.ts` 里一直没人用的 `navBarHeight` 现在与该常量同源。

下拉露白是另一回事：**回弹区露出来的是窗口背景色，不是页面自己的 CSS 背景** ——
给 `page` 或 `.page` 上色都盖不到它。决定它的是 `pages.json` 的 `backgroundColorTop`，
不设就用全局 `backgroundColor`（`#FFF8F0`，近白），于是橙色头图上方顶出一条白边。
已给 5 个自定义导航页（顶部都是橙色头图）设成品牌橙；系统导航栏的页面**不设** ——
它们的回弹区在系统导航栏底下看不见，乱设只会在某些机型上露出半条橙边。
新增 `utils/__tests__/brand-hero.test.ts` 同时钉住这两条（含"不许有页面乱设 `backgroundColorTop`"）。

**⚠️ 未验证：** 微信文档标注 `backgroundColorTop` **仅 iOS 支持**。开发者工具的 iOS 模拟
通常跟着变，但**没有真机确认过**；Android 没有回弹，不存在这块区域。

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

- [x] 5 个 tab 页图标正常显示（不是空白方块）—— **2026-10-12 开发者工具已确认**（用户回报「图标出来了」），
      机制见上面第 10 条
- [ ] **同一件事在真机上复看一遍** —— 开发者工具与真机的字体加载路径不同，
      第 10 条那两条路（组件内 base64、u-icon 的远程 `loadFontFace`）都还没在真机走过
- [ ] 下拉越界区是品牌橙、不是白色（`pages.json` 的 `backgroundColorTop`）—— **仅 iOS**，需真机确认，见第 11 条
- [ ] 登录 / 注册胶囊让开微信胶囊按钮后，头图整体下移 24px 的观感可接受（第 11 条）
- [ ] 5 个 tab 页在**两种数据状态**下各看过一遍（演示数据满 / 真实空数据空）
- [ ] 自定义 tabBar：凸起圆下沿与其它 tab 文字下沿齐平；4 个显示底栏的页面滚到底最后一行不被遮挡
- [ ] 客服页底部**没有** tabBar，输入栏贴底
- [ ] 案例页点分类 chip 后**列表真的变少**（不是静默失效）
- [x] `.env.production` 里 `VITE_DEMO_FALLBACK=false` —— 已确认
