// Serves the real renderer (gui/src/renderer) in a plain browser with a stubbed Electron bridge (stub.js), so the website's
// screenshots can be retaken without packaging the app. Used by shots.sh — not part of the app or the site.
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import fs from 'node:fs'
import os from 'node:os'

const here = path.dirname(fileURLToPath(import.meta.url))
const guiDir = path.resolve(here, '../../gui')
const require = createRequire(path.join(guiDir, 'package.json'))
const { defineConfig } = require('vite')
const react = require('@vitejs/plugin-react')
const reactPlugin = react.default || react

export default defineConfig({
  root: path.join(guiDir, 'src/renderer'),
  cacheDir: path.join(os.tmpdir(), 'vb-site-harness-vite'),
  plugins: [reactPlugin(), {
    name: 'vb-stub',
    configureServer(server) {
      const send = (res, file, type) => { res.setHeader('content-type', type); res.end(fs.readFileSync(file)) }
      server.middlewares.use('/__programs.json', (q, r) => send(r, path.join(here, 'programs.json'), 'application/json'))
      // font files for the font picker (harness only): /__file?p=<abs path>, fonts only
      server.middlewares.use('/__file', (q, r) => {
        try {
          const f = new URL(q.url, 'http://x').searchParams.get('p')
          if (!/\.(ttf|otf)$/i.test(f)) throw new Error('no')
          r.setHeader('content-type', 'font/ttf'); r.end(fs.readFileSync(f))
        } catch { r.statusCode = 404; r.end('') }
      })
      server.middlewares.use('/__fonts.json', (q, r) => send(r, path.join(here, 'fonts.json'), 'application/json'))
      server.middlewares.use('/__stub.js', (q, r) => send(r, path.join(here, 'stub.js'), 'text/javascript'))
      // the Examples library (harness only): examples/index.json and examples/presets/*.json, read-only
      const examplesDir = path.join(here, '../../examples')
      server.middlewares.use('/__examples', (q, r) => {
        try {
          const f = path.join(examplesDir, decodeURIComponent(q.url.split('?')[0]))
          if (!f.startsWith(examplesDir + path.sep) || !f.endsWith('.json')) throw new Error('no')
          send(r, f, 'application/json')
        } catch { r.statusCode = 404; r.end('') }
      })
      server.middlewares.use('/__ws', (q, r) => {
        try { send(r, path.join(here, 'ws', path.basename(q.url.split('?')[0])), 'application/json') } catch { r.statusCode = 404; r.end('') }
      })
    },
    transformIndexHtml: () => [{ tag: 'script', attrs: { src: '/__stub.js' }, injectTo: 'head-prepend' }]
  }],
  server: { port: 5199, strictPort: true, fs: { strict: false } }
})
