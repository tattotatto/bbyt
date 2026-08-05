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

// ── Navigate Back or Home ─────────────────────────

/**
 * Navigate back, or to home if no previous page exists.
 */
export function goBackOrHome(): void {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack()
  } else {
    uni.switchTab({ url: '/pages/index/index' })
  }
}
