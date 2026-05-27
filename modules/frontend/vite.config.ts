import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    // Polling required for Docker on Windows - inotify events don't work
    // across the WSL2 filesystem boundary
    watch: {
      usePolling: true,
      interval: 300,
    },
    proxy: {
      '/v1': { target: 'http://api:8000', changeOrigin: true },
      '/ws': { target: 'ws://api:8000', ws: true },
    },
  },
  resolve: {
    alias: { '@': '/src' },
  },
})