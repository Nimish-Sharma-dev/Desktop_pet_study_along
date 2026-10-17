import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'node:path';

// Two entry pages = two Tauri windows: index.html (pet), dashboard.html (dashboard).
export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  server: { port: 1420, strictPort: true },
  build: {
    chunkSizeWarningLimit: 1500, // desktop app, assets are local
    rollupOptions: {
      input: {
        pet: resolve(__dirname, 'index.html'),
        dashboard: resolve(__dirname, 'dashboard.html'),
      },
    },
  },
});
