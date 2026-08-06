import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    include: ['src/utils/__tests__/**'],
    environment: 'node',
  },
})
