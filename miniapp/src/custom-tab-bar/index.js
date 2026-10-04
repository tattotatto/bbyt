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
 * 选中项。
 *
 * 首选从页面栈当前位置推出来 —— 每个 tab 页各自渲染一份 tabBar 实例，
 * 实例所属的页面**就是**选中项，这是确定的事实，不存在过期。
 *
 * 存储是回落分支：页面 onShow 里会写 tabbar_selected，但页面生命周期与
 * 组件 attached 的先后在真机上没有保证，只靠存储可能先渲染出一帧高亮错格。
 */
function currentIndex() {
  const pages = getCurrentPages()
  const top = pages[pages.length - 1]
  const route = String((top && top.route) || '').replace(/^\//, '')
  const i = TABS.findIndex((t) => t.pagePath.replace(/^\//, '') === route)
  if (i >= 0) return i
  // wx.getStorageSync 与页面的 uni.setStorageSync 是同一个存储区
  return Number(wx.getStorageSync(SELECTED_KEY)) || 0
}

Component({
  data: {
    tabs: TABS,
    raisedIndex: RAISED_INDEX,
    selected: 0,
  },

  attached() {
    this.setData({ selected: currentIndex() })
  },

  pageLifetimes: {
    // attached 之外再兜一层：页面从别处切回来时重新对齐
    show() {
      this.setData({ selected: currentIndex() })
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
