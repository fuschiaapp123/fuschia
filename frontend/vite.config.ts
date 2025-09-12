import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // This is for local development
    port: 3000,
    host: true
  },
  preview: {
    // This is for the production preview server
    port: Number(process.env.PORT) || 4173,
    host: true
  }
})