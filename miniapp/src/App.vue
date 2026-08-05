<script setup lang="ts">
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app'

onLaunch(() => {
  console.log('[App] onLaunch - App launched')
  // Try to restore login state from storage
  try {
    const token = uni.getStorageSync('hxmall_token')
    if (token) {
      console.log('[App] Token found in storage, restoring login state')
      // Token exists — app can proceed with authenticated state
      // The actual user info restoration will be handled by the user store
    } else {
      console.log('[App] No token found, starting in guest mode')
    }
  } catch (err) {
    console.error('[App] Failed to read token from storage:', err)
  }

  // Initialize app-level settings
  try {
    // Get system info for adaptive layout
    const systemInfo = uni.getSystemInfoSync()
    console.log('[App] System info:', {
      platform: systemInfo.platform,
      version: systemInfo.version,
      screenWidth: systemInfo.screenWidth,
      screenHeight: systemInfo.screenHeight,
      statusBarHeight: systemInfo.statusBarHeight
    })
  } catch (err) {
    console.error('[App] Failed to get system info:', err)
  }
})

onShow(() => {
  console.log('[App] onShow - App shown')
})

onHide(() => {
  console.log('[App] onHide - App hidden')
})
</script>

<style lang="scss">
/* Import global styles */
@import '@/styles/global.scss';

/* App-level styles */
page {
  background-color: #FFF8F0;
  font-family: -apple-system, "SF Pro Rounded", "PingFang SC", "Helvetica Neue", sans-serif;
  color: #4a3728;
  font-size: 28rpx;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
