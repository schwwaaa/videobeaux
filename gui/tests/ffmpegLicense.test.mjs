import test from 'node:test'
import assert from 'node:assert/strict'
import { parseFfmpegLicense } from '../src/main/toolsSetup.js'

// The macOS-arm64 build that eugeneware/ffmpeg-static b6.1.1 shipped (from license-audit.json).
const SHIPPED_6_0 = `ffmpeg version 6.0 Copyright (c) 2000-2023 the FFmpeg developers
  configuration: --prefix=/Volumes/tempdisk/sw --extra-cflags=-fno-stack-check --arch=arm64 --cc=/usr/bin/clang --enable-gpl --enable-libvmaf --enable-libbluray --enable-libopenjpeg --enable-libopus --enable-libmp3lame --enable-libx264 --enable-libx265 --enable-libvpx --enable-libwebp --enable-libass --enable-libfreetype --enable-fontconfig --enable-libtheora --enable-libvorbis --enable-libsnappy --enable-libaom --enable-libvidstab --enable-libzimg --enable-libsvtav1 --enable-libkvazaar --enable-version3 --pkg-config-flags=--static --enable-ffplay --enable-postproc --enable-nonfree --enable-neon --enable-runtime-cpudetect`

const HOMEBREW_FULL = `configuration: --prefix=/opt/homebrew/Cellar/ffmpeg-full/9.0.1_1 --enable-shared --enable-version3 --enable-gpl --enable-libx264 --enable-libx265 --enable-libass --enable-videotoolbox`
const LGPL = `configuration: --enable-shared --enable-libopus --enable-libvpx --enable-videotoolbox`

test('the previously shipped build is flagged nonfree', () => {
  const l = parseFfmpegLicense(SHIPPED_6_0)
  assert.equal(l.nonfree, true)
  assert.equal(l.flavor, 'nonfree')
  assert.equal(l.gpl, true)
  assert.ok(l.libs.includes('libx264'))
})

test('a GPL build without nonfree is shippable', () => {
  const l = parseFfmpegLicense(HOMEBREW_FULL)
  assert.deepEqual([l.nonfree, l.gpl, l.version3, l.flavor], [false, true, true, 'gpl'])
})

test('an LGPL build is recognised', () => {
  const l = parseFfmpegLicense(LGPL)
  assert.deepEqual([l.nonfree, l.gpl, l.flavor], [false, false, 'lgpl'])
})

test('--disable-nonfree style text and --enable-nonfree-ish prefixes do not trip the check', () => {
  const l = parseFfmpegLicense('configuration: --enable-gpl --disable-nonfree --enable-libx264')
  assert.equal(l.nonfree, false)
})

