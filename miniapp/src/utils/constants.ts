// ═══════════════════════════════════════════
//  HxMall Application Constants
// ═══════════════════════════════════════════

// ── API Configuration ──────────────────────
export const API_BASE_URL = 'https://baby.mx.yn.cn/api/v1'

// ── Storage Keys ───────────────────────────
export const STORAGE_KEYS = {
  TOKEN: 'hxmall_token',
  REFRESH_TOKEN: 'hxmall_refresh_token',
  USER_INFO: 'hxmall_user_info',
  CART: 'hxmall_cart',
  SEARCH_HISTORY: 'hxmall_search_history'
} as const

// ── User Levels ────────────────────────────
export const USER_LEVELS = {
  NORMAL: { level: 0, label: '普通会员', discount: 1 },
  SILVER: { level: 1, label: '银卡会员', discount: 0.95 },
  GOLD: { level: 2, label: '金卡会员', discount: 0.9 },
  DIAMOND: { level: 3, label: '钻石会员', discount: 0.85 }
} as const

// ── Pagination ─────────────────────────────
export const PAGE_SIZE = 20

// ── Upload Limits ──────────────────────────
export const UPLOAD_MAX_SIZE = 10 * 1024 * 1024 // 10MB
export const UPLOAD_ALLOWED_TYPES = ['jpg', 'jpeg', 'png', 'gif', 'webp'] as const

// ── Age Ranges (Children's Products) ────────
export const AGE_RANGES = [
  { value: '0-1岁', label: '0-1岁' },
  { value: '1-3岁', label: '1-3岁' },
  { value: '3-6岁', label: '3-6岁' },
  { value: '6-12岁', label: '6-12岁' }
] as const

// ── Safety Certifications ──────────────────
export const SAFETY_CERTS = [
  { value: '3C', label: '3C认证', icon: 'shield' },
  { value: 'CE', label: 'CE认证', icon: 'shield' },
  { value: 'FDA', label: 'FDA认证', icon: 'shield' },
  { value: 'ISO', label: 'ISO认证', icon: 'shield' },
  { value: 'EN71', label: 'EN71认证', icon: 'shield' }
] as const

// ── Payment Methods ─────────────────────────
export const PAYMENT_METHODS = [
  { value: 'wechat', label: '微信支付', icon: 'wechat-fill' },
  { value: 'alipay', label: '支付宝', icon: 'alipay' },
  { value: 'balance', label: '余额支付', icon: 'rmb-circle-fill' }
] as const

// ── Shipping Status ─────────────────────────
export const SHIPPING_STATUS = {
  NOT_SHIPPED: { code: 0, label: '未发货' },
  SHIPPED: { code: 1, label: '运输中' },
  DELIVERED: { code: 2, label: '已签收' },
  RETURNED: { code: 3, label: '已退回' }
} as const

// ── Product Sort Options ────────────────────
export const SORT_OPTIONS = [
  { value: 'default', label: '综合' },
  { value: 'sales_desc', label: '销量' },
  { value: 'price_asc', label: '价格升序' },
  { value: 'price_desc', label: '价格降序' },
  { value: 'newest', label: '最新' }
] as const

// ── Review Ratings ──────────────────────────
export const REVIEW_RATINGS = [
  { value: 5, label: '好评' },
  { value: 4, label: '中评' },
  { value: 1, label: '差评' }
] as const

// ── Gender Options (Children) ───────────────
export const GENDER_OPTIONS = [
  { value: 'all', label: '全部' },
  { value: 'boy', label: '男童' },
  { value: 'girl', label: '女童' },
  { value: 'unisex', label: '中性' }
] as const
