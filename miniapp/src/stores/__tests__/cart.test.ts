import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCartStore } from '../cart'
import { useUserStore } from '../user'
import * as cartApi from '../../api/cart'

vi.mock('../../api/cart', () => ({
  getCart: vi.fn(),
  addCartItem: vi.fn(),
  updateCartItem: vi.fn(),
  removeCartItem: vi.fn(),
  clearCart: vi.fn(),
}))

const storage: Record<string, string> = {}
const uniMock = {
  getStorageSync: (k: string) => storage[k] ?? '',
  setStorageSync: (k: string, v: string) => { storage[k] = String(v) },
  removeStorageSync: (k: string) => { delete storage[k] },
  showToast: vi.fn(),
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.stubGlobal('uni', uniMock)
  Object.keys(storage).forEach(k => delete storage[k])
  vi.clearAllMocks()
})

const BACKEND_CART_ITEM = {
  id: 'c1',
  product_id: 'p1',
  name: '泳圈',
  image: null,
  spec: '默认',
  quantity: 5,
  unit_price_min: 35,
  unit_price_max: 35,
  stock: 100,
  min_order_qty: 10,
}

describe('cart store backend sync', () => {
  it('fetch() populates items from backend when logged in', async () => {
    const user = useUserStore()
    user.updateToken('at')
    const mGet = cartApi.getCart as unknown as ReturnType<typeof vi.fn>
    mGet.mockResolvedValue({ data: [BACKEND_CART_ITEM] })
    const store = useCartStore()
    await store.fetch()
    expect(store.totalCount).toBe(5)
    expect(store.items[0].productId).toBe('p1')
  })

  it('addItem calls addCartItem then refreshes', async () => {
    const user = useUserStore()
    user.updateToken('at')
    const mAdd = cartApi.addCartItem as unknown as ReturnType<typeof vi.fn>
    mAdd.mockResolvedValue({ data: { id: 'c1' } })
    const mGet = cartApi.getCart as unknown as ReturnType<typeof vi.fn>
    mGet.mockResolvedValue({ data: [] })
    const store = useCartStore()
    await store.addItem({ productId: 'p1', productName: '泳圈', quantity: 5 })
    expect(mAdd).toHaveBeenCalledWith(expect.objectContaining({ product_id: 'p1', quantity: 5 }))
  })

  it('fetch() keeps items empty when not logged in', async () => {
    const store = useCartStore()
    await store.fetch()
    expect(store.items).toEqual([])
  })

  it('addItem shows toast when not logged in', async () => {
    const store = useCartStore()
    await store.addItem({ productId: 'p1', productName: '泳圈', quantity: 5 })
    expect(uniMock.showToast).toHaveBeenCalledWith(
      expect.objectContaining({ title: '请先登录' })
    )
  })

  it('updateQuantity calls updateCartItem then refreshes', async () => {
    const user = useUserStore()
    user.updateToken('at')
    const mUpd = cartApi.updateCartItem as unknown as ReturnType<typeof vi.fn>
    mUpd.mockResolvedValue({ data: BACKEND_CART_ITEM })
    const mGet = cartApi.getCart as unknown as ReturnType<typeof vi.fn>
    mGet.mockResolvedValue({ data: [] })
    const store = useCartStore()
    await store.updateQuantity('c1', 3)
    expect(mUpd).toHaveBeenCalledWith('c1', 3)
  })

  it('removeItem calls removeCartItem then refreshes', async () => {
    const user = useUserStore()
    user.updateToken('at')
    const mDel = cartApi.removeCartItem as unknown as ReturnType<typeof vi.fn>
    mDel.mockResolvedValue({ data: null })
    const mGet = cartApi.getCart as unknown as ReturnType<typeof vi.fn>
    mGet.mockResolvedValue({ data: [] })
    const store = useCartStore()
    await store.removeItem('c1')
    expect(mDel).toHaveBeenCalledWith('c1')
  })

  it('clearCart calls API clearCart then refreshes', async () => {
    const user = useUserStore()
    user.updateToken('at')
    const mClr = cartApi.clearCart as unknown as ReturnType<typeof vi.fn>
    mClr.mockResolvedValue({ data: null })
    const mGet = cartApi.getCart as unknown as ReturnType<typeof vi.fn>
    mGet.mockResolvedValue({ data: [] })
    const store = useCartStore()
    await store.clearCart()
    expect(mClr).toHaveBeenCalled()
  })

  it('toggleChecked toggles local checked field', () => {
    const store = useCartStore()
    // Manually set items (bypassing fetch for this local-only test)
    store.items.push({
      id: 'c1',
      productId: 'p1',
      productName: '泳圈',
      productImage: '',
      spec: '默认',
      unitPrice: 35,
      quantity: 1,
      stock: 100,
      minOrderQty: 1,
      checked: false,
    } as any)
    store.toggleChecked('c1')
    expect(store.items[0].checked).toBe(true)
  })

  it('toggleAllChecked toggles all items', () => {
    const store = useCartStore()
    store.items.push(
      { id: 'c1', productId: 'p1', productName: 'A', productImage: '', spec: '默认', unitPrice: 1, quantity: 1, stock: 10, minOrderQty: 1, checked: false } as any,
      { id: 'c2', productId: 'p2', productName: 'B', productImage: '', spec: '默认', unitPrice: 2, quantity: 1, stock: 10, minOrderQty: 1, checked: false } as any,
    )
    store.toggleAllChecked()
    expect(store.items[0].checked).toBe(true)
    expect(store.items[1].checked).toBe(true)
  })

  it('getCheckoutItems returns only checked items', () => {
    const store = useCartStore()
    store.items.push(
      { id: 'c1', productId: 'p1', productName: 'A', productImage: '', spec: '默认', unitPrice: 1, quantity: 1, stock: 10, minOrderQty: 1, checked: true } as any,
      { id: 'c2', productId: 'p2', productName: 'B', productImage: '', spec: '默认', unitPrice: 2, quantity: 1, stock: 10, minOrderQty: 1, checked: false } as any,
    )
    const checkout = store.getCheckoutItems()
    expect(checkout).toHaveLength(1)
    expect(checkout[0].productId).toBe('p1')
  })

  it('removeCheckedItems calls removeCartItem for each checked item', async () => {
    const user = useUserStore()
    user.updateToken('at')
    const mDel = cartApi.removeCartItem as unknown as ReturnType<typeof vi.fn>
    mDel.mockResolvedValue({ data: null })
    const mGet = cartApi.getCart as unknown as ReturnType<typeof vi.fn>
    mGet.mockResolvedValue({ data: [] })
    const store = useCartStore()
    store.items.push(
      { id: 'c1', productId: 'p1', productName: 'A', productImage: '', spec: '默认', unitPrice: 1, quantity: 1, stock: 10, minOrderQty: 1, checked: true } as any,
      { id: 'c2', productId: 'p2', productName: 'B', productImage: '', spec: '默认', unitPrice: 2, quantity: 1, stock: 10, minOrderQty: 1, checked: false } as any,
    )
    await store.removeCheckedItems()
    expect(mDel).toHaveBeenCalledTimes(1)
    expect(mDel).toHaveBeenCalledWith('c1')
  })
})
