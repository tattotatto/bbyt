/**
 * 自定义 tabBar —— 原生小程序组件，不是 .vue。
 *
 * 为什么必须是原生文件：pages.json 里 `"custom": true` 会让微信到小程序根目录下
 * 找 `custom-tab-bar/index`。uni-app 对 `src/custom-tab-bar/` 的处理是**原样复制**
 * 到输出目录（见 @dcloudio/uni-mp-weixin 的 vite.copyOptions.targets，里面就列着
 * 这个目录名），不经过编译 —— 放 .vue 进去只会被原样拷成一个微信看不懂的文件，
 * 底栏直接不渲染。所以这里用 js/json/wxml/wxss 四件套。
 *
 * 顺序必须与 pages.json 的 tabBar.list 完全一致 —— switchTab 按索引跳转，
 * 两处不一致会导致点 A 跳到 B。这条不靠人记：`utils/__tests__/tabbar.test.ts`
 * 会读这两个文件比对顺序，错位就是 RED。
 */
const SELECTED_KEY = 'tabbar_selected'

/**
 * 图标字形表：uview-plus 的图标名 → 字体里的字形码点。
 *
 * ── 为什么底栏不能直接用 <u-icon> ──────────────────────────────────────
 *
 * uview-plus 的 u-icon 是**编译过的** uni-app 组件，它的 Vue props 只走
 * uni-app 的私有通道。编译产物里用它的写法是
 * `<u-icon u-i="…" bind:__l="__l" u-p="{{…}}"/>`，运行时按
 * `this.$vm = Iu({ props: gu(properties, isPage(this)) })` 取 props ——
 * 其中非页面（也就是自定义组件）那一支取的是 `properties.uP`，
 * **原生 wxml 属性 name / size / color 一个都不读**。
 *
 * 而本文件是原样复制的原生组件，永远不会发 u-p。所以
 * `<u-icon name="home" size="44rpx" color="#e16531">` 传进去的 name 是
 * undefined：`icons['uicon-undefined']` 取不到字形，`{{f}}` 渲染成空串，
 * `<text class="u-icon__icon">`（display:flex、内容是空文本节点）高度塌成 0，
 * 底栏就只剩文字标签 —— 不报错，只是图标不见了。
 * （2026-10-11 开发者工具实测：底栏白条上沿到标签之间只有内边距，
 *   没有 44rpx 的图标盒；同一页面上 AppIcon 里的 u-icon 正常，
 *   因为 AppIcon 是编译过的组件，走的是 u-p。）
 *
 * 所以这里改成原生 `<text>` + 图标字体：颜色和字号回到 CSS 手里，
 * 不再需要任何 props 通道。
 *
 * ── 抄一份字形码点的代价 ──────────────────────────────────────────────
 *
 * 码点抄错、或 uview-plus 升级换了字形，表现同样是**一片空白且无报错**，
 * 只能靠 `utils/__tests__/tabbar.test.ts` 逐字比对这张表。
 *
 * 写成 \uXXXX 转义而不是字面 PUA 字符：字面字符在这个手写文件里既不可见、
 * 又容易被编辑器的编码转换弄坏，转义形式至少是可审阅、可 diff 的。
 */
const GLYPHS = {
  home: '\ue965',
  'home-fill': '\ue964',
  photo: '\ue98d',
  'photo-fill': '\ue98b',
  'kefu-ermai': '\ue656',
  bag: '\ue619',
  'bag-fill': '\ue617',
  account: '\ue628',
  'account-fill': '\ue614',
}

const TABS = [
  { pagePath: '/pages/home/index',         text: '首页', icon: 'home',       iconActive: 'home-fill',    raised: false },
  { pagePath: '/pages/cases/index',        text: '案例', icon: 'photo',      iconActive: 'photo-fill',   raised: false },
  { pagePath: '/pages/ai-assistant/index', text: '',     icon: 'kefu-ermai', iconActive: 'kefu-ermai',   raised: true  },
  { pagePath: '/pages/products/index',     text: '商品', icon: 'bag',        iconActive: 'bag-fill',     raised: false },
  { pagePath: '/pages/mine/index',         text: '我的', icon: 'account',    iconActive: 'account-fill', raised: false },
]

