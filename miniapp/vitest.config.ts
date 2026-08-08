import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    include: ['src/utils/__tests__/**', 'src/api/__tests__/**', 'src/stores/__tests__/**'],
    environment: 'node',
  },
})
