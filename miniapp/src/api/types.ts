// ── Shared API types ──────────────────────────────────────────────────────────
export interface Paginated<T> { items: T[]; total: number; page: number; page_size: number }
export interface Category { id: string; parent_id: string | null; name: string; icon: string | null; sort_order: number; status: string; children: Category[] }
export interface PricingTier { qty: number; price: number }
