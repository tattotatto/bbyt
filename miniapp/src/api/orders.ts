import http from './request'
import type { Paginated } from './types'

// ── Order types ───────────────────────────────────────────────────────────────
export interface OrderItem {
  product_id: string; name: string; qty: number; unit_price: number; subtotal: number; image?: string | null
}
export interface Order {
  id: string; order_no: string; type: string; retailer_id: string; items: OrderItem[];
  total_amount: number; payment_method: string | null; payment_status: string; status: string;
  receiver_name?: string | null; receiver_phone?: string | null; receiver_address?: string | null;
  remark?: string | null; timeline?: unknown[]; created_at?: string | null
}
export interface CreateOrderParams {
  items: { product_id: string; name: string; qty: number; unit_price: number; subtotal: number }[];
  payment_method: string; remark?: string; receiver_name?: string; receiver_phone?: string; receiver_address?: string
}

// ── API functions ─────────────────────────────────────────────────────────────
export const createOrder = (params: CreateOrderParams) => http.post<Order>('/orders', params)
export const getOrderList = (params?: { page?: number; page_size?: number; status?: string }) =>
  http.get<Paginated<Order>>('/orders', params)
export const getOrderDetail = (id: string) => http.get<Order>(`/orders/${id}`)
export const cancelOrder = (id: string) => http.post(`/orders/${id}/cancel`)
export const confirmReceipt = (id: string) => http.post(`/orders/${id}/confirm`)
export const requestRefund = (id: string) => http.post(`/orders/${id}/refund`)
