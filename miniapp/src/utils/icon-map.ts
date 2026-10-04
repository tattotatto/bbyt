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
  // ⚠ 只写不带 U+FE0F 的形式：调用方写的是 '⚠️'（带变体选择符），
  // 查表时会被 iconForEmoji 归一化掉，两种写法都命中这一条。
  '⚠': 'empty-wifi',           // 加载失败 / 网络异常

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
  const direct = EMOJI_TO_ICON[emoji]
  if (direct) return direct

  // 变体选择符（U+FE0E 文本形态 / U+FE0F 表情形态）只影响渲染，不影响语义：
  // 同一个字符带不带它都是同一个字。映射表里只存一份，查表前先按码点去掉，
  // 免得表里出现一个肉眼看不见的键。
  // 这里用码点数字而不是正则字符类 —— 字符类要把变体选择符本身写进源码，
  // 而它是不可见的，改错了也看不出来。
  const stripped = [...emoji]
    .filter((ch) => {
      const cp = ch.codePointAt(0)
      return cp !== 0xfe0e && cp !== 0xfe0f
    })
    .join('')

  return EMOJI_TO_ICON[stripped] ?? fallback
}
