import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getCart,
  addCartItem,
  updateCartItem,
  removeCartItem,
  clearCart,
} from '../api/cart'
import type { CartItemOut } from '../api/cart'
import { useUserStore } from './user'

// ── Local CartItem (extends backend shape with checked) ──────────────────────
interface CartItem {
  id: string
  productId: string
  productName: string
  productImage: string
  spec: string
  unitPrice: number
  quantity: number
  stock: number
  minOrderQty: number
  checked: boolean
}

// ── Map backend CartItemOut → local CartItem ─────────────────────────────────
function mapCartItem(out: CartItemOut): CartItem {
  return {
    id: out.id,
    productId: out.product_id,
    productName: out.name,
    productImage: out.image ?? '',
    spec: out.spec,
    unitPrice: out.unit_price_min ?? 0,
    quantity: out.quantity,
    stock: out.stock ?? 0,
    minOrderQty: out.min_order_qty,
    checked: true,
  }
}

export const useCartStore = defineStore('cart', () => {
  // ── State ──────────────────────────────────────────────────────────────────
  const items = ref<CartItem[]>([])

  // ── Getters ────────────────────────────────────────────────────────────────
  const totalCount = computed(() =>
    items.value.reduce((sum, item) => sum + item.quantity, 0),
  )
  const checkedItems = computed(() =>
    items.value.filter(item => item.checked),
  )
  const checkedCount = computed(() =>
    checkedItems.value.reduce((sum, item) => sum + item.quantity, 0),
  )
  const totalPrice = computed(() =>
    checkedItems.value.reduce((sum, item) => sum + item.unitPrice * item.quantity, 0),
  )
  const isAllChecked = computed(() =>
    items.value.length > 0 && items.value.every(item => item.checked),
  )
  const isEmpty = computed(() => items.value.length === 0)

  // ── Actions ────────────────────────────────────────────────────────────────

  /** Fetch cart from backend. If not logged in, clears items.
   *  Preserves locally-unchecked state for items that still exist after fetch. */
  async function fetch(): Promise<void> {
    const user = useUserStore()
    if (!user.isLoggedIn) {
      items.value = []
      return
    }
    try {
      const res = await getCart()
      // Record currently-unchecked item IDs so we can restore after rebuild
      const uncheckedIds = new Set(
        items.value.filter(i => !i.checked).map(i => i.id),
      )
      items.value = (res.data || []).map(mapCartItem)
      // Restore unchecked state for items that still exist in the new list
      for (const item of items.value) {
        if (uncheckedIds.has(item.id)) {
          item.checked = false
        }
      }
    } catch {
      // Silently keep current items on error
    }
  }

  /** Add item to cart. Requires login. */
  async function addItem(input: {
    productId: string
    productName: string
    productImage?: string
    spec?: string
    quantity: number
    stock?: number
    minOrderQty?: number
  }): Promise<void> {
    const user = useUserStore()
    if (!user.isLoggedIn) {
      uni.showToast({ title: '请先登录', icon: 'none' })
      return
    }
    try {
      await addCartItem({
        product_id: input.productId,
        spec: input.spec,
        quantity: input.quantity,
      })
      await fetch()
    } catch {
      // Error already shown by request interceptor
    }
  }

  /** Update cart item quantity by cart item id. */
  async function updateQuantity(id: string, quantity: number): Promise<void> {
    try {
      await updateCartItem(id, quantity)
      await fetch()
    } catch {
      // Error already shown by request interceptor
    }
  }

  /** Remove item from cart by cart item id. */
  async function removeItem(id: string): Promise<void> {
    try {
      await removeCartItem(id)
      await fetch()
    } catch {
      // Error already shown by request interceptor
    }
  }

  /** Clear entire cart. */
  async function clearCartRemote(): Promise<void> {
    try {
      await clearCart()
      items.value = []
    } catch {
      // Error already shown by request interceptor
    }
  }

  // ── Local UI state (checked) ───────────────────────────────────────────────

  /** Toggle checked state of a single cart item by cart item id. */
  function toggleChecked(id: string) {
    const item = items.value.find(i => i.id === id)
    if (item) {
      item.checked = !item.checked
    }
  }

  /** Toggle all items checked/unchecked. */
  function toggleAllChecked() {
    const newChecked = !isAllChecked.value
    items.value.forEach(item => {
      item.checked = newChecked
    })
  }

  /** Get items that are checked (for checkout). */
  function getCheckoutItems(): CartItem[] {
    return items.value.filter(item => item.checked)
  }

  /** Remove all checked items (called after order submission). */
  async function removeCheckedItems(): Promise<void> {
    const checked = items.value.filter(item => item.checked)
    if (checked.length === 0) return
    try {
      // Remove each checked item via API
      await Promise.all(checked.map(item => removeCartItem(item.id)))
      await fetch()
    } catch {
      // Error already shown by request interceptor
    }
  }

  return {
    // State
    items,
    // Getters
    totalCount,
    checkedItems,
    checkedCount,
    totalPrice,
    isAllChecked,
    isEmpty,
    // Actions
    fetch,
    addItem,
    updateQuantity,
    removeItem,
    clearCart: clearCartRemote,
    toggleChecked,
    toggleAllChecked,
    getCheckoutItems,
    removeCheckedItems,
  }
})
