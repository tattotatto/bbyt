import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface CartItem {
  productId: number
  productName: string
  productImage: string
  spec: string          // Selected spec, e.g. "红色 / L码"
  unitPrice: number
  quantity: number
  stock: number
  minOrderQty: number   // MOQ
  checked: boolean
}

const CART_STORAGE_KEY = 'hxmall_cart'

export const useCartStore = defineStore('cart', () => {
  // State
  const items = ref<CartItem[]>([])

  // Getters
  const totalCount = computed(() => items.value.reduce((sum, item) => sum + item.quantity, 0))
  const checkedItems = computed(() => items.value.filter(item => item.checked))
  const checkedCount = computed(() => checkedItems.value.reduce((sum, item) => sum + item.quantity, 0))
  const totalPrice = computed(() => checkedItems.value.reduce((sum, item) => sum + item.unitPrice * item.quantity, 0))
  const isAllChecked = computed(() => items.value.length > 0 && items.value.every(item => item.checked))
  const isEmpty = computed(() => items.value.length === 0)

  // Actions

  // Initialize: load from storage
  function init() {
    try {
      const saved = uni.getStorageSync(CART_STORAGE_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed)) items.value = parsed
      }
    } catch { /* ignore */ }
  }

  // Persist to storage
  function persist() {
    try {
      uni.setStorageSync(CART_STORAGE_KEY, JSON.stringify(items.value))
    } catch { /* ignore */ }
  }

  // Add item to cart
  function addItem(item: Omit<CartItem, 'checked'>) {
    const existing = items.value.find(
      i => i.productId === item.productId && i.spec === item.spec
    )
    if (existing) {
      existing.quantity += item.quantity
      // Don't exceed stock
      if (existing.quantity > existing.stock) {
        existing.quantity = existing.stock
      }
    } else {
      items.value.push({ ...item, checked: true })
    }
    persist()
  }

  // Remove item from cart
  function removeItem(productId: number, spec: string) {
    const index = items.value.findIndex(i => i.productId === productId && i.spec === spec)
    if (index > -1) {
      items.value.splice(index, 1)
      persist()
    }
  }

  // Update item quantity
  function updateQuantity(productId: number, spec: string, quantity: number) {
    const item = items.value.find(i => i.productId === productId && i.spec === spec)
    if (item) {
      if (quantity < item.minOrderQty) {
        uni.showToast({ title: `最低起订量${item.minOrderQty}件`, icon: 'none' })
        return
      }
      if (quantity > item.stock) {
        uni.showToast({ title: '库存不足', icon: 'none' })
        item.quantity = item.stock
      } else {
        item.quantity = quantity
      }
      persist()
    }
  }

  // Toggle item checked
  function toggleChecked(productId: number, spec: string) {
    const item = items.value.find(i => i.productId === productId && i.spec === spec)
    if (item) {
      item.checked = !item.checked
      persist()
    }
  }

  // Toggle all checked
  function toggleAllChecked() {
    const newChecked = !isAllChecked.value
    items.value.forEach(item => { item.checked = newChecked })
    persist()
  }

  // Clear checked items
  function removeCheckedItems() {
    items.value = items.value.filter(item => !item.checked)
    persist()
  }

  // Clear all items
  function clearCart() {
    items.value = []
    persist()
  }

  // Get items ready for checkout (only checked ones)
  function getCheckoutItems(): CartItem[] {
    return items.value.filter(item => item.checked)
  }

  return {
    // State
    items,
    // Getters
    totalCount, checkedItems, checkedCount, totalPrice, isAllChecked, isEmpty,
    // Actions
    init, addItem, removeItem, updateQuantity, toggleChecked, toggleAllChecked,
    removeCheckedItems, clearCart, getCheckoutItems
  }
})
