import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()]
  },
  preload: {
    plugins: [externalizeDepsPlugin()]
  },
  renderer: {
    plugins: [react()],
    // Look thumbnails are ~3 KB each; keep them as files instead of base64 inside the JS bundle.
    build: { assetsInlineLimit: 0 }
  }
})
