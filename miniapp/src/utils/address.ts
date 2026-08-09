import type { Address } from '../api/address'

// ── Types ─────────────────────────────────────────────────────────────────────

/** Raw form data shape (before validation / trimming). */
export interface AddressFormData {
  name?: string
  phone?: string
  province?: string
  city?: string
  district?: string
  detail?: string
  is_default?: boolean
}

export interface AddressFormValidation {
  ok: boolean
  errors: Record<string, string>
}

// ── Constants ─────────────────────────────────────────────────────────────────

/** Required form fields (excluding is_default which is always optional). */
const REQUIRED_FIELDS = ['name', 'phone', 'province', 'city', 'district', 'detail'] as const

/** Chinese mainland mobile phone pattern: 1[3-9]xxxxxxxxx */
const PHONE_RE = /^1[3-9]\d{9}$/

// ── Validation ────────────────────────────────────────────────────────────────

/**
 * Validate address form data.
 *
 * Checks:
 * - All required fields (name, phone, province, city, district, detail) are non-empty after trim.
 * - Phone matches Chinese mainland mobile pattern `1[3-9]\d{9}`.
 *
 * @returns `{ ok: boolean, errors: Record<string, string> }`
 */
export function validateAddressForm(data: AddressFormData): AddressFormValidation {
  const errors: Record<string, string> = {}

  // Required non-empty checks
  for (const field of REQUIRED_FIELDS) {
    const value = (data as any)[field]
    if (typeof value !== 'string' || value.trim() === '') {
      errors[field] = getFieldLabel(field) + '不能为空'
    }
  }

  // Phone format check (only if phone is non-empty, to avoid duplicate messages)
  const phone = (data.phone ?? '').trim()
  if (phone.length > 0 && !PHONE_RE.test(phone)) {
    errors.phone = '请输入正确的11位手机号码'
  }

  return { ok: Object.keys(errors).length === 0, errors }
}

// ── Payload Builder ───────────────────────────────────────────────────────────

/**
 * Build a trimmed address payload from form data.
 *
 * All string fields are trimmed. is_default defaults to false when not provided.
 * Only the fields present on the Address type are included in the output.
 */
export function buildAddressPayload(form: AddressFormData): Partial<Address> {
  return {
    name: (form.name ?? '').trim(),
    phone: (form.phone ?? '').trim(),
    province: (form.province ?? '').trim(),
    city: (form.city ?? '').trim(),
    district: (form.district ?? '').trim(),
    detail: (form.detail ?? '').trim(),
    is_default: form.is_default ?? false,
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Human-readable label for each form field (used in error messages). */
function getFieldLabel(field: string): string {
  const labels: Record<string, string> = {
    name: '收货人',
    phone: '手机号码',
    province: '省份',
    city: '城市',
    district: '区/县',
    detail: '详细地址',
  }
  return labels[field] || field
}
