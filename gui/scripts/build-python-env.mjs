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

import { mkdirSync, rmSync, readdirSync, statSync, copyFileSync, createWriteStream, readFileSync, writeFileSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import { spawnSync } from 'child_process'
import { pipeline } from 'stream/promises'

const __dirname = dirname(fileURLToPath(import.meta.url))
const GUI_ROOT = join(__dirname, '..')
const REPO_ROOT = join(GUI_ROOT, '..')
const RESOURCES = join(GUI_ROOT, 'resources')

const platformArg = process.argv.find(a => a.startsWith('--platform='))
const targetPlatform = platformArg ? platformArg.split('=')[1] : process.platform

// ── python-build-standalone: pinned release + per-platform asset names ──────
// Bump PBS_RELEASE/PYTHON_VERSION periodically (check
// https://github.com/astral-sh/python-build-standalone/releases) — pinned
// rather than "latest" so a build today and a build in six months produce
// the same interpreter.
const PBS_RELEASE = '20260901'
const PYTHON_VERSION = '3.12.14'
const PBS_ASSETS = {
  darwin_arm64: `cpython-${PYTHON_VERSION}+${PBS_RELEASE}-aarch64-apple-darwin-install_only.tar.gz`,
  darwin_x64: `cpython-${PYTHON_VERSION}+${PBS_RELEASE}-x86_64-apple-darwin-install_only.tar.gz`,
  win32_x64: `cpython-${PYTHON_VERSION}+${PBS_RELEASE}-x86_64-pc-windows-msvc-install_only.tar.gz`
}

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

  const url = `https://github.com/astral-sh/python-build-standalone/releases/download/${PBS_RELEASE}/${asset}`
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

async function stageFfmpeg() {
  const ffmpegDir = join(RESOURCES, 'ffmpeg')
  mkdirSync(ffmpegDir, { recursive: true })

  if (targetPlatform === 'darwin') {
    for (const tool of ['ffmpeg', 'ffprobe']) {
      const info = await fetch(`https://evermeet.cx/ffmpeg/info/${tool}/release`).then(r => r.json())
      const zipUrl = info.download.zip.url
      const zipPath = join(RESOURCES, `_${tool}.zip`)
      await download(zipUrl, zipPath)
      run('unzip', ['-o', zipPath, '-d', ffmpegDir])
      rmSync(zipPath)
      run('chmod', ['+x', join(ffmpegDir, tool)])
    }
  } else if (targetPlatform === 'win32') {
    // GPL static build (needed: every program here uses libx264, which
    // LGPL-only builds omit) — BtbN's "latest n9.0" tag is a stable pointer
    // that only advances within the 9.0.x line, not a moving "master" build.
    const url = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n9.0-latest-win64-gpl-9.0.zip'
    const zipPath = join(RESOURCES, '_ffmpeg.zip')
    await download(url, zipPath)
    const extractDir = join(RESOURCES, '_ffmpeg_extract')
    run('powershell', ['-NoProfile', '-Command', `Expand-Archive -LiteralPath "${zipPath}" -DestinationPath "${extractDir}" -Force`])
    // BtbN's zip nests everything under one top-level folder with a bin/ subdir.
    const topLevel = readdirSync(extractDir)[0]
    const binDir = join(extractDir, topLevel, 'bin')
    for (const f of ['ffmpeg.exe', 'ffprobe.exe']) {
      copyFileSync(join(binDir, f), join(ffmpegDir, f))
    }
    rmrf(extractDir)
    rmSync(zipPath)
  } else {
    throw new Error(`No ffmpeg bundling configured for platform: ${targetPlatform}`)
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
}

// ── Main ──────────────────────────────────────────────────────────────────

async function main() {
  console.log(`Staging gui/resources/ for platform: ${targetPlatform}`)
  rmrf(RESOURCES)
  mkdirSync(RESOURCES, { recursive: true })

  await stagePython()
  await stageFfmpeg()
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
