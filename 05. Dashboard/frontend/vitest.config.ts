import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/setupTests.ts'],
    deps: {
      inline: ['msw', '@testing-library/react', '@testing-library/dom'],
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
    },
  },
}); 