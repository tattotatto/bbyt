// ═══════════════════════════════════════════
//  HxMall Utility Functions
// ═══════════════════════════════════════════

// ── Price Formatting ──────────────────────────────────

/**
 * Format price to 2 decimal places with ¥ symbol.
 * @example formatPrice(29.9) => "¥29.90"
 */
export function formatPrice(price: number): string {
  return `¥${price.toFixed(2)}`
}

/**
 * Format a price range (min - max).
 * When min equals max, displays a single price.
 * @example formatPriceRange(19.9, 39.9) => "¥19.90 - ¥39.90"
 */
export function formatPriceRange(min: number, max: number): string {
  if (min === max) return formatPrice(min)
  return `${formatPrice(min)} - ${formatPrice(max)}`
}

/**
 * Format price as integer (no decimals) when price is a whole number,
 * otherwise keep 2 decimal places.
 * @example formatPriceSmart(29) => "¥29" | formatPriceSmart(29.9) => "¥29.90"
 */
export function formatPriceSmart(price: number): string {
  if (Number.isInteger(price)) {
    return `¥${price}`
  }
  return formatPrice(price)
}

/**
 * Parse a formatted price string back to a number.
 * @example parsePrice("¥29.90") => 29.9
 */
export function parsePrice(priceStr: string): number {
  return parseFloat(priceStr.replace(/[^0-9.]/g, '')) || 0
}

// ── Debounce & Throttle ──────────────────────────────

/**
 * Creates a debounced version of the provided function.
 * The debounced function delays invoking `fn` until after `delay` milliseconds
 * have elapsed since the last time the debounced function was invoked.
 */
export function debounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout> | null = null
  return function (this: any, ...args: Parameters<T>) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
      timer = null
    }, delay)
  }
}

/**
 * Creates a throttled version of the provided function.
 * The throttled function invokes `fn` at most once per every `delay` milliseconds.
 */
export function throttle<T extends (...args: any[]) => any>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let lastTime = 0
  let timer: ReturnType<typeof setTimeout> | null = null
  return function (this: any, ...args: Parameters<T>) {
    const now = Date.now()
    const remaining = delay - (now - lastTime)

    if (remaining <= 0) {
      if (timer) {
        clearTimeout(timer)
        timer = null
      }
      lastTime = now
      fn.apply(this, args)
    } else if (!timer) {
      timer = setTimeout(() => {
        lastTime = Date.now()
        timer = null
        fn.apply(this, args)
      }, remaining)
    }
  }
}

// ── Validation ───────────────────────────────────────

/**
 * Validate Chinese mainland mobile phone number.
 */
export function isValidPhone(phone: string): boolean {
  return /^1[3-9]\d{9}$/.test(phone)
}

/**
 * Validate email address format.
 */
export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

/**
 * Validate ID number (Chinese 18-digit).
 */
export function isValidIdCard(idCard: string): boolean {
  return /^[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/.test(
    idCard
  )
}

/**
 * Check if value is empty (null, undefined, empty string, empty array).
 */
export function isEmpty(value: any): boolean {
  if (value === null || value === undefined) return true
  if (typeof value === 'string') return value.trim() === ''
  if (Array.isArray(value)) return value.length === 0
  if (typeof value === 'object') return Object.keys(value).length === 0
  return false
}

// ── Date Formatting ─────────────────────────────────

/**
 * Format a date to "YYYY-MM-DD HH:mm" format.
 */
export function formatDate(date: string | number | Date): string {
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

/**
 * Format a date to "YYYY-MM-DD" format.
 */
export function formatDateShort(date: string | number | Date): string {
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Format a date to "MM-DD HH:mm" format (no year).
 */
export function formatDateCompact(date: string | number | Date): string {
  const d = new Date(date)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hours}:${minutes}`
}

/**
 * Get relative time description (just now, N minutes ago, etc.).
 */
export function getRelativeTime(date: string | number | Date): string {
  const now = Date.now()
  const target = new Date(date).getTime()
  const diff = now - target

  if (diff < 0) return formatDate(date)

  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (seconds < 60) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  if (days < 30) return `${Math.floor(days / 7)}周前`
  if (days < 365) return `${Math.floor(days / 30)}个月前`
  return formatDateShort(date)
}

// ── Age Range ────────────────────────────────────────

/**
 * Get display label for an age range key.
 * @example getAgeRangeLabel('0-1') => "0-1岁"
 */
export function getAgeRangeLabel(range: string): string {
  const ageMap: Record<string, string> = {
    '0-1': '0-1岁',
    '1-3': '1-3岁',
    '3-6': '3-6岁',
    '6-12': '6-12岁'
  }
  return ageMap[range] || range
}

// ── Text Utilities ──────────────────────────────────

/**
 * Truncate text with ellipsis if it exceeds the maximum length.
 */
export function truncateText(text: string, maxLength: number): string {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

/**
 * Truncate text in the middle, keeping start and end.
 * Useful for long IDs, wallet addresses, etc.
 * @example truncateMiddle("13812345678", 3, 4) => "138****5678"
 */
export function truncateMiddle(
  text: string,
  startLen: number,
  endLen: number
): string {
  if (!text) return ''
  if (text.length <= startLen + endLen) return text
  return text.slice(0, startLen) + '****' + text.slice(-endLen)
}

/**
 * Mask a phone number for privacy display.
 * @example maskPhone("13812345678") => "138****5678"
 */
export function maskPhone(phone: string): string {
  if (!phone || phone.length < 11) return phone
  return phone.slice(0, 3) + '****' + phone.slice(-4)
}

/**
 * Capitalize the first letter of a string.
 */
export function capitalize(str: string): string {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1)
}

// ── Number Utilities ────────────────────────────────

/**
 * Format a number with thousand separators.
 * @example formatNumber(12345) => "12,345"
 */
export function formatNumber(num: number): string {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

/**
 * Generate a random integer between min and max (inclusive).
 */
export function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

/**
 * Clamp a number between min and max.
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

// ── URL / Navigation ───────────────────────────────

/**
 * Build a query string from an object, ignoring null/undefined values.
 */
export function buildQuery(params: Record<string, any>): string {
  const parts: string[] = []
  for (const key of Object.keys(params)) {
    const val = params[key]
    if (val !== null && val !== undefined && val !== '') {
      parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(val))}`)
    }
  }
  return parts.length > 0 ? '?' + parts.join('&') : ''
}

