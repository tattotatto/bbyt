import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  // State
  const systemInfo = ref<UniApp.GetSystemInfoResult | null>(null)
  const networkType = ref<string>('unknown')
  const isNetworkConnected = ref(true)
  const searchKeyword = ref('')
  const searchHistory = ref<string[]>([])
  const isPageLoading = ref(false)

  // Getters
  const statusBarHeight = computed(() => systemInfo.value?.statusBarHeight || 20)
  const navBarHeight = computed(() => 44) // WeChat mini program standard nav bar height
  const totalNavHeight = computed(() => statusBarHeight.value + navBarHeight.value)
  const windowWidth = computed(() => systemInfo.value?.windowWidth || 375)
  const windowHeight = computed(() => systemInfo.value?.windowHeight || 667)
  const isIOS = computed(() => {
    if (!systemInfo.value) return false
    return /ios/i.test(systemInfo.value.system || '')
  })
  const safeAreaBottom = computed(() => {
    if (!systemInfo.value?.safeAreaInsets) return 0
    return systemInfo.value.safeAreaInsets.bottom || 0
  })

  // Actions

  // Initialize: get system info and network status
  function init() {
    // Get system info
    try {
      const info = uni.getSystemInfoSync()
      systemInfo.value = info as UniApp.GetSystemInfoResult
    } catch { /* ignore */ }

    // Get network type
    uni.getNetworkType({
      success: (res) => {
        networkType.value = res.networkType || 'unknown'
        isNetworkConnected.value = res.networkType !== 'none'
      }
    })

    // Listen to network changes
    uni.onNetworkStatusChange((res) => {
      networkType.value = res.networkType
      isNetworkConnected.value = res.isConnected
    })

    // Load search history
    try {
      const history = uni.getStorageSync('hxmall_search_history')
      if (history) {
        try {
          searchHistory.value = JSON.parse(history)
        } catch { /* ignore */ }
      }
    } catch { /* ignore */ }
  }

  // Add to search history
  function addSearchHistory(keyword: string) {
    if (!keyword.trim()) return
    // Remove duplicate
    const index = searchHistory.value.indexOf(keyword)
    if (index > -1) {
      searchHistory.value.splice(index, 1)
    }
    // Add to front
    searchHistory.value.unshift(keyword)
    // Keep at most 20 items
    if (searchHistory.value.length > 20) {
      searchHistory.value = searchHistory.value.slice(0, 20)
    }
    // Persist
    try {
      uni.setStorageSync('hxmall_search_history', JSON.stringify(searchHistory.value))
    } catch { /* ignore */ }
  }

  // Clear search history
  function clearSearchHistory() {
    searchHistory.value = []
    try {
      uni.removeStorageSync('hxmall_search_history')
    } catch { /* ignore */ }
  }

  // Set page loading
  function setPageLoading(loading: boolean) {
    isPageLoading.value = loading
  }

  // Check network and show toast if disconnected
  function checkNetwork(): boolean {
    if (!isNetworkConnected.value) {
      uni.showToast({ title: '网络连接已断开', icon: 'none' })
      return false
    }
    return true
  }

  return {
    // State
    systemInfo, networkType, isNetworkConnected, searchKeyword, searchHistory, isPageLoading,
    // Getters
    statusBarHeight, navBarHeight, totalNavHeight, windowWidth, windowHeight, isIOS, safeAreaBottom,
    // Actions
    init, addSearchHistory, clearSearchHistory, setPageLoading, checkNetwork
  }
})
