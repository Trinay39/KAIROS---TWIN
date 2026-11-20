import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

const apiProxy = {
  '/api': {
    target: 'http://127.0.0.1:8000',
    changeOrigin: true,
    rewrite: (path: string) => path.replace(/^\/api/, ''),
  },
};

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, host: true, proxy: apiProxy },
  preview: { port: 4173, host: true, proxy: apiProxy },
  build: { outDir: '../dist-frontend', emptyOutDir: true },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    globals: true,
  },
});
