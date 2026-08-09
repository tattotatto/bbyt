import { describe, it, expect } from 'vitest'
import { validateAddressForm, buildAddressPayload } from '../address'

// ── Test data ───────────────────────────────────────────────────────────────────
const validForm = {
  name: '张三',
  phone: '13800138000',
  province: '广东省',
  city: '深圳市',
  district: '南山区',
  detail: '科技园路1号',
  is_default: false,
}

// ═══════════════════════════════════════════════════════════════════════════════
//  validateAddressForm
// ═══════════════════════════════════════════════════════════════════════════════
describe('validateAddressForm', () => {
  // ── Valid input ──────────────────────────────────────────────────────────────
  it('returns ok:true with no errors for valid input', () => {
    const result = validateAddressForm(validForm)
    expect(result.ok).toBe(true)
    expect(result.errors).toEqual({})
  })

  it('returns ok:true when is_default is true', () => {
    const result = validateAddressForm({ ...validForm, is_default: true })
    expect(result.ok).toBe(true)
    expect(result.errors).toEqual({})
  })

  // ── Missing required fields ──────────────────────────────────────────────────
  it('returns error for missing name', () => {
    const result = validateAddressForm({ ...validForm, name: '' })
    expect(result.ok).toBe(false)
    expect(result.errors.name).toBeDefined()
  })

  it('returns error for whitespace-only name', () => {
    const result = validateAddressForm({ ...validForm, name: '   ' })
    expect(result.ok).toBe(false)
    expect(result.errors.name).toBeDefined()
  })

  it('returns error for missing phone', () => {
    const result = validateAddressForm({ ...validForm, phone: '' })
    expect(result.ok).toBe(false)
    expect(result.errors.phone).toBeDefined()
  })

  it('returns error for missing province', () => {
    const result = validateAddressForm({ ...validForm, province: '' })
    expect(result.ok).toBe(false)
    expect(result.errors.province).toBeDefined()
  })

  it('returns error for missing city', () => {
    const result = validateAddressForm({ ...validForm, city: '' })
    expect(result.ok).toBe(false)
    expect(result.errors.city).toBeDefined()
  })

  it('returns error for missing district', () => {
    const result = validateAddressForm({ ...validForm, district: '' })
    expect(result.ok).toBe(false)
    expect(result.errors.district).toBeDefined()
  })

  it('returns error for missing detail', () => {
    const result = validateAddressForm({ ...validForm, detail: '' })
    expect(result.ok).toBe(false)
    expect(result.errors.detail).toBeDefined()
  })

  // ── Multiple missing fields ──────────────────────────────────────────────────
  it('returns multiple errors when several fields are missing', () => {
    const result = validateAddressForm({ name: '', phone: '', province: '', city: '', district: '', detail: '' })
    expect(result.ok).toBe(false)
    expect(Object.keys(result.errors).length).toBe(6)
  })

  // ── Invalid phone formats ────────────────────────────────────────────────────
  it('returns error for phone not matching 1[3-9]xxxxxxxxx pattern', () => {
    const result = validateAddressForm({ ...validForm, phone: '12345678901' })
    expect(result.ok).toBe(false)
    expect(result.errors.phone).toBeDefined()
  })

  it('returns error for phone too short', () => {
    const result = validateAddressForm({ ...validForm, phone: '1380013800' })
    expect(result.ok).toBe(false)
    expect(result.errors.phone).toBeDefined()
  })

  it('returns error for phone too long', () => {
    const result = validateAddressForm({ ...validForm, phone: '138001380000' })
    expect(result.ok).toBe(false)
    expect(result.errors.phone).toBeDefined()
  })

  it('returns error for phone with letters', () => {
    const result = validateAddressForm({ ...validForm, phone: '1380013800a' })
    expect(result.ok).toBe(false)
    expect(result.errors.phone).toBeDefined()
  })

  it('returns error for phone starting with 2', () => {
    const result = validateAddressForm({ ...validForm, phone: '23800138000' })
    expect(result.ok).toBe(false)
    expect(result.errors.phone).toBeDefined()
  })

  // ── Edge: phone error + field error together ─────────────────────────────────
  it('returns both phone and field error when both are invalid', () => {
    const result = validateAddressForm({ ...validForm, name: '', phone: '12345678901' })
    expect(result.ok).toBe(false)
    expect(result.errors.name).toBeDefined()
    expect(result.errors.phone).toBeDefined()
  })

  // ── Undefined / null fields ──────────────────────────────────────────────────
  it('handles undefined fields as empty', () => {
    const result = validateAddressForm({ name: undefined, phone: undefined } as any)
    expect(result.ok).toBe(false)
    expect(result.errors.name).toBeDefined()
    expect(result.errors.phone).toBeDefined()
  })
})

// ═══════════════════════════════════════════════════════════════════════════════
//  buildAddressPayload
// ═══════════════════════════════════════════════════════════════════════════════
describe('buildAddressPayload', () => {
  it('trims all string fields', () => {
    const payload = buildAddressPayload({
      name: '  张三  ',
      phone: '  13800138000  ',
      province: '  广东省  ',
      city: '  深圳市  ',
      district: '  南山区  ',
      detail: '  科技园路1号  ',
    })
    expect(payload.name).toBe('张三')
    expect(payload.phone).toBe('13800138000')
    expect(payload.province).toBe('广东省')
    expect(payload.city).toBe('深圳市')
    expect(payload.district).toBe('南山区')
    expect(payload.detail).toBe('科技园路1号')
  })

  it('preserves is_default true', () => {
    const payload = buildAddressPayload({
      name: '李四',
      phone: '13900139000',
      province: '北京市',
      city: '北京市',
      district: '朝阳区',
      detail: '望京路2号',
      is_default: true,
    })
    expect(payload.is_default).toBe(true)
  })

  it('preserves is_default false', () => {
    const payload = buildAddressPayload({
      name: '王五',
      phone: '13700137000',
      province: '上海市',
      city: '上海市',
      district: '浦东新区',
      detail: '陆家嘴',
      is_default: false,
    })
    expect(payload.is_default).toBe(false)
  })

  it('defaults is_default to false when undefined', () => {
    const payload = buildAddressPayload({
      name: '赵六',
      phone: '13600136000',
      province: '浙江省',
      city: '杭州市',
      district: '西湖区',
      detail: '文三路',
    })
    expect(payload.is_default).toBe(false)
  })

  it('handles empty strings without crashing', () => {
    const payload = buildAddressPayload({
      name: '',
      phone: '',
      province: '',
      city: '',
      district: '',
      detail: '',
    })
    expect(payload.name).toBe('')
    expect(payload.phone).toBe('')
  })

  it('does not include extra keys', () => {
    const payload = buildAddressPayload({
      name: '张三',
      phone: '13800138000',
      province: '广东省',
      city: '深圳市',
      district: '南山区',
      detail: '科技园路1号',
      is_default: false,
      extraField: 'should not appear',
    } as any)
    const keys = Object.keys(payload)
    expect(keys).toContain('name')
    expect(keys).toContain('phone')
    expect(keys).toContain('province')
    expect(keys).toContain('city')
    expect(keys).toContain('district')
    expect(keys).toContain('detail')
    expect(keys).toContain('is_default')
    expect(keys).not.toContain('extraField')
  })
})