const RAISED_INDEX = TABS.findIndex((t) => t.raised)

/**
 * 交给 wxml 的那份数据：把图标名翻成字形。
 *
 * WXML 的表达式里不能调函数，所以名字→字形的翻译必须在这里做完。
 * TABS 里只留图标名（那是唯一事实来源），字形由 GLYPHS 现查 —— 两份表
 * 各自写一遍的话，改了一处忘了另一处就是一片空白。
 */
const DISPLAY_TABS = TABS.map((t) => Object.assign({}, t, {
  glyph: GLYPHS[t.icon],
  glyphActive: GLYPHS[t.iconActive],
}))

/**
 * 不显示底栏的页面。
 *
 * spec §2 #12 / §5.4 ⑤：聊天页输入栏占住底部，保持沉浸。
 *
 * 这件事**只能在这里做**。`tabBar.custom: true` 之后，底栏不是微信原生渲染的，
 * 而是微信在每一个 tabBar 页底部挂一份本组件的实例 —— 只要页面还在
 * `tabBar.list` 里，底栏就一定出现，页面侧写什么都拦不住（页面不挂
 * `.has-custom-tabbar` 只是不给自己预留它的高度，底栏照样压在下面）。
 */
const HIDDEN_ROUTES = ['pages/ai-assistant/index']

/** 页面栈顶的路由，去掉前导斜杠。 */
function currentRoute() {
  const pages = getCurrentPages()
  const top = pages[pages.length - 1]
  return String((top && top.route) || '').replace(/^\//, '')
}

/**
 * 选中项。
 *
 * 首选从页面栈当前位置推出来 —— 每个 tab 页各自渲染一份 tabBar 实例，
 * 实例所属的页面**就是**选中项，这是确定的事实，不存在过期。
 *
 * 存储是回落分支：页面 onShow 里会写 tabbar_selected，但页面生命周期与
 * 组件 attached 的先后在真机上没有保证，只靠存储可能先渲染出一帧高亮错格。
 */
function currentIndex() {
  const route = currentRoute()
  const i = TABS.findIndex((t) => t.pagePath.replace(/^\//, '') === route)
  if (i >= 0) return i
  // 页面侧（用 uni API 编译出来的那个 `setStorageSync`）与本文件写的是同一个存储区
  return Number(wx.getStorageSync(SELECTED_KEY)) || 0
}

/** 本页要不要把底栏藏起来。 */
function isHidden() {
  return HIDDEN_ROUTES.indexOf(currentRoute()) >= 0
}

Component({
  data: {
    tabs: DISPLAY_TABS,
    raisedIndex: RAISED_INDEX,
    selected: 0,
    // 初值 false，attached 里按当前路由纠正。取不到路由时宁可多显示一帧
    // 底栏，也不要让 4 个正常的 tab 页因为读不到路由而集体没有底栏。
    hidden: false,
  },

  attached() {
    this.setData({ selected: currentIndex(), hidden: isHidden() })
  },

  pageLifetimes: {
    // attached 之外再兜一层：页面从别处切回来时重新对齐
    show() {
      this.setData({ selected: currentIndex(), hidden: isHidden() })
    },
  },

  methods: {
    switchTo(e) {
      const index = Number(e.currentTarget.dataset.index)
      if (!(index >= 0) || index >= TABS.length) return
      this.setData({ selected: index })
      // 用 wx 而不是 uni：本文件原样复制、不编译，`uni` 在这里没有定义
      // （编译过的页面会把对 uni 的调用改写成 import 进来的对象，这个文件不享受这一步）。
      // 微信运行时的全局只有 wx，写 uni 会在这一行抛 ReferenceError；
      // 又因为它在点击回调里，表现成「高亮闪了一下、页面不动」，没有任何报错。
      wx.setStorageSync(SELECTED_KEY, index)
      wx.switchTab({ url: TABS[index].pagePath })
    },
  },
})
