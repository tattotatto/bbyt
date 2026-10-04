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
