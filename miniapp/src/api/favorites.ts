import http from './request'
import type { Paginated } from './types'

// ── Types ─────────────────────────────────────────────────────────────────────
export interface FavoriteItemOut {
  product_id: string; name: string; image: string | null;
  price_min: number | null; price_max: number | null; created_at: string
}

// ── API functions ─────────────────────────────────────────────────────────────
export const getFavorites = (params?: { page?: number; page_size?: number }) =>
  http.get<Paginated<FavoriteItemOut>>('/favorites', params)
export const addFavorite = (product_id: string) => http.post('/favorites', { product_id })
export const removeFavorite = (product_id: string) => http.delete(`/favorites/${product_id}`)
