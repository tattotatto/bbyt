import http from './request'

export interface OrderItem {
  product_id: number
  product_name: string
  product_image: string
  spec: string
  unit_price: number
  quantity: number
  total_price: number
}

export interface Order {
  id: number
  order_no: string
  status: number           // 0-5 matching ORDER_STATUS
  status_label: string
  items: OrderItem[]
  total_amount: number
  discount_amount: number
  final_amount: number
  shipping_address: Address
  shipping_method: string
  tracking_no?: string
  remark: string
  created_at: string
  paid_at?: string
  shipped_at?: string
  completed_at?: string
}

export interface Address {
  id?: number
  name: string
  phone: string
  province: string
  city: string
  district: string
  detail: string
  is_default: boolean
}

export interface CreateOrderParams {
  items: Array<{
    product_id: number
    spec: string
    quantity: number
  }>
  address_id: number
  remark?: string
}

export interface OrderListParams {
  page?: number
  page_size?: number
  status?: number
}

export interface OrderListResult {
  list: Order[]
  total: number
  page: number
  page_size: number
}

// Create order
export function createOrder(params: CreateOrderParams): Promise<{ data: { order_id: number; order_no: string; final_amount: number } }> {
  return http.post('/orders', params)
}

// Get order list
export function getOrderList(params: OrderListParams): Promise<{ data: OrderListResult }> {
  return http.get<OrderListResult>('/orders', params)
}

// Get order detail
export function getOrderDetail(id: number): Promise<{ data: Order }> {
  return http.get<Order>(`/orders/${id}`)
}

// Cancel order
export function cancelOrder(id: number, reason?: string): Promise<{ data: { success: boolean } }> {
  return http.put(`/orders/${id}/cancel`, { reason })
}

// Confirm receipt
export function confirmReceipt(id: number): Promise<{ data: { success: boolean } }> {
  return http.put(`/orders/${id}/confirm`)
}

// Request refund
export function requestRefund(id: number, reason: string): Promise<{ data: { success: boolean } }> {
  return http.post(`/orders/${id}/refund`, { reason })
}

// Get address list
export function getAddressList(): Promise<{ data: Address[] }> {
  return http.get<Address[]>('/user/addresses')
}

// Save address
export function saveAddress(address: Omit<Address, 'id'> & { id?: number }): Promise<{ data: Address }> {
  if (address.id) {
    return http.put<Address>(`/user/addresses/${address.id}`, address)
  }
  return http.post<Address>('/user/addresses', address)
}

// Delete address
export function deleteAddress(id: number): Promise<{ data: { success: boolean } }> {
  return http.delete(`/user/addresses/${id}`)
}