/**
 * Parse query string from a URL into an object.
 */
export function parseQuery(url: string): Record<string, string> {
  const result: Record<string, string> = {}
  const queryString = url.split('?')[1]
  if (!queryString) return result
  const pairs = queryString.split('&')
  for (const pair of pairs) {
    const [key, val] = pair.split('=')
    if (key) {
      result[decodeURIComponent(key)] = val ? decodeURIComponent(val) : ''
    }
  }
  return result
}

// ── Image Utilities ────────────────────────────────

/**
 * Check if a file extension is an allowed image type.
 */
export function isAllowedImageType(filename: string): boolean {
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  return ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)
}

/**
 * Get the file extension from a filename or URL.
 */
export function getFileExtension(filename: string): string {
  return filename.split('.').pop()?.toLowerCase() || ''
}

// ── Cart → Order Items Mapping ──────────────────────

/** Input shape from cart store getCheckoutItems() */
export interface CartCheckoutItem {
  productId: string
  productName: string
  productImage?: string
  spec?: string
  quantity: number
  unitPrice: number
}

/** Output shape matching backend OrderCreate.items */
export interface OrderCreateItem {
  product_id: string
  name: string
  qty: number
  unit_price: number
  subtotal: number
  image?: string
}

/**
 * Map cart checkout items to backend order item shape.
 * Spec is appended to name as "productName / spec" when present.
 */
export function buildOrderItems(items: CartCheckoutItem[]): OrderCreateItem[] {
  return items.map((item) => ({
    product_id: item.productId,
    name: item.spec ? `${item.productName} / ${item.spec}` : item.productName,
    qty: item.quantity,
    unit_price: item.unitPrice,
    subtotal: parseFloat((item.unitPrice * item.quantity).toFixed(2)),
    ...(item.productImage ? { image: item.productImage } : {}),
  }))
}

// ── Deep Clone ─────────────────────────────────────

/**
 * Deep clone an object using JSON serialization.
 * Note: loses functions, undefined, Symbol, Date, etc.
 * For full-featured cloning, use lodash.cloneDeep or structuredClone.
 */
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') return obj
  return JSON.parse(JSON.stringify(obj))
}

// ── Platform Detection ─────────────────────────────

/**
 * Get platform info for the current mini program environment.
 */
export function getPlatformInfo() {
  try {
    const info = uni.getSystemInfoSync()
    return {
      platform: info.platform,
      isIOS: info.platform === 'ios',
      isAndroid: info.platform === 'android',
      isDevTools: info.platform === 'devtools',
      screenWidth: info.screenWidth,
      screenHeight: info.screenHeight,
      windowWidth: info.windowWidth,
      windowHeight: info.windowHeight,
      statusBarHeight: info.statusBarHeight || 0,
      safeArea: info.safeArea,
      pixelRatio: info.pixelRatio,
      version: info.version
    }
  } catch {
    return null
  }
}

/**
 * Convert rpx to px based on screen width.
 * Standard: 750rpx = screen width
 */
export function rpxToPx(rpx: number): number {
  try {
    const info = uni.getSystemInfoSync()
    return (rpx * info.screenWidth) / 750
  } catch {
    return rpx
  }
}

