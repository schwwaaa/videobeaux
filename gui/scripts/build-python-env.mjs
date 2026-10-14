#!/usr/bin/env node
// Stages everything electron-builder's `extraResources` needs to produce a
// self-contained installer: a real (unfrozen) CPython interpreter with the
// app's dependencies pre-installed, static ffmpeg/ffprobe binaries, and a
// copy of the videobeaux Python package — all under gui/resources/.
//
// Run before `electron-builder` (wired as a pre-step in package.json's
// `dist` script). Safe to re-run — it starts by wiping gui/resources/.
//
// Usage: node scripts/build-python-env.mjs [--platform=darwin|win32]
// Defaults to the current platform. Only the current platform's Python
// build can actually be pip-installed here (pip installs compiled wheels
// for the *running* interpreter's platform) — cross-building for another
// OS needs to run this script on a machine/runner of that OS.

import { mkdirSync, rmSync, readdirSync, statSync, copyFileSync, createWriteStream, readFileSync, writeFileSync, existsSync, mkdtempSync } from 'fs'
import { tmpdir } from 'os'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import { spawnSync } from 'child_process'
import { pipeline } from 'stream/promises'
import { installFfmpeg, ffmpegBinaryPath, ffmpegLicense, adoptLocalFfmpeg, findLocalFfmpegDir } from '../src/main/toolsSetup.js'

const __dirname = dirname(fileURLToPath(import.meta.url))
const GUI_ROOT = join(__dirname, '..')
const REPO_ROOT = join(GUI_ROOT, '..')
const RESOURCES = join(GUI_ROOT, 'resources')

const platformArg = process.argv.find(a => a.startsWith('--platform='))
const targetPlatform = platformArg ? platformArg.split('=')[1] : process.platform

// ── python-build-standalone: pinned release + per-platform asset names ──────
// Lives in gui/python-runtime.json (shared with the in-app dev setup in
// src/main/pythonSetup.js) so the installer and a source checkout always use
// the same interpreter. Pinned rather than "latest" so a build today and a
// build in six months produce the same Python.
const RUNTIME = JSON.parse(readFileSync(join(GUI_ROOT, 'python-runtime.json'), 'utf8'))
const PBS_RELEASE = RUNTIME.release
const PYTHON_VERSION = RUNTIME.version
const PBS_ASSETS = RUNTIME.assets

function pbsAssetKey() {
  const arch = process.arch === 'arm64' ? 'arm64' : 'x64'
  return `${targetPlatform}_${arch}`
}

function run(cmd, args, opts = {}) {
  console.log(`+ ${cmd} ${args.join(' ')}`)
  const result = spawnSync(cmd, args, { stdio: 'inherit', ...opts })
  if (result.status !== 0) {
    throw new Error(`Command failed (${result.status}): ${cmd} ${args.join(' ')}`)
  }
}

async function download(url, destPath) {
  console.log(`Downloading ${url}`)
  const res = await fetch(url)
  if (!res.ok || !res.body) throw new Error(`Download failed (HTTP ${res.status}): ${url}`)
  mkdirSync(dirname(destPath), { recursive: true })
  await pipeline(res.body, createWriteStream(destPath))
}

function rmrf(p) {
  rmSync(p, { recursive: true, force: true })
}

function copyDirFiltered(src, dest, skipDirs) {
  mkdirSync(dest, { recursive: true })
  for (const entry of readdirSync(src)) {
    if (skipDirs.has(entry)) continue
    const s = join(src, entry)
    const d = join(dest, entry)
    if (statSync(s).isDirectory()) {
      copyDirFiltered(s, d, skipDirs)
    } else {
      copyFileSync(s, d)
    }
  }
}

// ── Step 1: bundled Python interpreter ───────────────────────────────────────

