import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  // 管理后台由后端在 /admin 路径托管，构建资源必须带上 /admin/ 前缀
  base: '/admin/',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api/v1': {
        target: 'http://localhost:7000',
        changeOrigin: true,
      },
    },
  },
})
