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

const TABS = [
  { pagePath: '/pages/home/index',         text: '首页', icon: 'home',       iconActive: 'home-fill',    raised: false },
  { pagePath: '/pages/cases/index',        text: '案例', icon: 'photo',      iconActive: 'photo-fill',   raised: false },
  { pagePath: '/pages/ai-assistant/index', text: '',     icon: 'kefu-ermai', iconActive: 'kefu-ermai',   raised: true  },
  { pagePath: '/pages/products/index',     text: '商品', icon: 'bag',        iconActive: 'bag-fill',     raised: false },
  { pagePath: '/pages/mine/index',         text: '我的', icon: 'account',    iconActive: 'account-fill', raised: false },
]

const RAISED_INDEX = TABS.findIndex((t) => t.raised)

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
  // wx.getStorageSync 与页面的 uni.setStorageSync 是同一个存储区
  return Number(wx.getStorageSync(SELECTED_KEY)) || 0
}

/** 本页要不要把底栏藏起来。 */
function isHidden() {
  return HIDDEN_ROUTES.indexOf(currentRoute()) >= 0
}

Component({
  data: {
    tabs: TABS,
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
      uni.setStorageSync(SELECTED_KEY, index)
      uni.switchTab({ url: TABS[index].pagePath })
    },
  },
})
