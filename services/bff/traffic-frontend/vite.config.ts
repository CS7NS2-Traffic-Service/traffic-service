import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteStaticCopy } from 'vite-plugin-static-copy'
import path from 'path'

export default defineConfig({
  plugins: [
    react(),
    // babel({ presets: [reactCompilerPreset()] }),
    viteStaticCopy({
      targets: [{
        src: 'node_modules/@fontsource-variable/inter/files/*',
        dest: 'assets/files'
      }]
    })
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            return 'vendor'
          }
        },
      },
    },
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    }
  }
})
