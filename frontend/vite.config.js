import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/auth': { target: 'http://localhost:8000', changeOrigin: true },
      '/upload': { target: 'http://localhost:8000', changeOrigin: true },
      '/predictions': { target: 'http://localhost:8000', changeOrigin: true },
      '/interventions': { target: 'http://localhost:8000', changeOrigin: true },
      '/dashboard': { target: 'http://localhost:8000', changeOrigin: true },
      '/reports': { target: 'http://localhost:8000', changeOrigin: true },
      '/admin': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
