import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  
  resolve: {
    alias: {
      '@': path.resolve(new URL('.', import.meta.url).pathname, './src')
    }
  },
  
  // Production preview configuration (for Railway)
  preview: {
    host: '0.0.0.0',
    port: parseInt(process.env.PORT || '3000', 10),
    strictPort: false, // Allow fallback if port is taken
    cors: true
  },
  
  // Development server configuration
  server: {
    host: '0.0.0.0',
    port: process.env.PORT ? parseInt(process.env.PORT, 10) : 5173,
    strictPort: false, // Allow fallback to other ports in dev
    cors: true,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    },
    hmr: {
      port: process.env.PORT ? parseInt(process.env.PORT, 10) + 1 : 5174
    }
  },
  
  // Build configuration
  build: {
    outDir: 'dist',
    sourcemap: false, // Disable source maps in production for smaller bundle
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom']
        }
      }
    }
  },
  
  // Environment variables that will be available to the client
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '0.1.0')
  }
})