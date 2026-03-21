import { defineConfig } from 'vite'
import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'
import { viteStaticCopy } from 'vite-plugin-static-copy'
import path from 'path'

export default defineConfig({
  define: {
    'import.meta.env.VITE_MAPBOX_TOKEN': JSON.stringify(process.env.MAPBOX_TOKEN),
  },
  plugins: [
    react(),
    babel({ presets: [reactCompilerPreset()] }),
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
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    }
  }
})
