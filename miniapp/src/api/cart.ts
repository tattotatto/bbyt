import http from './request'

// ── Types ─────────────────────────────────────────────────────────────────────
export interface CartItemOut {
  id: string; product_id: string; name: string; image: string | null; spec: string;
  quantity: number; unit_price_min: number | null; unit_price_max: number | null;
  stock: number | null; min_order_qty: number
}

// ── API functions ─────────────────────────────────────────────────────────────
export const getCart = () => http.get<CartItemOut[]>('/cart')
export const addCartItem = (data: { product_id: string; spec?: string; quantity: number }) =>
  http.post<CartItemOut>('/cart', data)
export const updateCartItem = (id: string, quantity: number) =>
  http.put<CartItemOut>(`/cart/${id}`, { quantity })
export const removeCartItem = (id: string) => http.delete(`/cart/${id}`)
export const clearCart = () => http.delete('/cart')
