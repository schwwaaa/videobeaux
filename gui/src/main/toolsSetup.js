import { chmodSync, copyFileSync, createReadStream, createWriteStream, existsSync, mkdirSync, renameSync, rmSync } from 'fs'
import { join, resolve } from 'path'
import { tmpdir } from 'os'
import { spawn } from 'child_process'
import { pipeline } from 'stream/promises'
import { createGunzip } from 'zlib'
import { createHash } from 'crypto'
import { downloadToFile } from './download.js'

/**
 * Downloads static ffmpeg + ffprobe (see gui/ffmpeg-runtime.json) into
 * `targetDir`. Used by the in-app dev setup (<repo>/.tools/ffmpeg) and by the
 * installer build (gui/resources/ffmpeg), so both ship the same, fully
 * featured build. Pure Node with an injectable downloader, testable offline.
 */

function sha256File(path) {
  return new Promise((resolve, reject) => {
    const h = createHash('sha256')
    createReadStream(path).on('data', d => h.update(d)).on('end', () => resolve(h.digest('hex'))).on('error', reject)
  })
}

export function ffmpegBinaryPath(dir, tool = 'ffmpeg', platform = process.platform) {
  return join(dir, platform === 'win32' ? `${tool}.exe` : tool)
}

export function runtimeKey(platform = process.platform, arch = process.arch) {
  return `${platform}_${arch === 'arm64' ? 'arm64' : 'x64'}`
}

/** Run `<bin> <args>`; resolve { code, out } (never rejects). */
export function runCapture(bin, args) {
  return new Promise(resolve => {
    let out = ''
    let proc
    try { proc = spawn(bin, args, { windowsHide: true }) } catch (e) { return resolve({ code: -1, out: e.message }) }
    proc.stdout?.on('data', d => { out += d.toString('utf8') })
    proc.stderr?.on('data', d => { out += d.toString('utf8') })
    proc.on('error', e => resolve({ code: -1, out: e.message }))
    proc.on('close', code => resolve({ code, out }))
  })
}

/**
 * What licence flavor is this ffmpeg? Parsed from `ffmpeg -version` / `-buildconf` output.
 *   nonfree  → cannot legally be redistributed (FFmpeg's own licensing doc)
 *   gpl      → GPL build: shippable with the licence text, notices and a source offer
 *   (neither) → LGPL build
 */
export function parseFfmpegLicense(text) {
  const flags = new Set((text.match(/--[a-z0-9][a-z0-9-]*(?:=\S*)?/gi) || []).map(f => f.toLowerCase()))
  const has = f => flags.has(f)
  const libs = [...flags].filter(f => f.startsWith('--enable-lib')).map(f => f.slice('--enable-'.length)).sort()
  return {
    nonfree: has('--enable-nonfree'),
    gpl: has('--enable-gpl'),
    version3: has('--enable-version3'),
    libs,
    flavor: has('--enable-nonfree') ? 'nonfree' : has('--enable-gpl') ? 'gpl' : 'lgpl'
  }
}

/** Run `<bin> -buildconf` (falling back to -version) and parse its licence flavor. */
export async function ffmpegLicense(bin) {
  let r = await runCapture(bin, ['-hide_banner', '-buildconf'])
  if (r.code !== 0 || !/--/.test(r.out)) r = await runCapture(bin, ['-version'])
  return r.code === 0 ? parseFfmpegLicense(r.out) : null
}

// Used when videobeaux/assets/ffmpeg_requirements.json can't be read (the file is the real source of truth).
const FALLBACK_FEATURES = [
  { id: 'text', label: 'Text overlays (drawtext)', kind: 'filter', any: ['drawtext'], required: true },
  { id: 'subtitles', label: 'Caption burning (libass)', kind: 'filter', any: ['ass', 'subtitles'], required: true },
  { id: 'hdr', label: 'HDR tone mapping (zscale)', kind: 'filter', any: ['zscale'], required: true }
]

