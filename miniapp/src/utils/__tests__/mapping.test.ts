import { describe, it, expect } from 'vitest'
import { orderStatusLabel, orderStatusColor, orderStatusBg, formatCents, parsePriceRange } from '../mapping'
import { buildOrderItems } from '../index'

describe('orderStatusLabel', () => {
  it('maps backend string status to Chinese label', () => {
    expect(orderStatusLabel('pending_payment')).toBe('待付款')
    expect(orderStatusLabel('paid')).toBe('待发货')
    expect(orderStatusLabel('shipped')).toBe('已发货')
    expect(orderStatusLabel('confirmed')).toBe('已确认')
    expect(orderStatusLabel('completed')).toBe('已完成')
    expect(orderStatusLabel('cancelled')).toBe('已取消')
    expect(orderStatusLabel('refunding')).toBe('退款中')
    expect(orderStatusLabel('unknown_status')).toBe('待付款') // 兜底
  })
})

describe('orderStatusColor', () => {
  it('returns color for known status and fallback otherwise', () => {
    expect(orderStatusColor('pending_payment')).toBe('#FF7B7B')
    expect(orderStatusColor('nope')).toBe('#7a6a5a')
  })
})

describe('orderStatusBg', () => {
  it('returns bg color for known status and fallback otherwise', () => {
    expect(orderStatusBg('pending_payment')).toBe('#FFF0F0')
    expect(orderStatusBg('paid')).toBe('#FFF8F0')
    expect(orderStatusBg('shipped')).toBe('#F0F8FB')
    expect(orderStatusBg('confirmed')).toBe('#F2FAF5')
    expect(orderStatusBg('completed')).toBe('#F2FAF5')
    expect(orderStatusBg('cancelled')).toBe('#F5F5F5')
    expect(orderStatusBg('refunding')).toBe('#FFF0F0')
    expect(orderStatusBg('unknown_status')).toBe('#F5F5F5')
  })
})

describe('formatCents', () => {
  it('converts cents to yuan string', () => {
    expect(formatCents(3500)).toBe('¥35.00')
    expect(formatCents(0)).toBe('¥0.00')
    expect(formatCents(99)).toBe('¥0.99')
    expect(formatCents(123456)).toBe('¥1234.56')
  })
  it('rounds float cents before conversion', () => {
    expect(formatCents(19.9)).toBe('¥0.20')
    expect(formatCents(100.4)).toBe('¥1.00')
    expect(formatCents(199.6)).toBe('¥2.00')
  })
})

describe('parsePriceRange', () => {
  it('extracts min/max across all level rules', () => {
    const rules = {
      normal: [{ qty: 10, price: 30 }, { qty: 100, price: 25 }],
      gold: [{ qty: 10, price: 28 }],
    }
    expect(parsePriceRange(rules)).toEqual({ min: 25, max: 30 })
  })
  it('returns nulls on empty rules', () => {
    expect(parsePriceRange({})).toEqual({ min: null, max: null })
  })
  it('handles single level with single tier (min === max)', () => {
    const rules = {
      normal: [{ qty: 10, price: 32.0 }],
    }
    expect(parsePriceRange(rules)).toEqual({ min: 32, max: 32 })
  })
  it('handles single level with multiple tiers', () => {
    const rules = {
      gold: [
        { qty: 10, price: 25.0 },
        { qty: 50, price: 20.0 },
        { qty: 100, price: 16.0 },
      ],
    }
    expect(parsePriceRange(rules)).toEqual({ min: 16, max: 25 })
  })
})

describe('buildOrderItems', () => {
  it('maps cart items to backend order item shape', () => {
    const out = buildOrderItems([
      { productId: 'p1', productName: '泳圈', productImage: 'img.png', spec: '红色', quantity: 5, unitPrice: 35 },
    ])
    expect(out[0]).toEqual({ product_id: 'p1', name: '泳圈 / 红色', qty: 5, unit_price: 35, subtotal: 175, image: 'img.png' })
  })
  it('handles no spec', () => {
    const out = buildOrderItems([{ productId: 'p1', productName: '泳圈', productImage: '', quantity: 2, unitPrice: 30 }])
    expect(out[0].name).toBe('泳圈')
  })
  it('returns empty array for empty input', () => {
    expect(buildOrderItems([])).toEqual([])
  })
})
