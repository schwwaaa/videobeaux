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

import { mkdirSync, rmSync, readdirSync, statSync, copyFileSync, createWriteStream, readFileSync, writeFileSync, mkdtempSync, chmodSync, statfsSync, existsSync } from 'fs'
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
  assertNoBrokenLinks(pythonDir)

  return pythonBin
}

// python-build-standalone uses symlinks (bin/python3 → python3.x). A link that doesn't resolve after staging would leave a
// broken interpreter inside the app, so fail here rather than on a user's first launch.
function assertNoBrokenLinks(dir) {
  const broken = []
  const walk = d => {
    for (const e of readdirSync(d, { withFileTypes: true })) {
      const p = join(d, e.name)
      if (e.isSymbolicLink()) { if (!existsSync(p)) broken.push(p) }
      else if (e.isDirectory()) walk(p)
    }
  }
  walk(dir)
  if (broken.length) throw new Error(`Broken symlinks in the bundled Python: ${broken.slice(0, 5).join(', ')}`)
}

// ── Step 2: static ffmpeg/ffprobe ────────────────────────────────────────────
// Same fully-featured static build the in-app dev setup downloads (gui/ffmpeg-runtime.json):
// native arm64 + x64 on macOS and x64 on Windows, with libx264/x265, libvpx, libass, libfreetype,
// libzimg and SVT-AV1/dav1d — so HDR tone mapping, caption burning, text overlays and AV1 work in
// the installed app. (No libvidstab: nothing here uses it.)  What the app requires of a build is
// listed in videobeaux/assets/ffmpeg_requirements.json.

// Where ffmpeg comes from (first match wins) — decided BEFORE anything in gui/resources is touched, so a missing ffmpeg
// stops the build in seconds instead of after 10 minutes of Python/pip work, and never costs you what a previous run staged:
//   --ffmpeg-dir=PATH  or  VIDEOBEAUX_FFMPEG_DIR=PATH   any folder containing ffmpeg + ffprobe
//   gui/.ffmpeg-build/dist                               what `npm run ffmpeg:local` produces
//   gui/resources/ffmpeg                                 the one a previous successful run staged
//   our published release (gui/ffmpeg-runtime.json)
// A local build is refused if it won't start or is --enable-nonfree. The installer never uses a third-party build.
const ffmpegDirArg = process.argv.find(a => a.startsWith('--ffmpeg-dir='))
const LOCAL_FFMPEG_CANDIDATES = [
  ffmpegDirArg && ffmpegDirArg.split('=')[1],
  process.env.VIDEOBEAUX_FFMPEG_DIR,
  join(GUI_ROOT, '.ffmpeg-build', 'dist'),
  join(RESOURCES, 'ffmpeg')
]

/** Returns { dir, how } — a scratch folder holding a verified ffmpeg + ffprobe, ready to be copied into resources. */
async function resolveFfmpeg() {
  const keep = mkdtempSync(join(tmpdir(), 'vb-ffmpeg-stage-'))
  const localDir = targetPlatform === process.platform ? findLocalFfmpegDir(LOCAL_FFMPEG_CANDIDATES, targetPlatform) : null
  if (ffmpegDirArg && !localDir) throw new Error(`--ffmpeg-dir: no ffmpeg + ffprobe found in ${ffmpegDirArg.split('=')[1]}`)
  if (localDir) {
    const r = await adoptLocalFfmpeg({ sourceDir: localDir, targetDir: keep, platform: targetPlatform })
    return { dir: keep, how: `local build in ${localDir}`, version: r.version, flavor: r.license?.flavor }
  }
  const runtime = JSON.parse(readFileSync(join(GUI_ROOT, 'ffmpeg-runtime.json'), 'utf8'))
  try {
    await installFfmpeg({
      targetDir: keep,
      runtime,
      platform: targetPlatform,
      arch: process.arch,
      onProgress: p => { if (p.message && p.received === 0) console.log('  ' + p.message) }
    })
  } catch (e) {
    if (/HTTP 404/.test(e.message)) {
      throw new Error(
        `Our ffmpeg release "${runtime.tag}" has not been published yet (HTTP 404), and the installer never falls back to a ` +
        `third-party build. Nothing in gui/resources was touched.\n\nBuild it yourself and re-run:\n` +
        `    npm run ffmpeg:local && npm run dist\n` +
        `(or point at any non-nonfree build:  VIDEOBEAUX_FFMPEG_DIR=/path/to/folder npm run dist)\n\n` +
        `Or publish the release: GitHub → Actions → "Build redistributable ffmpeg", then push tag ${runtime.tag}.`)
    }
    throw e
  }
  const lic = targetPlatform === process.platform ? await ffmpegLicense(ffmpegBinaryPath(keep, 'ffmpeg', targetPlatform)) : null
  if (lic?.nonfree) throw new Error('Refusing to package an --enable-nonfree ffmpeg: it is not redistributable.')
  return { dir: keep, how: `published release ${runtime.tag}`, version: '', flavor: lic?.flavor }
}

