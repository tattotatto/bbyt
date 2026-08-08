import { describe, it, expect } from 'vitest'
import { BASE_URL } from '../request'
import { API_BASE_URL } from '../../utils/constants'

describe('request base url', () => {
  it('uses the shared API_BASE_URL', () => {
    expect(BASE_URL).toBe(API_BASE_URL)
  })
})