/** Second column of `ffmpeg -encoders|-decoders|-filters` (codecs have 6 flag chars, filters 2-3; legend lines have "="). */
export function parseNames(listing = '') {
  const names = new Set()
  for (const line of listing.split('\n')) {
    const p = line.trim().split(/\s+/)
    if (p.length >= 3 && p[1] !== '=' && /^[A-Z.]{2,6}$/.test(p[0])) names.add(p[1])
  }
  return names
}

/** Pure: which of the required/optional features does a build have? */
export function evaluateFeatures(features, { encoders, decoders, filters }) {
  const pool = { encoder: encoders, decoder: decoders, filter: filters }
  return features.map(f => ({ ...f, ok: f.any.some(n => pool[f.kind].has(n)) }))
}

/** Does this ffmpeg run, and does it have what Videobeaux's programs rely on (see ffmpeg_requirements.json)? */
export async function inspectFfmpeg(bin, features = FALLBACK_FEATURES) {
  const v = await runCapture(bin, ['-version'])
  if (v.code !== 0) return { ok: false, capable: false, detail: v.out.split('\n')[0] }
  const [f, e, d] = await Promise.all(['-filters', '-encoders', '-decoders'].map(a => runCapture(bin, ['-hide_banner', a])))
  const evaluated = evaluateFeatures(features, { filters: parseNames(f.out), encoders: parseNames(e.out), decoders: parseNames(d.out) })
  const missing = evaluated.filter(x => x.required && !x.ok).map(x => x.label)
  const optionalMissing = evaluated.filter(x => !x.required && !x.ok).map(x => x.label)
  const license = parseFfmpegLicense(v.out)
  return {
    ok: true, capable: missing.length === 0, missing, optionalMissing, features: evaluated,
    detail: v.out.split('\n')[0], license
  }
}

/**
 * Install ffmpeg + ffprobe into `targetDir`. A binary built with --enable-nonfree is never accepted (it cannot be
 * redistributed) — unless `allowNonfree` is set, which only the in-app *dev* setup does. With `allowFallback`, if
 * our own release can't be downloaded yet, `runtime.devFallback` (third-party static builds) is used for
 * development only; the installer build never passes it, so a release can't ship that binary.
 */
export async function installFfmpeg(opts) {
  const { runtime, allowFallback = false, onProgress = () => {} } = opts
  try {
    return await installFfmpegFrom(opts)
  } catch (e) {
    if (!allowFallback || e.nonfree || !runtime.devFallback) throw e
    onProgress({ phase: 'ffmpeg-fallback', message: 'Our ffmpeg build isn\'t published yet — using a development-only build.' })
    const r = await installFfmpegFrom({ ...opts, runtime: { ...runtime.devFallback }, allowNonfree: true })
    return { ...r, fallback: true }
  }
}

