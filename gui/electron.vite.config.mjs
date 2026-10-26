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
    // Small assets (every Look thumbnail is under 8 KB) are embedded as data URIs. Referencing them as separate files made the
    // hover previews depend on a file path that failed on a fresh Windows install; embedded images need no path at all.
    build: { assetsInlineLimit: 8192 }
  }
})
