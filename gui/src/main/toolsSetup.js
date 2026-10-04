import { chmodSync, createReadStream, createWriteStream, existsSync, mkdirSync, renameSync, rmSync } from 'fs'
import { join } from 'path'
import { tmpdir } from 'os'
import { spawn } from 'child_process'
import { pipeline } from 'stream/promises'
import { createGunzip } from 'zlib'
import { downloadToFile } from './download.js'

/**
 * Downloads static ffmpeg + ffprobe (see gui/ffmpeg-runtime.json) into
 * `targetDir`. Used by the in-app dev setup (<repo>/.tools/ffmpeg) and by the
 * installer build (gui/resources/ffmpeg), so both ship the same, fully
 * featured build. Pure Node with an injectable downloader, testable offline.
 */

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

/** Does this ffmpeg run, and does it have the filters Videobeaux's programs rely on? */
export async function inspectFfmpeg(bin) {
  const v = await runCapture(bin, ['-version'])
  if (v.code !== 0) return { ok: false, capable: false, detail: v.out.split('\n')[0] }
  const f = await runCapture(bin, ['-hide_banner', '-filters'])
  const have = new Set(f.out.split('\n').map(l => l.trim().split(/\s+/)[1]).filter(Boolean))
  const missing = ['zscale', 'ass', 'drawtext'].filter(n => !have.has(n))
  return { ok: true, capable: missing.length === 0, missing, detail: v.out.split('\n')[0] }
}

export async function installFfmpeg({
  targetDir, runtime, onProgress = () => {},
  platform = process.platform, arch = process.arch,
  download = downloadToFile
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
  const check = await runCapture(ffmpegBinaryPath(targetDir, 'ffmpeg', platform), ['-version'])
  if (check.code !== 0) throw new Error(`The downloaded ffmpeg wouldn't start: ${check.out.split('\n')[0]}`)
  return { dir: targetDir }
}