async function stagePython() {
  const key = pbsAssetKey()
  const asset = PBS_ASSETS[key]
  if (!asset) throw new Error(`No python-build-standalone asset configured for ${key}`)

  const url = `${RUNTIME.urlBase}/${PBS_RELEASE}/${asset}`
  const tarPath = join(RESOURCES, '_python.tar.gz')
  await download(url, tarPath)

  const pythonDir = join(RESOURCES, 'python')
  mkdirSync(pythonDir, { recursive: true })
  // python-build-standalone archives contain a top-level "python/" dir already
  run('tar', ['-xzf', tarPath, '-C', RESOURCES])
  rmSync(tarPath)

  const pythonBin = targetPlatform === 'win32'
    ? join(pythonDir, 'python.exe')
    : join(pythonDir, 'bin', 'python3')

  console.log('Installing pip dependencies into the bundled interpreter…')
  run(pythonBin, ['-m', 'pip', 'install', '--upgrade', 'pip'])
  // requirements.txt's "-e ./videobeaux" line is dev-only: an editable
  // install records an absolute path back to THIS build machine's source
  // tree, which won't exist on an end user's computer. It's also
  // unnecessary here — videobeaux is invoked as "python -m videobeaux.cli"
  // with resourcesPath as cwd (see getPaths() in main/index.js), which
  // Python resolves via sys.path without any pip registration at all.
  // Stage a filtered copy with that line stripped for this install only.
  const rawReqs = readFileSync(join(REPO_ROOT, 'requirements.txt'), 'utf8')
  const filteredReqs = rawReqs.split('\n').filter(line => !line.trim().startsWith('-e ')).join('\n')
  const filteredReqsPath = join(RESOURCES, '_requirements.filtered.txt')
  writeFileSync(filteredReqsPath, filteredReqs)
  run(pythonBin, ['-m', 'pip', 'install', '-r', filteredReqsPath])
  rmSync(filteredReqsPath)

  return pythonBin
}

// ── Step 2: static ffmpeg/ffprobe ────────────────────────────────────────────
// Same fully-featured static build the in-app dev setup downloads (gui/ffmpeg-runtime.json):
// native arm64 + x64 on macOS and x64 on Windows, with libx264/x265, libvpx, libass, libfreetype,
// libzimg and SVT-AV1/dav1d — so HDR tone mapping, caption burning, text overlays and AV1 work in
// the installed app. (No libvidstab: nothing here uses it.)  What the app requires of a build is
// listed in videobeaux/assets/ffmpeg_requirements.json.

// Where a locally built ffmpeg may come from (first match wins), so `npm run dist` works before our release is published:
//   --ffmpeg-dir=PATH  or  VIDEOBEAUX_FFMPEG_DIR=PATH   any folder containing ffmpeg + ffprobe
//   gui/.ffmpeg-build/dist                               what `npm run ffmpeg:local` produces
// Either is refused if it is an --enable-nonfree build. Otherwise our published release is downloaded.
const ffmpegDirArg = process.argv.find(a => a.startsWith('--ffmpeg-dir='))
const LOCAL_FFMPEG_CANDIDATES = [
  ffmpegDirArg && ffmpegDirArg.split('=')[1],
  process.env.VIDEOBEAUX_FFMPEG_DIR,
  join(GUI_ROOT, '.ffmpeg-build', 'dist')
]

async function stageFfmpeg(localDir) {
  const target = join(RESOURCES, 'ffmpeg')
  if (localDir) {
    if (targetPlatform !== process.platform) {
      throw new Error(`A local ffmpeg can only be bundled for this machine's platform (${process.platform}); `
        + `use the published release for ${targetPlatform}.`)
    }
    const r = await adoptLocalFfmpeg({ sourceDir: localDir, targetDir: target, platform: targetPlatform })
    console.log(`Using your locally built ffmpeg from ${localDir}\n  ${r.version}\n  licence flavor: ${r.license?.flavor || 'unknown'}`)
    return
  }
  const runtime = JSON.parse(readFileSync(join(GUI_ROOT, 'ffmpeg-runtime.json'), 'utf8'))
  try {
    await installFfmpeg({
      targetDir: target,
      runtime,
      platform: targetPlatform,
      arch: process.arch,
      onProgress: p => { if (p.message && p.received === 0) console.log(p.message) }
    })
  } catch (e) {
    if (/HTTP 404/.test(e.message)) {
      throw new Error(
        `Our ffmpeg release "${runtime.tag}" has not been published yet (HTTP 404), and the installer never falls back to a ` +
        `third-party build.\n\nBuild it yourself and re-run:\n` +
        `    npm run ffmpeg:local && npm run dist\n` +
        `(or point at any non-nonfree build:  VIDEOBEAUX_FFMPEG_DIR=/path/to/folder npm run dist)\n\n` +
        `Or publish the release: GitHub → Actions → "Build redistributable ffmpeg", then push tag ${runtime.tag}.`)
    }
    throw e
  }
  // Release guard: installFfmpeg already refuses a --enable-nonfree binary (it can't be redistributed).
  // Report the flavor so it is visible in the build log, and enforce it for binaries staged some other way.
  const bin = ffmpegBinaryPath(target, 'ffmpeg', targetPlatform)
  if (targetPlatform === process.platform) {
    const lic = await ffmpegLicense(bin)
    if (lic) {
      console.log(`ffmpeg licence flavor: ${lic.flavor}${lic.version3 ? ' (v3)' : ''}`)
      if (lic.nonfree) throw new Error('Refusing to package an --enable-nonfree ffmpeg: it is not redistributable.')
    }
  }
}