/**
 * Convert px to rpx based on screen width.
 */
export function pxToRpx(px: number): number {
  try {
    const info = uni.getSystemInfoSync()
    return (px * 750) / info.screenWidth
  } catch {
    return px
  }
}

// ── Storage Helpers ────────────────────────────────

/**
 * Safely get JSON data from uni storage.
 */
export function getStorageJSON<T = any>(key: string): T | null {
  try {
    const data = uni.getStorageSync(key)
    if (!data) return null
    if (typeof data === 'string') {
      return JSON.parse(data) as T
    }
    return data as T
  } catch {
    return null
  }
}

/**
 * Safely set JSON data to uni storage.
 */
export function setStorageJSON(key: string, value: any): void {
  try {
    uni.setStorageSync(key, JSON.stringify(value))
  } catch (err) {
    console.error(`[Storage] Failed to save key "${key}":`, err)
  }
}

/**
 * Safely remove a key from uni storage.
 */
export function removeStorage(key: string): void {
  try {
    uni.removeStorageSync(key)
  } catch (err) {
    console.error(`[Storage] Failed to remove key "${key}":`, err)
  }
}

/**
 * Clear all storage (useful for logout).
 */
export function clearStorage(): void {
  try {
    uni.clearStorageSync()
  } catch (err) {
    console.error('[Storage] Failed to clear storage:', err)
  }
}

// ── Toast Helpers ─────────────────────────────────

/**
 * Show a success toast message.
 */
export function showSuccess(title: string, duration = 2000): void {
  uni.showToast({ title, icon: 'success', duration })
}

/**
 * Show an error toast message.
 */
export function showError(title: string, duration = 2000): void {
  uni.showToast({ title, icon: 'error', duration })
}

/**
 * Show a loading toast that must be manually hidden.
 */
export function showLoading(title = '加载中...', mask = true): void {
  uni.showLoading({ title, mask })
}

/**
 * Hide the loading toast.
 */
export function hideLoading(): void {
  uni.hideLoading()
}

// ── 自定义导航栏的让位 ─────────────────────────

/**
 * 微信导航栏带的高度（px）。
 *
 * `navigationStyle: "custom"` 的页面里，状态栏下面这 44px 是微信留给自己
 * 胶囊按钮（··· 和 ◉）的：胶囊本身 87×32，在这一条里上下居中，也就是占
 * `statusBar + 6` ~ `statusBar + 38`。
 */
export const NAV_BAR_HEIGHT = 44

/**
 * 头图内容距页面顶部的距离（px）—— 让开右上角的微信胶囊按钮。
 *
 * ── 为什么需要这个函数 ────────────────────────────────────────────────
 *
 * 头图（BrandHero）是自定义导航页面里的第一个元素，内容默认就落在上面
 * 那条 44px 导航栏带里。右上角一旦摆上「登录 / 注册」白胶囊，两个白块
 * 就叠在一起。2026-10-11 开发者工具实测（素材/index2.png）：
 * 微信胶囊 y 38~69、登录胶囊 y 65~93，上沿被盖住 4px，视觉上粘成一块。
 * 原来的算式是 `statusBar + 20`，正好落进带内。
 *
 *   statusBar ─────┬─ 胶囊上沿 statusBar+6
 *                  │   胶囊 32px
 *                  ├─ 胶囊下沿 statusBar+38
 *   statusBar + 44 ──── 内容从这里开始（离胶囊下沿还有 6px 余量）
 *
 * 让位量取整条导航栏而不是「刚好差一点」：6px 是胶囊在带内居中留下的
 * 半格，任意状态栏高度下都成立，不需要按机型调数值。
 *
 * 右侧没有内容的页面不必让：左侧的品牌块和右上角的胶囊不在一处，
 * 保持原来的紧凑间距（compact 8px / 普通 20px）。
 *
 * @param statusBarHeight 设备状态栏高度（px），取不到时按 20 兜底
 * @param opts.showLogin  头图右上角有内容（登录胶囊）
 * @param opts.compact    紧凑变体（只放标题、右上角空着的页面）
 */
export function heroPaddingTop(
  statusBarHeight: number,
  opts: { showLogin?: boolean; compact?: boolean } = {}
): number {
  const statusBar = statusBarHeight || 20
  if (opts.showLogin) return statusBar + NAV_BAR_HEIGHT
  return statusBar + (opts.compact ? 8 : 20)
}

// ── Navigate Back or Home ─────────────────────────

/**
 * Navigate back, or to home if no previous page exists.
 */
export function goBackOrHome(): void {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack()
  } else {
    // 首页的真实路由是 /pages/home/index；原来写的 /pages/index/index
    // 根本没注册，switchTab 必然失败。
    uni.switchTab({ url: '/pages/home/index' })
  }
}
