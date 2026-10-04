// Run with: node --test gui/src/main/toolsSetup.test.js   (needs network, ~40 MB download)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, mkdtempSync, readFileSync, readdirSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { ffmpegBinaryPath, inspectFfmpeg, installFfmpeg } from './toolsSetup.js'

const here = dirname(fileURLToPath(import.meta.url))
const runtime = JSON.parse(readFileSync(join(here, '../../ffmpeg-runtime.json'), 'utf8'))

test('downloads ffmpeg + ffprobe, they run, and have the filters Videobeaux needs', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'vb-ff-'))
  const phases = []
  await installFfmpeg({ targetDir: dir, runtime, onProgress: p => { if (!phases.includes(p.phase)) phases.push(p.phase) } })
  assert.deepEqual(phases, ['ffmpeg-download', 'ffmpeg-unpack'])
  for (const t of ['ffmpeg', 'ffprobe']) assert.ok(existsSync(ffmpegBinaryPath(dir, t)))
  assert.deepEqual(readdirSync(dir).sort(), ['ffmpeg', 'ffprobe'])      // no .part / .gz leftovers
  const info = await inspectFfmpeg(ffmpegBinaryPath(dir))
  assert.equal(info.ok, true)
  assert.equal(info.capable, true, `missing filters: ${info.missing}`)   // zscale, ass, drawtext
  rmSync(dir, { recursive: true })
}, { timeout: 300_000 })

test('a failed download leaves nothing half-installed', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'vb-ff-'))
  await assert.rejects(installFfmpeg({ targetDir: dir, runtime, download: async () => { throw new Error('offline') } }), /offline/)
  assert.deepEqual(readdirSync(dir), [])
  rmSync(dir, { recursive: true })
})

test('inspectFfmpeg reports a missing binary instead of throwing', async () => {
  const r = await inspectFfmpeg('/definitely/not/ffmpeg')
  assert.equal(r.ok, false)
})