import { installFfmpeg } from '../src/main/toolsSetup.js'
import { mkdtempSync, writeFileSync, chmodSync, existsSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { gzipSync } from 'node:zlib'

// A stand-in "ffmpeg" that prints a canned -version/-buildconf and exits 0.
function fakeBinaryGz(text) {
  const script = `#!/bin/sh\ncat <<'EOF'\n${text}\nEOF\n`
  return gzipSync(Buffer.from(script))
}
const fakeDownload = (gzByUrl) => async (url, dest) => { writeFileSync(dest, gzByUrl(url)) }
const runtimeFor = (tag) => ({
  tag, urlBase: 'https://example.invalid',
  assets: { darwin_arm64: { ffmpeg: 'ffmpeg.gz', ffprobe: 'ffprobe.gz' }, darwin_x64: { ffmpeg: 'ffmpeg.gz', ffprobe: 'ffprobe.gz' } }
})

test('installFfmpeg refuses a nonfree build and removes it', { skip: process.platform === 'win32' }, async () => {
  const dir = mkdtempSync(join(tmpdir(), 'vb-ff-'))
  await assert.rejects(
    installFfmpeg({ targetDir: dir, runtime: runtimeFor('t'), platform: process.platform, download: fakeDownload(() => fakeBinaryGz(SHIPPED_6_0)) }),
    /nonfree/
  )
  assert.equal(existsSync(join(dir, 'ffmpeg')), false)
})

test('installFfmpeg accepts a GPL build without nonfree', { skip: process.platform === 'win32' }, async () => {
  const dir = mkdtempSync(join(tmpdir(), 'vb-ff-'))
  const r = await installFfmpeg({ targetDir: dir, runtime: runtimeFor('t'), platform: process.platform, download: fakeDownload(() => fakeBinaryGz(HOMEBREW_FULL)) })
  assert.equal(r.license.flavor, 'gpl')
  assert.equal(existsSync(join(dir, 'ffmpeg')), true)
})

test('allowFallback uses devFallback only when our release cannot be downloaded', { skip: process.platform === 'win32' }, async () => {
  const dir = mkdtempSync(join(tmpdir(), 'vb-ff-'))
  const runtime = { ...runtimeFor('ours'), devFallback: runtimeFor('legacy') }
  const download = async (url, dest) => {
    if (url.includes('/ours/')) throw new Error('404')
    writeFileSync(dest, fakeBinaryGz(SHIPPED_6_0))
  }
  await assert.rejects(installFfmpeg({ targetDir: dir, runtime, platform: process.platform, download }), /404/)   // installer path: no fallback
  const r = await installFfmpeg({ targetDir: dir, runtime, platform: process.platform, download, allowFallback: true })
  assert.equal(r.fallback, true)
})

import { parseNames, evaluateFeatures, inspectFfmpeg } from '../src/main/toolsSetup.js'

const ENCODERS = `Encoders:
 V..... = Video
 ------
 V....D libx264              libx264 H.264 (codec h264)
 V....D libsvtav1            SVT-AV1(Scalable Video Technology for AV1) encoder (codec av1)
 A....D aac                  AAC (Advanced Audio Coding)`
const FILTERS = `Filters:
  T.. = Timeline support
 ------
 T.C drawtext          V->V       Draw text on top of video frames using libfreetype library.
 TS zscale             V->V       Apply resizing, colorspace and bit depth conversion.`

test('parseNames reads codec tables, 2- and 3-char filter flag columns, and ignores the legend', () => {
  assert.deepEqual([...parseNames(ENCODERS)].sort(), ['aac', 'libsvtav1', 'libx264'])
  assert.deepEqual([...parseNames(FILTERS)].sort(), ['drawtext', 'zscale'])
})

test('evaluateFeatures: any-of names, kinds are kept apart', () => {
  const feats = [
    { id: 'av1_enc', kind: 'encoder', any: ['libsvtav1', 'libaom-av1'], required: false },
    { id: 'av1_dec', kind: 'decoder', any: ['libdav1d'], required: false },
    { id: 'text', kind: 'filter', any: ['drawtext'], required: true },
    { id: 'libx264-as-filter', kind: 'filter', any: ['libx264'], required: true }
  ]
  const r = evaluateFeatures(feats, { encoders: parseNames(ENCODERS), decoders: new Set(), filters: parseNames(FILTERS) })
  assert.deepEqual(r.map(f => [f.id, f.ok]), [['av1_enc', true], ['av1_dec', false], ['text', true], ['libx264-as-filter', false]])
})

const BUNDLED = new URL('../resources/ffmpeg/ffmpeg', import.meta.url).pathname
test('the bundled ffmpeg (when present) meets every required feature and is not nonfree', { skip: !existsSync(BUNDLED) }, async () => {
  const reqs = JSON.parse((await import('node:fs')).readFileSync(new URL('../../videobeaux/assets/ffmpeg_requirements.json', import.meta.url), 'utf8')).features
  const r = await inspectFfmpeg(BUNDLED, reqs)
  assert.equal(r.ok, true)
  assert.deepEqual(r.missing, [])
  assert.notEqual(r.license.flavor, 'nonfree')
})

// ── bundling a locally built ffmpeg (npm run dist before our release is published) ───────────────────────────────
import { adoptLocalFfmpeg, findLocalFfmpegDir } from '../src/main/toolsSetup.js'

function fakeFfmpegDir(configLine, { start = true } = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'vb-local-ff-'))
  const body = start
    ? `#!/bin/sh\necho "ffmpeg version 7.1.1 Copyright"\necho "  configuration: ${configLine}"\n`
    : '#!/bin/sh\nexit 1\n'
  for (const t of ['ffmpeg', 'ffprobe']) {
    writeFileSync(join(dir, t), body)
    chmodSync(join(dir, t), 0o755)
  }
  return dir
}

test('a locally built GPL ffmpeg is copied into the bundle', { skip: process.platform === 'win32' }, async () => {
  const src = fakeFfmpegDir('--enable-gpl --enable-libx264 --enable-libsvtav1')
  const dst = mkdtempSync(join(tmpdir(), 'vb-bundle-'))
  const r = await adoptLocalFfmpeg({ sourceDir: src, targetDir: join(dst, 'ffmpeg'), platform: process.platform })
  assert.equal(r.license.flavor, 'gpl')
  assert.equal(existsSync(join(dst, 'ffmpeg', 'ffmpeg')), true)
  assert.equal(existsSync(join(dst, 'ffmpeg', 'ffprobe')), true)
})

test('a nonfree or non-starting local ffmpeg is refused and nothing is copied', { skip: process.platform === 'win32' }, async () => {
  const dst = mkdtempSync(join(tmpdir(), 'vb-bundle-'))
  await assert.rejects(
    adoptLocalFfmpeg({ sourceDir: fakeFfmpegDir('--enable-gpl --enable-nonfree'), targetDir: join(dst, 'a'), platform: process.platform }),
    /nonfree/)
  await assert.rejects(
    adoptLocalFfmpeg({ sourceDir: fakeFfmpegDir('', { start: false }), targetDir: join(dst, 'b'), platform: process.platform }),
    /won't start/)
  assert.equal(existsSync(join(dst, 'a', 'ffmpeg')), false)
  assert.equal(existsSync(join(dst, 'b', 'ffmpeg')), false)
})

test('findLocalFfmpegDir returns the first candidate that has both binaries', { skip: process.platform === 'win32' }, () => {
  const good = fakeFfmpegDir('--enable-gpl')
  const empty = mkdtempSync(join(tmpdir(), 'vb-empty-'))
  assert.equal(findLocalFfmpegDir([undefined, '/definitely/not/here', empty, good]), good)
  assert.equal(findLocalFfmpegDir([empty, null]), null)
})