function placeFfmpeg(from) {
  const target = join(RESOURCES, 'ffmpeg')
  mkdirSync(target, { recursive: true })
  for (const t of ['ffmpeg', 'ffprobe']) {
    const dest = ffmpegBinaryPath(target, t, targetPlatform)
    copyFileSync(ffmpegBinaryPath(from, t, targetPlatform), dest)
    if (targetPlatform !== 'win32') chmodSync(dest, 0o755)
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
  // the example library: presets + the sample clip, shown by the app's Examples button
  copyDirFiltered(join(REPO_ROOT, 'examples'), join(RESOURCES, 'examples'), new Set(['README.md']))
  const guiDest = join(RESOURCES, 'gui')
  mkdirSync(guiDest, { recursive: true })
  copyFileSync(join(GUI_ROOT, 'discover_programs.py'), join(guiDest, 'discover_programs.py'))
  copyFileSync(join(GUI_ROOT, 'arg_ranges.py'), join(guiDest, 'arg_ranges.py'))
  // The "Looks → Output art → Choose clip…" feature renders thumbnails from the user's own video with make_module_art.py, which
  // runs the smoke runner. Both go to resources/tools/ — the same depth as tools/ in the repo — so each finds videobeaux/ and
  // gui/ relative to its own location. Nothing else from tests/ or tools/ ships.
  // The per-slider response curves (gui/slider_curves.json) are read by discover_programs.py from its own folder.
  copyFileSync(join(GUI_ROOT, 'slider_curves.json'), join(guiDest, 'slider_curves.json'))
  for (const [from, to] of [[join(REPO_ROOT, 'tools', 'make_module_art.py'), join(RESOURCES, 'tools', 'make_module_art.py')],
                            [join(REPO_ROOT, 'tests', 'smoke', 'run_smoke.py'), join(RESOURCES, 'tools', 'run_smoke.py')]]) {
    mkdirSync(dirname(to), { recursive: true })
    copyFileSync(from, to)
  }
}

// ── Main ──────────────────────────────────────────────────────────────────

function checkDisk() {
  try {
    const st = statfsSync(GUI_ROOT)
    const free = Number(st.bavail) * Number(st.bsize) / 1e9
    console.log(`Free disk space: ${free.toFixed(1)} GB`)
    if (free < 4) throw new Error(`Only ${free.toFixed(1)} GB free — the installer build needs roughly 6–8 GB. Free some space and re-run.`)
    if (free < 10) console.log('  ⚠️  Under 10 GB free: the build may run out of space.')
  } catch (e) {
    if (/free —/.test(e.message)) throw e                      // our own message; statfs being unavailable is not an error
  }
}

async function main() {
  console.log(`Staging gui/resources/ for platform: ${targetPlatform}`)
  checkDisk()

  console.log('\n[1/4] ffmpeg — deciding where it comes from (nothing is deleted yet)')
  const ff = await resolveFfmpeg()
  console.log(`  using the ${ff.how}${ff.version ? `\n  ${ff.version}` : ''}${ff.flavor ? `\n  licence flavor: ${ff.flavor}` : ''}`)

  console.log('\n[2/4] Python interpreter + packages (the slow part)')
  rmrf(RESOURCES)
  mkdirSync(RESOURCES, { recursive: true })
  await stagePython()

  console.log('\n[3/4] copying ffmpeg into gui/resources/ffmpeg')
  placeFfmpeg(ff.dir)
  rmrf(ff.dir)

  console.log('\n[4/4] videobeaux package + tools')
  stageVideobeaux()

  console.log('\n✓ gui/resources/ staged:')
  console.log(`  ${join(RESOURCES, 'python')}`)
  console.log(`  ${join(RESOURCES, 'ffmpeg')}`)
  console.log(`  ${join(RESOURCES, 'videobeaux')}`)
  console.log(`  ${join(RESOURCES, 'gui', 'discover_programs.py')}`)
}

main().catch(err => {
  console.error('\n✗ build-python-env failed:', err.message)
  process.exit(1)
})
