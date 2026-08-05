// api/orders.ts — 订单管理 API
import request from './request'
import type { PaginatedResult } from './products'

export interface OrderItem {
  id: string
  order_no: string
  type: string                    // physical_goods | store_design
  retailer: {
    id: string
    phone: string
    company_name?: string
  }
  items: {
    product_id: string
    name: string
    qty: number
    unit_price: number            // 单位：分
    subtotal: number              // 单位：分
  }[]
  total_amount: number            // 单位：分
  payment_method: string          // wechat_pay | bank_transfer | credit
  payment_status: string          // pending | paid | confirmed | overdue
  status: string                  // pending_payment | paid | shipped | confirmed | completed | cancelled
  bank_receipt_url?: string       // 银行转账凭证图片
  store_design_detail?: {
    store_area?: string
    style_preference?: string
    budget_range?: string
    assigned_designer?: {
      id: string
      name: string
    }
    attachments?: string[]
    delivery_progress?: string
  }
  created_at: string
  updated_at: string
}

export interface OrderListParams {
  page?: number
  page_size?: number
  status?: string
  payment_status?: string
  keyword?: string
  type?: string
}

export function getOrderList(params: OrderListParams): Promise<PaginatedResult<OrderItem>> {
  return request.get('/orders/admin', { params }).then((res) => res.data)
}

export function getOrderDetail(id: string): Promise<OrderItem> {
  return request.get(`/orders/${id}`).then((res) => res.data)
}

export function updateOrderStatus(id: string, status: string): Promise<any> {
  return request.put(`/orders/${id}/status`, { status }).then((res) => res.data)
}

export function assignDesigner(orderId: string, designerId: string): Promise<any> {
  return request.post(`/orders/${orderId}/assign`, { designer_id: designerId }).then((res) => res.data)
}
