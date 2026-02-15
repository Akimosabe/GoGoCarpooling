import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
const isProd = process.env.NODE_ENV === 'production'
export default defineConfig({
  base: isProd ? '/static/' : '/',
  plugins: [
    react(),
    tailwindcss(),
    // В проде статика по /static/; в index.html правим только public-ассеты (favicon, preload)
    isProd && {
      name: 'html-static-paths',
      transformIndexHtml(html: string) {
        return html
          .replace('href="/vite.svg"', 'href="/static/vite.svg"')
          .replace('href="/hero-road.jpg"', 'href="/static/hero-road.jpg"')
      },
    },
  ].filter(Boolean),
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/media': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
