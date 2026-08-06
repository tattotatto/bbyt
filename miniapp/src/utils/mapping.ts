// ═══════════════════════════════════════════
//  HxMall Mapping Utilities
//  (pure TS — no uni dependency, testable in node)
// ═══════════════════════════════════════════

// ── Order Status (string-keyed, self-contained) ─────

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  pending_payment: { label: '待付款', color: '#FF7B7B' },
  paid:             { label: '待发货', color: '#FFD93D' },
  shipped:          { label: '已发货', color: '#7EC8E3' },
  confirmed:        { label: '已确认', color: '#A8D8B9' },
  completed:        { label: '已完成', color: '#A8D8B9' },
  cancelled:        { label: '已取消', color: '#7a6a5a' },
  refunding:        { label: '退款中', color: '#FF7B7B' },
}

const FALLBACK_STATUS = { label: '待付款', color: '#7a6a5a' }

/**
 * Map a backend string status to a Chinese display label.
 * Falls back to "待付款" for unknown statuses.
 */
export function orderStatusLabel(status: string): string {
  return STATUS_MAP[status]?.label ?? FALLBACK_STATUS.label
}

/**
 * Map a backend string status to its display color (hex).
 * Falls back to "#7a6a5a" for unknown statuses.
 */
export function orderStatusColor(status: string): string {
  return STATUS_MAP[status]?.color ?? FALLBACK_STATUS.color
}

// ── Price Utilities ──────────────────────────────────

/**
 * Convert an integer amount in cents to a yuan display string.
 * @example formatCents(3500) => "¥35.00"
 */
export function formatCents(cents: number): string {
  return `¥${(cents / 100).toFixed(2)}`
}

/**
 * Extract the global min and max price across all tier pricing rules.
 * Returns { min: null, max: null } when the rules object is empty.
 */
export function parsePriceRange(
  pricing_rules: Record<string, { qty: number; price: number }[]>
): { min: number | null; max: number | null } {
  const allPrices: number[] = []
  for (const level of Object.values(pricing_rules)) {
    for (const rule of level) {
      allPrices.push(rule.price)
    }
  }
  if (allPrices.length === 0) {
    return { min: null, max: null }
  }
  return { min: Math.min(...allPrices), max: Math.max(...allPrices) }
}
