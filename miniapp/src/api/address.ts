import http from './request'

// ── Types ─────────────────────────────────────────────────────────────────────
export interface Address {
  id: string; name: string; phone: string; province: string; city: string;
  district: string; detail: string; is_default: boolean
}

// ── API functions ─────────────────────────────────────────────────────────────
export const getAddressList = () => http.get<Address[]>('/users/addresses')
export const createAddress = (data: Partial<Address>) => http.post<Address>('/users/addresses', data)
export const updateAddress = (id: string, data: Partial<Address>) => http.put<Address>(`/users/addresses/${id}`, data)
export const deleteAddress = (id: string) => http.delete(`/users/addresses/${id}`)
