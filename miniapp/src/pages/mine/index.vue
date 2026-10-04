<template>
  <view class="page has-custom-tabbar">
    <!-- ① 品牌头图。未登录时标题是「点击登录」，白色胶囊是真正的点击目标 -->
    <BrandHero
      :title="userStore.isLoggedIn ? memberName : '点击登录'"
      :slogan="userStore.isLoggedIn ? (companyName || '完善企业信息可开通账期') : '登录后查看专属价格'"
      :show-login="!userStore.isLoggedIn"
      @login="handleLogin"
    />

    <!-- ② 上叠白卡：我的订单五宫格。
         padding 交给子元素（SectionHeader 自带左右内边距、宫格自带），
         卡片自己不留 —— 否则两层内边距叠起来。 -->
    <SurfaceCard overlap :padding="'0'">
      <SectionHeader title="我的订单" more="全部订单" @more="goToOrderList('')" />
      <view class="orders">
        <view
          v-for="o in ORDER_ENTRIES"
          :key="o.status"
          class="orders__item"
          @tap="goToOrderList(o.status)"
        >
          <view class="orders__icon">
            <AppIcon :name="o.icon" :size="40" tone="primary" />
          </view>
          <text class="orders__label">{{ o.label }}</text>
        </view>
      </view>
    </SurfaceCard>

    <!-- ③ 我的权益双栏 -->
    <view class="benefit-wrap">
      <BenefitCard
        :main="benefitMain"
        :side="benefitSide"
        @main-tap="goToMember"
        @side-tap="goToCoupons"
      />
    </view>

    <!-- ④ 分组菜单卡。padding: 0 才能让分隔线通到卡片边缘（SurfaceCard 的注释里点名的就是这一处） -->
    <SurfaceCard :padding="'0'">
      <view v-for="(group, gi) in MENU_GROUPS" :key="gi" class="menu">
        <view v-if="gi > 0" class="menu__divider" />
        <view v-for="item in group" :key="item.label" class="menu__item" @tap="item.action()">
          <AppIcon :name="item.icon" :size="34" tone="primary" />
          <text class="menu__label">{{ item.label }}</text>
          <text v-if="item.value" class="menu__value">{{ item.value }}</text>
          <AppIcon name="arrow-right" :size="26" tone="muted" />
        </view>
      </view>
    </SurfaceCard>

    <!-- ⑤ 退出登录（仅登录后） -->
    <view v-if="userStore.isLoggedIn" class="logout" @tap="handleLogout">
      <text class="logout__text">退出登录</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import AppIcon from '../../components/AppIcon.vue'
import BrandHero from '../../components/BrandHero.vue'
import SurfaceCard from '../../components/SurfaceCard.vue'
import SectionHeader from '../../components/SectionHeader.vue'
import BenefitCard from '../../components/BenefitCard.vue'
import { useUserStore } from '../../stores/user'
import { useAppStore } from '../../stores/app'

const userStore = useUserStore()
const appStore = useAppStore()

// 取系统信息。BrandHero 自己扛状态栏高度，读的是 appStore.statusBarHeight，
// 不 init 就永远是 0，头图会被状态栏压住。
appStore.init()

// 自定义 tabBar 是每个页面各自渲染的一份实例，状态不共享。这里写下本页在
// tabs 数组里的下标（我的 = 4）。组件优先按页面栈推断选中项，存储是回落值。
onShow(() => {
  uni.setStorageSync('tabbar_selected', 4)
})

/**
 * 昵称。
 *
 * 不用 store 的 `nickname` —— 那个 getter 的兜底是「未登录」，登录了但后端没返
 * 昵称时会在头图上渲染出「未登录」三个字，比空白更糟。
 */
const memberName = computed(() => userStore.userInfo?.nickname || '蓓贝会员')
const companyName = computed(() => userStore.userInfo?.retailer_profile?.company_name || '')

// ── Login / Logout ──────────────────────────────────────────────────────────
async function handleLogin() {
  try {
    await userStore.login()
    uni.showToast({ title: '登录成功', icon: 'success' })
  } catch {
    uni.showToast({ title: '登录失败，请重试', icon: 'none' })
  }
}

function handleLogout() {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        // store 里的 logout 是纯本地清 token，不发请求（后端没有 logout 接口）
        userStore.logout()
      }
    }
  })
}

