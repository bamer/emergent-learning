import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    react(),
    visualizer({
      filename: 'dist/stats.html',
      open: false,
      gzipSize: true,
      brotliSize: true,
    })
  ],
  server: {
    port: 3001,
    proxy: {
      '/api': {
        target: 'http://localhost:8888',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8888',
        ws: true,
        secure: false,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Split vendor chunks
          'react-vendor': ['react', 'react-dom'],
          'three-vendor': ['three', '@react-three/fiber', '@react-three/drei', '@react-three/postprocessing'],
          'ui-vendor': ['framer-motion', 'lucide-react'],
          'chart-vendor': ['d3', 'recharts'],
          'util-vendor': ['date-fns', 'zustand', 'react-markdown']
        }
      }
    },
    // Increase chunk size warnings limit since we've optimized successfully
    chunkSizeWarningLimit: 500,
    // Enable CSS code splitting
    cssCodeSplit: true,
    // Enable build report
    reportCompressedSize: true,
    // Enable minification
    minify: 'esbuild',
  }
})