// ── Step 3: videobeaux package + discover_programs.py ───────────────────────
// Staged so resourcesPath itself is the exact equivalent of the dev repo
// root — resources/videobeaux/ (the importable package) and
// resources/gui/discover_programs.py — because discover_programs.py computes
// its own VB_ROOT as "one directory above my own location" (SCRIPT_DIR/..),
// i.e. it expects to live at <root>/gui/discover_programs.py with
// videobeaux/ at <root>/videobeaux, exactly mirroring the dev layout.
// Matching that structure exactly (rather than putting it directly beside
// videobeaux/) means main/index.js can use the identical relative path in
// both dev and packaged modes with no special-casing.

function stageVideobeaux() {
  const dest = join(RESOURCES, 'videobeaux')
  copyDirFiltered(join(REPO_ROOT, 'videobeaux'), dest, new Set(['__pycache__', 'videobeaux.egg-info']))
  const guiDest = join(RESOURCES, 'gui')
  mkdirSync(guiDest, { recursive: true })
  copyFileSync(join(GUI_ROOT, 'discover_programs.py'), join(guiDest, 'discover_programs.py'))
  copyFileSync(join(GUI_ROOT, 'arg_ranges.py'), join(guiDest, 'arg_ranges.py'))
  // The "Appearance → Module previews → Choose clip…" feature renders thumbnails from the user's own video with these
  // two scripts (they find videobeaux/ and gui/ relative to their own location, so they sit at the same depth as in the repo).
  for (const [from, to] of [[join(REPO_ROOT, 'tools', 'make_module_art.py'), join(RESOURCES, 'tools', 'make_module_art.py')],
                            [join(REPO_ROOT, 'tests', 'smoke', 'run_smoke.py'), join(RESOURCES, 'tests', 'smoke', 'run_smoke.py')]]) {
    mkdirSync(dirname(to), { recursive: true })
    copyFileSync(from, to)
  }
}

// ── Main ──────────────────────────────────────────────────────────────────

async function main() {
  console.log(`Staging gui/resources/ for platform: ${targetPlatform}`)
  // A local ffmpeg may live inside gui/resources itself (e.g. the one a previous run staged) — keep a copy across the wipe.
  let localDir = findLocalFfmpegDir(LOCAL_FFMPEG_CANDIDATES, targetPlatform)
  if (localDir && (localDir === RESOURCES || localDir.startsWith(RESOURCES + '/') || localDir.startsWith(RESOURCES + '\\'))) {
    const keep = mkdtempSync(join(tmpdir(), 'vb-ffmpeg-keep-'))
    for (const t of ['ffmpeg', 'ffprobe']) copyFileSync(ffmpegBinaryPath(localDir, t, targetPlatform), ffmpegBinaryPath(keep, t, targetPlatform))
    localDir = keep
  }
  if (ffmpegDirArg && !localDir) throw new Error(`--ffmpeg-dir: no ffmpeg + ffprobe found in ${ffmpegDirArg.split('=')[1]}`)
  rmrf(RESOURCES)
  mkdirSync(RESOURCES, { recursive: true })

  await stagePython()
  await stageFfmpeg(localDir)
  stageVideobeaux()

  console.log('\n✓ gui/resources/ staged:')
  console.log(`  ${join(RESOURCES, 'python')}`)
  console.log(`  ${join(RESOURCES, 'ffmpeg')}`)
  console.log(`  ${join(RESOURCES, 'videobeaux')}`)
  console.log(`  ${join(RESOURCES, 'discover_programs.py')}`)
}

main().catch(err => {
  console.error('\n✗ build-python-env failed:', err.message)
  process.exit(1)
})