// ── 订单入口 ────────────────────────────────────────────────────────────────
// status 必须与 pages/order/list 的 tabs 对上：这一页原来写的是 `pending`，
// 而订单页认的是 `pending_payment` —— 点「待付款」会落到「全部」，
// 看起来像"就是没有待付款订单"。contract 测试会比对两边。
const ORDER_ENTRIES = [
  { status: 'pending_payment', label: '待付款',   icon: 'rmb-circle' },
  { status: 'paid',            label: '待发货',   icon: 'bag' },
  { status: 'shipped',         label: '已发货',   icon: 'car' },
  { status: 'completed',       label: '已完成',   icon: 'checkmark-circle' },
  { status: 'refunding',       label: '退款售后', icon: 'server-man' },
]

function goToOrderList(status: string) {
  uni.navigateTo({ url: `/pages/order/list${status ? `?status=${status}` : ''}` })
}

// ── 我的权益 ────────────────────────────────────────────────────────────────
const benefitMain = computed(() => ({
  title: '我的权益',
  desc: `当前折扣 ${(userStore.discountRate * 10).toFixed(1)} 折`,
  action: '查看权益',
}))
// 优惠券张数没有数据源（全站还没有 coupons 接口），与「积分」一样是占位
const benefitSide = ref([
  { icon: 'coupon',   title: '优惠券', desc: '可用 0 张' },
  { icon: 'integral', title: '积分',   desc: '即将上线' },
])

// ── 分组菜单 ────────────────────────────────────────────────────────────────
interface MenuItem {
  icon: string
  label: string
  /** 右侧的次要文字，可选 */
  value?: string
  action: () => void
}

// 用 computed 而不是常量数组：会员中心那一行要跟着等级走。
// （等级徽章原来在头图上，BrandHero 没有徽章位，挪到这一行）
const MENU_GROUPS = computed<MenuItem[][]>(() => [
  [
    { icon: 'file-text', label: '企业信息', action: () => uni.navigateTo({ url: '/pages/mine/company/index' }) },
    { icon: 'map',       label: '收货地址', action: () => uni.navigateTo({ url: '/pages/mine/address/index' }) },
    {
      icon: 'level',
      label: '会员中心',
      value: userStore.isLoggedIn ? userStore.levelLabel : '普通会员',
      action: goToMember,
    },
  ],
  [
    { icon: 'heart',  label: '我的收藏', action: () => uni.navigateTo({ url: '/pages/mine/favorites/index' }) },
    { icon: 'clock',  label: '浏览记录', action: () => uni.navigateTo({ url: '/pages/mine/history/index' }) },
    { icon: 'coupon', label: '优惠券',   action: goToCoupons },
  ],
  [
    // 客服是 tabBar 页（index 2）：只能 switchTab，navigateTo 是静默失败
    { icon: 'phone',   label: '联系客服', action: () => uni.switchTab({ url: '/pages/ai-assistant/index' }) },
    { icon: 'setting', label: '设置',     action: () => uni.navigateTo({ url: '/pages/mine/settings/index' }) },
  ],
])

function goToMember()  { uni.navigateTo({ url: '/pages/mine/member/index' }) }
function goToCoupons() { uni.navigateTo({ url: '/pages/mine/coupons/index' }) }
</script>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  background: var(--bg-primary);
}

// ── 订单五宫格 ────────────────────────────────
.orders {
  display: flex;
  padding: 0 var(--space-lg) var(--space-xl);
}
.orders__item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.orders__icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: var(--radius-circle);
  background: var(--color-primary-bg);
  display: flex;
  align-items: center;
  justify-content: center;
}
.orders__label {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  margin-top: var(--space-xs);
}

// ── 权益双栏 ──────────────────────────────────
.benefit-wrap {
  padding: var(--space-lg) var(--space-lg) 0;
}

// ── 分组菜单 ──────────────────────────────────
.menu__divider {
  height: 1rpx;
  background: var(--border-light);
  margin-left: var(--space-2xl);
}
.menu__item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: 28rpx var(--space-lg);
}
.menu__label {
  flex: 1;
  font-size: var(--font-base);
  color: var(--text-primary);
}
.menu__value {
  font-size: var(--font-sm);
  color: var(--text-muted);
}

// ── 退出登录 ──────────────────────────────────
.logout {
  margin: var(--space-xl) var(--space-lg) 0;
  background: var(--bg-white);
  border-radius: var(--radius-lg);
  padding: 28rpx;
  text-align: center;
}
.logout__text {
  font-size: var(--font-base);
  color: var(--color-primary);
}
</style>