async function installFfmpegFrom({
  targetDir, runtime, onProgress = () => {},
  platform = process.platform, arch = process.arch,
  download = downloadToFile, allowNonfree = false
}) {
  const assets = runtime.assets[runtimeKey(platform, arch)]
  if (!assets) throw new Error(`No ffmpeg build is available for this platform (${runtimeKey(platform, arch)}).`)
  mkdirSync(targetDir, { recursive: true })
  const tools = ['ffmpeg', 'ffprobe']
  for (let i = 0; i < tools.length; i++) {
    const tool = tools[i]
    const label = `Downloading ${tool}…`
    const gz = join(tmpdir(), `videobeaux-${tool}-${Date.now()}.gz`)
    const dest = ffmpegBinaryPath(targetDir, tool, platform)
    const part = `${dest}.part`
    try {
      onProgress({ phase: 'ffmpeg-download', message: label, received: 0, total: 0, index: i, count: tools.length })
      await download(`${runtime.urlBase}/${runtime.tag}/${assets[tool]}`, gz, {
        onProgress: ({ received, total }) =>
          onProgress({ phase: 'ffmpeg-download', message: label, received, total, index: i, count: tools.length })
      })
      const expected = runtime.sha256?.[runtimeKey(platform, arch)]?.[tool]
      if (expected) {
        const got = await sha256File(gz)
        if (got !== expected.toLowerCase()) throw new Error(`${tool} download failed its integrity check (sha256 mismatch).`)
      }
      onProgress({ phase: 'ffmpeg-unpack', message: `Unpacking ${tool}…` })
      await pipeline(createReadStream(gz), createGunzip(), createWriteStream(part))
      if (platform !== 'win32') chmodSync(part, 0o755)
      if (existsSync(dest)) rmSync(dest, { force: true })
      renameSync(part, dest)
    } finally {
      rmSync(gz, { force: true })
      rmSync(part, { force: true })
    }
  }
  const ffmpegBin = ffmpegBinaryPath(targetDir, 'ffmpeg', platform)
  const check = await runCapture(ffmpegBin, ['-version'])
  if (check.code !== 0) throw new Error(`The downloaded ffmpeg wouldn't start: ${check.out.split('\n')[0]}`)
  const license = await ffmpegLicense(ffmpegBin)
  if (license?.nonfree && !allowNonfree) {
    for (const tool of tools) rmSync(ffmpegBinaryPath(targetDir, tool, platform), { force: true })
    const err = new Error(
      'That ffmpeg was built with --enable-nonfree, which makes it non-redistributable, so it was removed. ' +
      'Point gui/ffmpeg-runtime.json at a build configured without --enable-nonfree (see tools/ffmpeg-build/).')
    err.nonfree = true
    throw err
  }
  return { dir: targetDir, license }
}

/**
 * First existing directory (holding ffmpeg + ffprobe for `platform`) among the candidates, in order.
 * Used by the installer build so a developer can bundle an ffmpeg they built themselves (tools/ffmpeg-build/).
 */
export function findLocalFfmpegDir(candidates, platform = process.platform) {
  for (const c of candidates) {
    if (!c) continue
    const dir = resolve(c)
    if (existsSync(ffmpegBinaryPath(dir, 'ffmpeg', platform)) && existsSync(ffmpegBinaryPath(dir, 'ffprobe', platform))) return dir
  }
  return null
}

/**
 * Copy a locally built ffmpeg + ffprobe into `targetDir` for bundling. It must start, and must not be an
 * --enable-nonfree build (not redistributable) — the same rule the downloaded build is held to.
 */
export async function adoptLocalFfmpeg({ sourceDir, targetDir, platform = process.platform }) {
  const tools = ['ffmpeg', 'ffprobe']
  for (const t of tools) {
    if (!existsSync(ffmpegBinaryPath(sourceDir, t, platform))) throw new Error(`${t} not found in ${sourceDir}`)
  }
  const bin = ffmpegBinaryPath(sourceDir, 'ffmpeg', platform)
  const check = await runCapture(bin, ['-version'])
  if (check.code !== 0) throw new Error(`The ffmpeg in ${sourceDir} won't start: ${check.out.split('\n')[0]}`)
  const license = await ffmpegLicense(bin)
  if (license?.nonfree) {
    throw new Error(`The ffmpeg in ${sourceDir} was built with --enable-nonfree and cannot be bundled in a redistributable installer. ` +
      'Use the build from tools/ffmpeg-build/ (npm run ffmpeg:local).')
  }
  mkdirSync(targetDir, { recursive: true })
  for (const t of tools) {
    const dest = ffmpegBinaryPath(targetDir, t, platform)
    copyFileSync(ffmpegBinaryPath(sourceDir, t, platform), dest)
    if (platform !== 'win32') chmodSync(dest, 0o755)
  }
  return { dir: targetDir, license, version: check.out.split('\n')[0] }
}
