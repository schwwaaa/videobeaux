// Run with: node --test gui/src/main/pythonSetup.test.js
// Hits the network (python-build-standalone on GitHub + PyPI) — takes a minute or two.
import { test, before } from 'node:test'
import assert from 'node:assert/strict'
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, writeFileSync, chmodSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'
import { downloadToFile } from './download.js'
import { findVenvPython, installPython } from './pythonSetup.js'

const here = dirname(fileURLToPath(import.meta.url))
const runtime = JSON.parse(readFileSync(join(here, '../../python-runtime.json'), 'utf8'))

let cachedTarball = null   // downloaded once by the first test, reused by the rest
const caching = async (url, dest, opts) => {
  const r = await downloadToFile(url, dest, opts)
  cachedTarball = join(tmpdir(), `vb-test-python-cache-${process.pid}.tar.gz`)
  copyFileSync(dest, cachedTarball)
  return r
}
const fromCache = async (url, dest, opts) => {
  copyFileSync(cachedTarball, dest)
  opts?.onProgress?.({ received: 1, total: 1 })
  return { size: 1 }
}

function fakeRepo(requirements) {
  const root = mkdtempSync(join(tmpdir(), 'vb-repo-'))
  writeFileSync(join(root, 'requirements.txt'), requirements)
  return root
}

test('fresh machine: downloads Python, installs requirements (skipping the -e line), verifies', async () => {
  const root = fakeRepo('tqdm==4.67.1\n-e ./videobeaux\n')
  const phases = []
  const r = await installPython({
    vbRoot: root, runtime, verifyImports: 'import tqdm', download: caching,
    onProgress: p => { if (!phases.includes(p.phase)) phases.push(p.phase) }
  })
  assert.equal(r.ok, true, r.error)
  assert.ok(findVenvPython(join(root, 'venv')))
  assert.deepEqual(phases, ['python-download', 'python-unpack', 'pip', 'verify', 'done'])
  const out = spawnSync(r.python, ['-c', 'import tqdm,sys; print(sys.version_info[:2])'], { encoding: 'utf8' })
  assert.match(out.stdout, /\(3, 12\)/)
  // no leftovers in the repo besides venv + requirements
  assert.deepEqual(readdirSync(root).sort(), ['requirements.txt', 'venv'])

  // second run is idempotent and does NOT download again
  const again = []
  const r2 = await installPython({ vbRoot: root, runtime, verifyImports: 'import tqdm', download: fromCache,
    onProgress: p => again.push(p.phase) })
  assert.equal(r2.ok, true, r2.error)
  assert.ok(!again.includes('python-download'))
}, { timeout: 600_000 })

test('failed package install removes the half-built venv it created', async () => {
  const root = fakeRepo('this-package-does-not-exist-videobeaux-xyz==1.0\n')
  const r = await installPython({ vbRoot: root, runtime, download: fromCache })
  assert.equal(r.ok, false)
  assert.match(r.error, /Installing packages failed/)
  assert.equal(existsSync(join(root, 'venv')), false)
}, { timeout: 600_000 })

test('"fresh" moves a broken venv aside instead of deleting it', async () => {
  const root = fakeRepo('tqdm==4.67.1\n')
  const bin = join(root, 'venv', 'bin')
  mkdirSync(bin, { recursive: true })
  writeFileSync(join(bin, 'python3'), '#!/bin/sh\nexit 1\n')
  chmodSync(join(bin, 'python3'), 0o755)
  const r = await installPython({ vbRoot: root, runtime, fresh: true, verifyImports: 'import tqdm', download: fromCache })
  assert.equal(r.ok, true, r.error)
  const aside = readdirSync(root).filter(n => n.startsWith('venv.old-'))
  assert.equal(aside.length, 1)
  assert.ok(existsSync(join(root, aside[0], 'bin', 'python3')))   // the old one is still there
}, { timeout: 600_000 })

test('a second setup started while one is running is rejected', async () => {
  const root = fakeRepo('tqdm==4.67.1\n')
  let release
  const gate = new Promise(res => { release = res })
  const slow = async (url, dest) => { await gate; copyFileSync(cachedTarball, dest); return { size: 1 } }
  const first = installPython({ vbRoot: root, runtime, verifyImports: 'import tqdm', download: slow })
  await new Promise(r => setTimeout(r, 50))
  const second = await installPython({ vbRoot: root, runtime, download: slow })
  assert.equal(second.ok, false)
  assert.match(second.error, /already running/)
  release()
  const done = await first
  assert.equal(done.ok, true, done.error)
}, { timeout: 600_000 })
