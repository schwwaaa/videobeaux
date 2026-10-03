// Run with: node --test gui/src/main/download.test.js
import { test } from 'node:test'
import assert from 'node:assert/strict'
import http from 'node:http'
import { mkdtempSync, readFileSync, existsSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { downloadToFile } from './download.js'

function serve(handler) {
  return new Promise(resolve => {
    const server = http.createServer(handler)
    server.listen(0, '127.0.0.1', () => resolve({ server, url: `http://127.0.0.1:${server.address().port}` }))
  })
}

test('downloads a file, follows a redirect, reports progress, and leaves no .part', async () => {
  const body = Buffer.alloc(300_000, 7)
  const { server, url } = await serve((req, res) => {
    if (req.url === '/go') { res.writeHead(302, { Location: '/file' }); return res.end() }
    res.writeHead(200, { 'content-length': body.length }); res.end(body)
  })
  const dir = mkdtempSync(join(tmpdir(), 'dl-'))
  const dest = join(dir, 'sub', 'f.bin')
  const seen = []
  const r = await downloadToFile(`${url}/go`, dest, { expectedSize: body.length, onProgress: p => seen.push(p) })
  assert.equal(r.size, body.length)
  assert.deepEqual(readFileSync(dest), body)
  assert.equal(existsSync(`${dest}.part`), false)
  assert.equal(seen.at(-1).received, body.length)
  assert.equal(seen.at(-1).total, body.length)
  server.close(); rmSync(dir, { recursive: true })
})

test('size mismatch fails and removes the partial file', async () => {
  const { server, url } = await serve((req, res) => { res.writeHead(200); res.end(Buffer.alloc(100)) })
  const dir = mkdtempSync(join(tmpdir(), 'dl-'))
  const dest = join(dir, 'f.bin')
  await assert.rejects(downloadToFile(url, dest, { expectedSize: 500 }), /incomplete/)
  assert.equal(existsSync(dest), false)
  assert.equal(existsSync(`${dest}.part`), false)
  server.close(); rmSync(dir, { recursive: true })
})

test('HTTP error fails cleanly', async () => {
  const { server, url } = await serve((req, res) => { res.writeHead(404); res.end() })
  const dir = mkdtempSync(join(tmpdir(), 'dl-'))
  await assert.rejects(downloadToFile(url, join(dir, 'f.bin')), /HTTP 404/)
  server.close(); rmSync(dir, { recursive: true })
})
