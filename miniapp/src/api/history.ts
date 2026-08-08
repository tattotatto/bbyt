import http from './request'
import type { Paginated } from './types'

// ── Types ─────────────────────────────────────────────────────────────────────
export interface HistoryItemOut {
  product_id: string; name: string; image: string | null;
  price_min: number | null; price_max: number | null; viewed_at: string
}

// ── API functions ─────────────────────────────────────────────────────────────
export const getHistory = (params?: { page?: number; page_size?: number }) =>
  http.get<Paginated<HistoryItemOut>>('/history', params)
export const addHistory = (product_id: string) => http.post('/history', { product_id })
export const removeHistory = (product_id: string) => http.delete(`/history/${product_id}`)
export const clearHistory = () => http.delete('/history')
