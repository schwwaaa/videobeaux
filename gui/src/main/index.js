import { app, BrowserWindow, ipcMain, dialog, shell } from 'electron'
import { join, dirname, extname, parse, delimiter } from 'path'
import { fileURLToPath } from 'url'
import { spawn } from 'child_process'
import { unlinkSync, statSync, existsSync, readdirSync, writeFileSync, readFileSync, rmSync, mkdirSync, createWriteStream } from 'fs'
import { tmpdir } from 'os'
import { randomUUID } from 'crypto'
import { execFile } from 'child_process'
import { promisify } from 'util'
import { downloadToFile } from './download.js'
import { findVenvPython, installPython } from './pythonSetup.js'
import { ffmpegBinaryPath, inspectFfmpeg, installFfmpeg } from './toolsSetup.js'
import pythonRuntime from '../../python-runtime.json'
import ffmpegRuntime from '../../ffmpeg-runtime.json'

const execFileAsync = promisify(execFile)

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// Dev (npm run dev): index.js runs unpacked from gui/out/main/, so climbing
// three levels up (out/main -> out -> gui -> repo root) reaches the project.
// Packaged: index.js runs from inside app.asar, so that same climb would
// land outside the .app bundle entirely — everything needed instead lives
// in process.resourcesPath, populated by electron-builder's extraResources
// (see gui/scripts/build-python-env.mjs and package.json's build config).
// modelsDir is deliberately NOT under resourcesPath even when packaged: a
// signed/notarized .app's Resources folder is effectively read-only by
// convention, and a Program Files install needs admin rights to write —
// models need a genuinely user-writable location from the start.
function getPaths() {
  if (app.isPackaged) {
    // vbRoot is resourcesPath itself (not resources/videobeaux) — it must be
    // the PARENT of the videobeaux/ package dir, exactly mirroring dev mode
    // where vbRoot is the repo root containing videobeaux/ as a subfolder.
    // "python -m videobeaux.cli" only resolves the package when run with
    // this directory as cwd; discover_programs.py is staged as its sibling
    // for the same reason (see build-python-env.mjs's staging layout).
    const resources = process.resourcesPath
    return {
      vbRoot: resources,
      pythonHome: join(resources, 'python'),
      ffmpegDir: join(resources, 'ffmpeg'),
      modelsDir: join(app.getPath('userData'), 'models')
    }
  }
  const vbRoot = join(__dirname, '../../..')
  return {
    vbRoot,
    pythonHome: join(vbRoot, 'venv'),
    ffmpegDir: findManagedFfmpegDir(vbRoot) || findFullFfmpegDir(), // null → dev falls back to whatever ffmpeg is on PATH
    modelsDir: join(vbRoot, 'models')
  }
}

// Dev only. The app can download its own full-featured ffmpeg into
// <repo>/.tools/ffmpeg (see setup:repair) — preferred over anything on the machine.
function managedFfmpegDir(vbRoot) {
  return join(vbRoot, '.tools', 'ffmpeg')
}
function findManagedFfmpegDir(vbRoot) {
  const dir = managedFfmpegDir(vbRoot)
  return existsSync(ffmpegBinaryPath(dir, 'ffmpeg')) ? dir : null
}

// Dev only. Homebrew's plain `ffmpeg` formula omits libzimg/libass/libfreetype
// (zscale, ass, drawtext) that HDR tone mapping, Captburn and Thumbs labels
// need. `ffmpeg-full` is keg-only, so even when installed it isn't on PATH
// unless the user relinked it — prefer it automatically when it's there.
function findFullFfmpegDir() {
  for (const dir of ['/opt/homebrew/opt/ffmpeg-full/bin', '/usr/local/opt/ffmpeg-full/bin']) {
    if (existsSync(join(dir, 'ffmpeg'))) return dir
  }
  return null
}

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: '#141414',
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  })

  if (process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }

  return mainWindow
}

// A packaged/GUI-launched Electron app only inherits whatever PATH its own
// launcher happened to have — not the user's actual shell config. On macOS
// especially, that means a tool installed to a user-local bin directory
// (uv tool install, pipx, cargo, etc.) can be genuinely on PATH in every
// Terminal the user opens and still be completely invisible to spawn() here,
// producing a confusing "not found" even though `which <tool>` works fine
// for the user. Querying the user's own login shell for its real PATH once,
// at startup, fixes this for every external tool this app ever shells out to
// (ffmpeg in dev, kokoro-tts, ollama, etc.) — not just a one-off workaround
// for a single tool.
async function syncShellPath() {
  if (process.platform === 'win32') return // Windows doesn't have this class of problem
  try {
    const userShell = process.env.SHELL || '/bin/zsh'
    const { stdout } = await execFileAsync(
      userShell,
      // ${PATH} (braced), not $PATH — bash/zsh treat "_" as a valid identifier
      // character, so an unbraced $PATH immediately followed by "__PATH_END__"
      // parses as one (undefined) variable name and silently expands to
      // nothing, truncating the whole marker string right after the prefix.
      ['-ilc', 'echo -n "__PATH_START__${PATH}__PATH_END__"'],
      { timeout: 5000 }
    )
    const match = stdout.match(/__PATH_START__(.*)__PATH_END__/s)
    if (match && match[1]) {
      process.env.PATH = match[1]
    }
  } catch (err) {
    console.error('Could not sync PATH from login shell (non-fatal):', err.message)
  }
}

app.whenReady().then(async () => {
  await syncShellPath()
  const win = createWindow()

  // ── File dialogs ────────────────────────────────────────────────────────────

  ipcMain.handle('dialog:openFile', async (_, filters) => {
    const result = await dialog.showOpenDialog(win, {
      properties: ['openFile'],
      filters: filters || [
        { name: 'Videos', extensions: ['mp4', 'mov', 'avi', 'mkv', 'webm', 'mts', 'mpg', 'mpeg'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    })
    return result.filePaths[0] || null
  })

  ipcMain.handle('dialog:openDirectory', async () => {
    const result = await dialog.showOpenDialog(win, {
      properties: ['openDirectory', 'createDirectory'],
      buttonLabel: 'Select Folder'
    })
    return result.filePaths[0] || null
  })

  ipcMain.handle('dialog:saveFile', async (_, { defaultName, filters }) => {
    const result = await dialog.showSaveDialog(win, {
      defaultPath: defaultName || 'output.mp4',
      filters: filters || [
        { name: 'MP4 Video', extensions: ['mp4'] },
        { name: 'MOV Video', extensions: ['mov'] },
        { name: 'AVI Video', extensions: ['avi'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    })
    return result.filePath || null
  })

  // ── Presets (canvas save/load) ────────────────────────────────────────────────

  ipcMain.handle('presets:save', async (_, { defaultName, data }) => {
    const result = await dialog.showSaveDialog(win, {
      defaultPath: defaultName || 'pipeline.vbpreset.json',
      filters: [
        { name: 'Videobeaux Preset', extensions: ['json'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    })
    if (!result.filePath) return null
    writeFileSync(result.filePath, JSON.stringify(data, null, 2), 'utf8')
    return result.filePath
  })

  ipcMain.handle('presets:load', async () => {
    const result = await dialog.showOpenDialog(win, {
      properties: ['openFile'],
      filters: [
        { name: 'Videobeaux Preset', extensions: ['json'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    })
    if (!result.filePaths[0]) return null
    const raw = readFileSync(result.filePaths[0], 'utf8')
    return { path: result.filePaths[0], data: JSON.parse(raw) }
  })

  // ── App settings (theme, shadow style) ──────────────────────────────────────
  // Small persisted prefs, unrelated to any one pipeline — stored as JSON
  // under userData (the same writable-everywhere directory modelsDir already
  // uses), not the file-dialog-driven preset mechanism above.

  const DEFAULT_SETTINGS = {
    theme: 'light',
    shadowOffset: 5,
    shadowColor: '#080808',
    shadowsEnabled: true,
    setupSeen: false
  }

  function settingsPath() {
    const dir = app.getPath('userData')
    mkdirSync(dir, { recursive: true })
    return join(dir, 'settings.json')
  }

  ipcMain.handle('settings:get', () => {
    try {
      const raw = readFileSync(settingsPath(), 'utf8')
      return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) }
    } catch {
      return { ...DEFAULT_SETTINGS }
    }
  })

  ipcMain.handle('settings:set', (_, patch) => {
    // Merge into what's already stored so one caller's partial update can't wipe another's keys.
    let current = {}
    try { current = JSON.parse(readFileSync(settingsPath(), 'utf8')) } catch { /* first write */ }
    const merged = { ...DEFAULT_SETTINGS, ...current, ...patch }
    writeFileSync(settingsPath(), JSON.stringify(merged, null, 2), 'utf8')
    return merged
  })

  // ── Program discovery ────────────────────────────────────────────────────────

  ipcMain.handle('programs:discover', () => {
    return new Promise((resolve) => {
      const { vbRoot, ffmpegDir } = getPaths()
      const interpreter = findPython()
      // Same relative path in both dev and packaged modes: discover_programs.py
      // computes its own VB_ROOT as "one directory above my own location," so
      // the staged resources/ tree mirrors gui/discover_programs.py's dev
      // location exactly (see build-python-env.mjs) rather than needing a
      // packaged-specific path here.
      const script = join(vbRoot, 'gui', 'discover_programs.py')

      let output = ''
      const proc = spawn(interpreter, [script], {
        cwd: vbRoot,
        env: {
          ...process.env,
          PYTHONUTF8: '1',
          PYTHONIOENCODING: 'utf-8',
          ...(ffmpegDir ? { PATH: `${ffmpegDir}${delimiter}${process.env.PATH}` } : {})
        },
        windowsHide: true
      })
      proc.stdout.on('data', d => { output += d.toString('utf8') })
      proc.on('close', code => {
        if (code === 0) {
          try   { resolve(JSON.parse(output)) }
          catch { resolve({}) }
        } else {
          resolve({})
        }
      })
      proc.on('error', () => resolve({}))
    })
  })

  // ── Model picker ─────────────────────────────────────────────────────────────
  // Lists videobeaux-gui/models/ fresh on every call (not cached like program
  // discovery), so a model dropped in mid-session shows up without a restart.
  //
  // The only current consumer of this list is the Vosk "STT Model" field
  // (transcraibe/auto_narrate's stt_model), so this filters to directories
  // that actually look like a Vosk model — a conf/model.conf file is the
  // one thing every Vosk model release has. Without this, models/ also
  // shows kokoro-tts's folder (a TTS model with a completely different,
  // flat layout — kokoro-v1.0.onnx + voices-v1.0.bin, no conf/ at all) as
  // a selectable "Vosk Model", which crashes Vosk's Model() constructor
  // if picked since it's not a Vosk model at all.
  ipcMain.handle('models:list', () => {
    const { modelsDir } = getPaths()
    try {
      return readdirSync(modelsDir, { withFileTypes: true })
        .filter(e => e.isDirectory())
        .filter(e => existsSync(join(modelsDir, e.name, 'conf', 'model.conf')))
        .map(e => ({ name: e.name, path: join(modelsDir, e.name) }))
    } catch {
      return []
    }
  })

  // ── Batch helpers ─────────────────────────────────────────────────────────────
  // Shared between the files:listVideos IPC handler (used by the Input node's
  // live file-count display), the pipeline runner's batch-source seeding, and
  // discovering what a native fan-out program (qwikchop) wrote after it runs.

  const VIDEO_EXTS = new Set(['.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.mts', '.mpg', '.mpeg'])

  function listVideoFiles(dirPath) {
    try {
      return readdirSync(dirPath, { withFileTypes: true })
        .filter(e => e.isFile() && VIDEO_EXTS.has(extname(e.name).toLowerCase()))
        .map(e => join(dirPath, e.name))
        .sort()
    } catch {
      return []
    }
  }

  /** The folder a program's output stem resolves to (extension stripped) —
   *  the same convention extract_frames.py/qwikchop.py use for their own
   *  multi-file output, so a batch task's discovered/derived directory always
   *  matches what the Python side actually wrote to. */
  function batchDirFor(outputPath) {
    const { dir, name } = parse(outputPath)
    return join(dir, name)
  }

  ipcMain.handle('files:listVideos', (_, dirPath) => listVideoFiles(dirPath))

  // ── Helper-window support (e.g. the Lagkage layout editor) ──────────────────────

  // Same path rules lagkage.py uses for a layer's "filename": absolute paths/URLs as-is,
  // "../media/x" and "media/x" relative to the project root, anything else next to the JSON.
  function resolveLayerPath(filename, layoutPath) {
    if (!filename) return filename
    if (filename.includes('://') || filename.startsWith('/') || /^[A-Za-z]:[\\/]/.test(filename)) return filename
    const { vbRoot } = getPaths()
    if (filename.startsWith('../media/')) return join(vbRoot, 'media', filename.slice('../media/'.length))
    if (filename.startsWith('media/')) return join(vbRoot, filename)
    return join(layoutPath ? dirname(layoutPath) : vbRoot, filename)
  }

  const IMAGE_MIME = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif',
                       '.webp': 'image/webp', '.bmp': 'image/bmp', '.svg': 'image/svg+xml' }

  // Small local images as data: URLs so the sandboxed renderer (CSP: 'self') can preview them.
  ipcMain.handle('files:readDataUrl', (_, { path, layoutPath }) => {
    try {
      const full = resolveLayerPath(path, layoutPath)
      const mime = IMAGE_MIME[extname(full).toLowerCase()]
      if (!mime) return null
      if (statSync(full).size > 30 * 1024 * 1024) return null
      return `data:${mime};base64,${readFileSync(full).toString('base64')}`
    } catch { return null }
  })

  // Width/height/duration of any image or video via ffprobe (managed ffmpeg when we have one).
  ipcMain.handle('media:probe', async (_, { path, layoutPath }) => {
    try {
      const { ffmpegDir } = getPaths()
      const ffprobe = ffmpegDir ? ffmpegBinaryPath(ffmpegDir, 'ffprobe') : 'ffprobe'
      const full = resolveLayerPath(path, layoutPath)
      const { stdout } = await execFileAsync(ffprobe, [
        '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:format=duration',
        '-of', 'json', full], { timeout: 15000 })
      const j = JSON.parse(stdout)
      const st = (j.streams || [])[0] || {}
      return { width: st.width || 0, height: st.height || 0, duration: Number(j.format?.duration) || 0, resolved: full }
    } catch { return null }
  })

  // Layout JSON files made by helper windows live under userData/layouts (user-writable, survives updates).
  ipcMain.handle('layouts:write', (_, { name, json }) => {
    const dir = join(app.getPath('userData'), 'layouts')
    mkdirSync(dir, { recursive: true })
    const safe = String(name || 'layout').replace(/[^A-Za-z0-9._-]+/g, '_').slice(0, 80)
    const file = join(dir, safe.endsWith('.json') ? safe : `${safe}.json`)
    writeFileSync(file, typeof json === 'string' ? json : JSON.stringify(json, null, 2), 'utf8')
    return file
  })

  ipcMain.handle('layouts:read', (_, path) => {
    try {
      if (!path || extname(path).toLowerCase() !== '.json' || statSync(path).size > 2 * 1024 * 1024) return null
      return readFileSync(path, 'utf8')
    } catch { return null }
  })

  ipcMain.handle('run:confirmOverwrite', async (_, { outputPath, isBatch }) => {
    let target = outputPath
    let needsConfirm = false
    try {
      if (isBatch) {
        target = batchDirFor(outputPath)
        needsConfirm = existsSync(target) && readdirSync(target).length > 0
      } else {
        needsConfirm = existsSync(outputPath)
      }
    } catch {
      needsConfirm = false
    }

    if (!needsConfirm) return { proceed: true }

    const result = await dialog.showMessageBox(win, {
      type: 'warning',
      buttons: ['Cancel', 'Overwrite'],
      defaultId: 0,
      cancelId: 0,
      message: isBatch
        ? `The folder "${target}" already contains files.`
        : `"${target}" already exists.`,
      detail: 'Continue and overwrite it?'
    })
    return { proceed: result.response === 1 }
  })

  // ── Ollama model picker ──────────────────────────────────────────────────────
  // Optional-path support for auto_narrate's --topic mode. Queries whatever
  // Ollama server happens to be running locally; degrades to an empty list
  // (not an error) if it isn't reachable, since this is never a hard
  // requirement of any program.

  ipcMain.handle('ollama:listModels', async () => {
    try {
      const res = await fetch('http://localhost:11434/api/tags', { signal: AbortSignal.timeout(2000) })
      if (!res.ok) return []
      const data = await res.json()
      return (data.models || []).map(m => ({ name: m.name, size: m.size }))
    } catch {
      return []
    }
  })

  // ── kokoro-tts voice picker ────────────────────────────────────────────────
  // Queries kokoro-tts's own `--help-voices` output rather than a hardcoded
  // list — fully local, no network, and stays accurate across kokoro-tts
  // versions/voice-pack updates without us maintaining a duplicate list.
  // Degrades to an empty list (not an error) if kokoro-tts isn't installed,
  // matching auto_narrate's own "optional tool" treatment of it.

  // How to invoke kokoro-tts: through the app's own Python when the package
  // is installed there (always true in the packaged app — and a console
  // script installed by pip into a relocatable bundle has a shebang pointing
  // at the build machine, so `python -m kokoro_tts` is the reliable form), else
  // a `kokoro-tts` on PATH (e.g. a dev machine's `uv tool install`).
  async function kokoroInvocation() {
    const python = findPython()
    const bundled = await new Promise(resolve => {
      let proc
      try {
        proc = spawn(python, ['-c', "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('kokoro_tts') else 1)"],
          { windowsHide: true })
      } catch { return resolve(false) }
      proc.on('close', code => resolve(code === 0))
      proc.on('error', () => resolve(false))
    })
    return bundled
      ? { cmd: python, pre: ['-m', 'kokoro_tts'], source: 'bundled' }
      : { cmd: 'kokoro-tts', pre: [], source: 'system' }
  }

  ipcMain.handle('kokoro:listVoices', async () => {
    try {
      const { modelsDir } = getPaths()
      const kokoroModel = join(modelsDir, 'kokoro-tts', 'kokoro-v1.0.onnx')
      const kokoroVoices = join(modelsDir, 'kokoro-tts', 'voices-v1.0.bin')
      const { cmd, pre } = await kokoroInvocation()
      const args = [...pre, '--help-voices']
      if (existsSync(kokoroModel) && existsSync(kokoroVoices)) {
        args.push('--model', kokoroModel, '--voices', kokoroVoices)
      }
      const { stdout } = await execFileAsync(cmd, args, { timeout: 15000 })
      return stdout
        .split('\n')
        .map(line => line.match(/^\s*\d+\.\s*(\S+)/))
        .filter(Boolean)
        .map(m => m[1])
    } catch {
      return []
    }
  })

  // ── Optional features: narration voice (kokoro-tts) + Ollama ────────────────
  // Neither is needed by most programs, so Setup treats them as opt-in extras
  // rather than required environment checks.

  // Exact sizes let the downloader reject a truncated file instead of leaving
  // something that looks installed but fails at synthesis time.
  const KOKORO_FILES = [
    { name: 'kokoro-v1.0.onnx', size: 325532387,
      url: 'https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx' },
    { name: 'voices-v1.0.bin', size: 26124436,
      url: 'https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin' }
  ]

  function kokoroModelStatus() {
    const { modelsDir } = getPaths()
    const missing = KOKORO_FILES
      .filter(f => {
        const p = join(modelsDir, 'kokoro-tts', f.name)
        try { return !existsSync(p) || statSync(p).size !== f.size } catch { return true }
      })
      .map(f => f.name)
    return { ok: missing.length === 0, missing }
  }

  // Background-removal models (U²-Net family, run through onnxruntime) — opt-in, kept under models/bgremove/.
  const BG_MODELS = {
    u2netp: { name: 'u2netp.onnx', size: 4574861, label: 'Fast, general-purpose',
              url: 'https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx' },
    u2net_human_seg: { name: 'u2net_human_seg.onnx', size: 175997641, label: 'Best for people',
                       url: 'https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx' }
  }

  function bgModelStatus() {
    const { modelsDir } = getPaths()
    const out = {}
    for (const [id, m] of Object.entries(BG_MODELS)) {
      const p = join(modelsDir, 'bgremove', m.name)
      let ok = false
      try { ok = existsSync(p) && statSync(p).size === m.size } catch { /* not installed */ }
      out[id] = { ok, sizeMB: Math.round(m.size / 1e6), label: m.label }
    }
    return out
  }

  ipcMain.handle('setup:downloadBgModel', async (event, id) => {
    const m = BG_MODELS[id]
    if (!m) return { ok: false, error: `Unknown model: ${id}` }
    const { modelsDir } = getPaths()
    const dest = join(modelsDir, 'bgremove', m.name)
    try {
      try { if (existsSync(dest) && statSync(dest).size === m.size) return { ok: true } } catch { /* re-download */ }
      await downloadToFile(m.url, dest, {
        expectedSize: m.size,
        onProgress: ({ received }) => event.sender.send('setup:downloadProgress', {
          modelId: `bgremove-${id}`, received, total: m.size, phase: 'downloading'
        })
      })
      event.sender.send('setup:downloadProgress', { modelId: `bgremove-${id}`, received: m.size, total: m.size, phase: 'done' })
      return { ok: true }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  })

  ipcMain.handle('setup:checkOptional', async () => {
    const [{ cmd, pre, source }, ollamaRunning] = await Promise.all([
      kokoroInvocation(),
      fetch('http://localhost:11434/api/tags', { signal: AbortSignal.timeout(1500) })
        .then(r => r.ok).catch(() => false)
    ])
    const engine = await new Promise(resolve => {
      let proc
      try { proc = spawn(cmd, [...pre, '--version'], { windowsHide: true }) }
      catch (err) { return resolve({ ok: false, detail: err.message }) }
      let out = ''
      proc.stdout?.on('data', d => { out += d.toString('utf8') })
      proc.stderr?.on('data', d => { out += d.toString('utf8') })
      proc.on('close', code => resolve({ ok: code === 0, detail: out.trim().split('\n')[0] || '' }))
      proc.on('error', err => resolve({ ok: false, detail: err.message }))
    })
    const ollamaInstalled = ollamaRunning || await new Promise(resolve => {
      let proc
      try { proc = spawn('ollama', ['--version'], { windowsHide: true }) } catch { return resolve(false) }
      proc.on('close', code => resolve(code === 0))
      proc.on('error', () => resolve(false))
    })
    return {
      kokoro: { engine: { ...engine, source }, models: kokoroModelStatus(),
                downloadMB: Math.round(KOKORO_FILES.reduce((n, f) => n + f.size, 0) / 1e6) },
      ollama: { installed: ollamaInstalled, running: ollamaRunning },
      bgremove: { models: bgModelStatus() }
    }
  })

  ipcMain.handle('setup:downloadKokoro', async (event) => {
    const { modelsDir } = getPaths()
    const totalBytes = KOKORO_FILES.reduce((n, f) => n + f.size, 0)
    let done = 0
    try {
      for (const f of KOKORO_FILES) {
        const dest = join(modelsDir, 'kokoro-tts', f.name)
        try { if (existsSync(dest) && statSync(dest).size === f.size) { done += f.size; continue } } catch { /* re-download */ }
        await downloadToFile(f.url, dest, {
          expectedSize: f.size,
          onProgress: ({ received }) => event.sender.send('setup:downloadProgress', {
            modelId: 'kokoro-tts', received: done + received, total: totalBytes, phase: 'downloading'
          })
        })
        done += f.size
      }
      event.sender.send('setup:downloadProgress', { modelId: 'kokoro-tts', received: totalBytes, total: totalBytes, phase: 'done' })
      return { ok: true }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  })

  // Only the project's own download pages — never an arbitrary URL from the renderer.
  const EXTERNAL_LINKS = { ollama: 'https://ollama.com/download' }
  ipcMain.handle('shell:openExternal', (_, key) => {
    const url = EXTERNAL_LINKS[key]
    if (url) shell.openExternal(url)
    return !!url
  })

  // ── First-run setup ──────────────────────────────────────────────────────────
  // Environment health check + model download, so a downloaded install can
  // get itself working end-to-end without a terminal or any prior Python/
  // ffmpeg knowledge. Re-runnable anytime (not a one-shot wizard) — the
  // renderer decides when to show it (no model found yet) vs. surface it
  // as a menu/button afterward.

  const VOSK_MODEL_CATALOG = [
    { id: 'vosk-model-small-en-us-0.15', label: 'Small — fast, ~40MB download',
      url: 'https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip' },
    { id: 'vosk-model-en-us-0.22-lgraph', label: 'Standard — balanced, ~130MB download (recommended)',
      url: 'https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip' },
    { id: 'vosk-model-en-us-0.22', label: 'Large — most accurate, ~1.9GB download',
      url: 'https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip' }
  ]

  ipcMain.handle('setup:listModelCatalog', () => VOSK_MODEL_CATALOG.map(({ id, label }) => ({ id, label })))

  ipcMain.handle('setup:openModelsFolder', () => {
    const { modelsDir } = getPaths()
    mkdirSync(modelsDir, { recursive: true })
    shell.openPath(modelsDir)
  })

  // Imports the core packages and runs numpy through a large-array self-test: numpy 2.2.x on
  // Python 3.14 silently miscomputes big images (see videobeaux/utils/numpy_check.py), so an
  // "importable" numpy isn't proof it works. A failure here sends the user to Setup → Repair.
  const PYTHON_HEALTH_CHECK = [
    'import vosk, numpy as np, PIL',
    'n=480*640; i=np.arange(n); m=(i%7)>2; b=m.copy()',
    'p=np.empty(n,dtype=bool); p[0]=False; p[1:]=m[:-1]',
    '_=m&(~p|(i%640==0))',
    'assert (m==b).all(), "numpy %s miscomputes large arrays on this Python - Repair will update it" % np.__version__',
    'print("ok")'
  ].join('\n')

  async function environmentStatus() {
    const { ffmpegDir } = getPaths()
    const python = findPython()
    const ffmpegBin = ffmpegDir ? ffmpegBinaryPath(ffmpegDir, 'ffmpeg') : 'ffmpeg'
    const ffprobeBin = ffmpegDir ? ffmpegBinaryPath(ffmpegDir, 'ffprobe') : 'ffprobe'

    const check = (cmd, args) => new Promise(resolveCheck => {
      let proc
      try {
        proc = spawn(cmd, args, { windowsHide: true })
      } catch (err) {
        resolveCheck({ ok: false, detail: err.message })
        return
      }
      let out = ''
      proc.stdout?.on('data', d => { out += d.toString('utf8') })
      proc.stderr?.on('data', d => { out += d.toString('utf8') })
      // Report the LAST line: for a Python failure the first line is just
      // "Traceback (most recent call last):", the useful part is at the end.
      proc.on('close', code => {
        const lines = out.trim().split('\n').filter(Boolean)
        resolveCheck({ ok: code === 0, detail: (code === 0 ? lines[0] : lines[lines.length - 1]) || '' })
      })
      proc.on('error', err => resolveCheck({ ok: false, detail: err.message }))
    })

    const [pythonResult, ffmpegInfo, ffprobeResult] = await Promise.all([
      check(python, ['-c', PYTHON_HEALTH_CHECK]),
      inspectFfmpeg(ffmpegBin),
      check(ffprobeBin, ['-version'])
    ])
    const ffmpegResult = { ok: ffmpegInfo.ok, detail: ffmpegInfo.detail }
    // A source checkout also needs a *capable* ffmpeg (HDR tone mapping, caption burning and
    // text labels need zscale/libass/drawtext, which a plain system build often lacks); the
    // installer always bundles one.
    const ffmpegCapable = app.isPackaged || ffmpegInfo.capable

    return {
      python: pythonResult, ffmpeg: ffmpegResult, ffprobe: ffprobeResult, ffmpegCapable,
      ready: pythonResult.ok && ffmpegInfo.ok && ffprobeResult.ok && ffmpegCapable,
      // Source/dev checkouts can have the app repair itself; a packaged app ships everything.
      canRepair: !app.isPackaged,
      canInstallPython: !app.isPackaged
    }
  }

  ipcMain.handle('setup:checkEnvironment', () => environmentStatus())

  // One-click "make everything work" for source checkouts: Python + packages, then
  // a full-featured ffmpeg. Idempotent — only fixes what's missing/broken.
  ipcMain.handle('setup:repair', async (event, opts) => {
    if (app.isPackaged) return { ok: false, error: 'This install already includes everything it needs — try reinstalling the app.' }
    const { vbRoot } = getPaths()
    const send = (p) => event.sender.send('setup:installProgress', p)
    try {
      const before = await environmentStatus()
      const steps = []
      if (!before.python.ok || opts?.fresh) steps.push('python')
      if (!before.ffmpeg.ok || !before.ffprobe.ok || !before.ffmpegCapable) steps.push('ffmpeg')
      for (let i = 0; i < steps.length; i++) {
        const meta = { step: steps[i] === 'python' ? 'Setting up the video engine' : 'Getting video tools', stepIndex: i + 1, stepCount: steps.length }
        if (steps[i] === 'python') {
          const r = await installPython({
            vbRoot, runtime: pythonRuntime, fresh: !!opts?.fresh,
            onProgress: p => send({ ...meta, ...p })
          })
          if (!r.ok) return { ok: false, error: r.error }
        } else {
          await installFfmpeg({
            targetDir: managedFfmpegDir(vbRoot), runtime: ffmpegRuntime,
            onProgress: p => send({ ...meta, ...p })
          })
        }
      }
      const after = await environmentStatus()
      return after.ready
        ? { ok: true }
        : { ok: false, error: 'Setup finished but something still isn\'t working — press Repair to try again.' }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  })

  ipcMain.handle('setup:getInfo', () => ({ modelsDir: getPaths().modelsDir, packaged: app.isPackaged }))

  ipcMain.handle('setup:downloadModel', async (event, modelId) => {
    const model = VOSK_MODEL_CATALOG.find(m => m.id === modelId)
    if (!model) return { ok: false, error: `Unknown model: ${modelId}` }

    const { modelsDir } = getPaths()
    mkdirSync(modelsDir, { recursive: true })
    const zipPath = join(tmpdir(), `${model.id}-${randomUUID()}.zip`)
    const sendProgress = (payload) => event.sender.send('setup:downloadProgress', { modelId, ...payload })

    try {
      const res = await fetch(model.url)
      if (!res.ok || !res.body) throw new Error(`Download failed: HTTP ${res.status}`)
      const total = Number(res.headers.get('content-length')) || 0
      let received = 0

      const fileStream = createWriteStream(zipPath)
      const reader = res.body.getReader()
      // eslint-disable-next-line no-constant-condition
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        received += value.length
        await new Promise((res2, rej2) => fileStream.write(value, err => (err ? rej2(err) : res2())))
        sendProgress({ received, total, phase: 'downloading' })
      }
      await new Promise((res2, rej2) => fileStream.end(err => (err ? rej2(err) : res2())))

      sendProgress({ received, total, phase: 'extracting' })
      if (process.platform === 'win32') {
        await execFileAsync('powershell', [
          '-NoProfile', '-Command',
          `Expand-Archive -LiteralPath "${zipPath}" -DestinationPath "${modelsDir}" -Force`
        ])
      } else {
        await execFileAsync('unzip', ['-o', zipPath, '-d', modelsDir])
      }

      sendProgress({ received, total, phase: 'done' })
      return { ok: true }
    } catch (err) {
      return { ok: false, error: err.message }
    } finally {
      try { if (existsSync(zipPath)) unlinkSync(zipPath) } catch {}
    }
  })

  // ── Python subprocess helpers ────────────────────────────────────────────────

  /** Pick a temp-file extension that matches the step's output type. */
  function getTempExt(outputType) {
    switch (outputType) {
      case 'audio': return '.wav'
      case 'json':  return '.json'
      case 'image': return '.png'
      case 'text':  return '.txt'
      default:      return '.mp4'
    }
  }

  function findPython() {
    // 1. Prefer the bundled interpreter (packaged) / the app-managed or user venv (dev).
    //    findVenvPython also knows the Windows layout, where python-build-standalone
    //    puts python.exe at the folder root rather than under Scripts/.
    const { pythonHome } = getPaths()
    const found = findVenvPython(pythonHome)
    if (found) return found

    // 2. Fall back to system Python
    return process.platform === 'win32' ? 'python' : 'python3'
  }

  // Progress stat lines always contain a time=HH:MM:SS.ss field — true for
  // both ffmpeg's own default stderr stats (frame=... time=... speed=...)
  // and the videobeaux CLI's plain "time=...speed=..." progress lines
  // (emitted instead of a tqdm bar when stderr isn't a TTY, e.g. here).
  // Detected here in the main process so we can buffer/split correctly before
  // sending to the renderer, eliminating all chunking ambiguity.
  const STAT_LINE_RE = /\btime=\s*\d+:\d+:\d+/

  function runStep(python, args, cwd, sender) {
    return new Promise((resolve, reject) => {
      const { ffmpegDir, modelsDir } = getPaths()
      const proc = spawn(python, args, {
        cwd,
        env: {
          ...process.env,
          PYTHONUNBUFFERED: '1',
          PYTHONUTF8: '1',
          PYTHONIOENCODING: 'utf-8',
          // Programs that infer a model path themselves (e.g. auto_narrate.py's
          // kokoro-tts lookup) can't derive it from __file__ once they're
          // running from the staged/packaged videobeaux copy — that copy's
          // directory has no models/ sibling. getPaths().modelsDir is the
          // one place that already computes the right answer for both dev
          // and packaged (see the comment above getPaths()), so hand it
          // across the process boundary instead of leaving Python to guess.
          VIDEOBEAUX_MODELS_DIR: modelsDir,
          // Every program shells out to bare "ffmpeg"/"ffprobe" and resolves
          // them via PATH — prepending the bundled binaries' directory here
          // (packaged only; null in dev, which relies on system ffmpeg)
          // makes every one of those call sites use the bundled build with
          // zero changes to any Python file.
          ...(ffmpegDir ? { PATH: `${ffmpegDir}${delimiter}${process.env.PATH}` } : {})
        },
        windowsHide: true
      })
      currentProcess = proc

      proc.stdout.on('data', data => {
        sender.send('log:message', { text: data.toString('utf8'), type: 'stdout' })
      })

      // Buffer stderr so we never classify a partial line.
      // Split on \r OR \n so both TTY-style (\r) and pipe-style (\n / \r\n)
      // line endings are handled. This also normalizes tqdm-style \r-redrawn
      // bars (which would otherwise look like a new, ever-longer line each
      // update) down to one classified stat line per update. The last
      // (possibly incomplete) segment stays in the buffer until the next
      // chunk or process close.
      let stderrBuf = ''
      const flushStderr = (isFinal) => {
        const parts = stderrBuf.split(/[\r\n]+/)
        stderrBuf = isFinal ? '' : (parts.pop() ?? '')

        const normal = []
        for (const line of parts) {
          const trimmed = line.trim()
          if (!trimmed) continue
          if (STAT_LINE_RE.test(trimmed)) {
            // Send as a dedicated 'progress' type — renderer will parse time/speed
            sender.send('log:message', { text: trimmed, type: 'progress' })
          } else {
            normal.push(line)
          }
        }
        if (normal.length > 0) {
          sender.send('log:message', { text: normal.join('\n') + '\n', type: 'stderr' })
        }
      }

      proc.stderr.on('data', data => {
        stderrBuf += data.toString('utf8')
        flushStderr(false)
      })
      proc.on('close', code => {
        if (stderrBuf.trim()) flushStderr(true)
        currentProcess = null
        if (code === 0) resolve()
        else reject(new Error(`Process exited with code ${code}`))
      })
      proc.on('error', err => {
        currentProcess = null
        if (err.code === 'ENOENT') {
          reject(new Error(`Python not found. Make sure "python" or "python3" is on your PATH.`))
        } else {
          reject(err)
        }
      })
    })
  }

  let currentProcess = null

  /** Extension a batch task's final per-item file should get: whatever the
   *  chosen output path's own extension is for ordinary video outputs
   *  (matching single-file behavior), else the type's usual temp extension. */
  function finalItemExt(t, outputPath) {
    if (!t.outputType || t.outputType === 'video') return extname(outputPath) || '.mp4'
    return getTempExt(t.outputType)
  }

  function buildArgs(t, dest, resolveFn) {
    const args = [
      '-m', 'videobeaux.cli',
      '-P', t.program,
      '-i', resolveFn(t.primaryInput, `${t.program} main input`),
      '-o', dest,
      '-F'  // always overwrite temp + final output — a pre-flight confirm
            // (run:confirmOverwrite) already gated whether we got here at all
    ]

    // Extra video inputs (e.g. stack_2x's --input2), each resolved from an
    // upstream node's output or a manually picked literal path. Validation
    // in buildPipeline guarantees none of these ever reference a batch
    // producer, so resolveFn always returns a single path here.
    for (const ex of (t.extraInputs || [])) {
      args.push(`--${ex.argName}`, resolveFn(ex.ref, `${t.program} --${ex.argName}`))
    }

    // Remaining program-specific args
    for (const [key, value] of Object.entries(t.args || {})) {
      const v = String(value).trim()
      if (v !== '' && v !== 'false') {
        if (v === 'true') {
          args.push(`--${key}`)
        } else {
          args.push(`--${key}`, v)
        }
      }
    }
    return args
  }

  // ── Pipeline runner ─────────────────────────────────────────────────────────

  ipcMain.on('pipeline:run', async (event, pipeline) => {
    if (!pipeline || !Array.isArray(pipeline.tasks)) {
      event.sender.send('pipeline:error', { message: 'Outdated pipeline format — rebuild/reload the app.' })
      return
    }

    const { outputPath, sources, batchSources, tasks, finalTaskNodeId, finalProducesBatch } = pipeline
    const python = findPython()
    const { vbRoot } = getPaths()
    const tempEntries = []   // { path, kind: 'file' | 'dir' }

    const log = (text, type = 'system') => event.sender.send('log:message', { text, type })

    // nodeId -> absolute path (or, for a batch producer, an array of paths)
    // of that node's produced/provided media. Seeded with every Input node's
    // file; effect tasks add their own output as they complete, so
    // downstream tasks can look theirs up.
    const outputs = new Map(Object.entries(sources || {}))

    const resolve = (ref, what) => {
      if (ref.source === 'path') return ref.path
      const p = outputs.get(ref.nodeId)
      if (p === undefined) throw new Error(`Internal error: ${what} expects the output of ${ref.nodeId}, which has not been produced.`)
      return p
    }

    log(`videobeaux pipeline — ${tasks.length} step(s)\n`)
    for (const p of outputs.values()) log(`Source: ${p}\n`)
    log(`Output: ${outputPath}\n\n`)

    try {
      // Seed batch sources (folder-mode Input nodes) with their file lists.
      for (const [nodeId, folderPath] of Object.entries(batchSources || {})) {
        const files = listVideoFiles(folderPath)
        if (files.length === 0) throw new Error(`${folderPath}: no video files found in this folder.`)
        outputs.set(nodeId, files)
        log(`Source (batch): ${folderPath} — ${files.length} file(s)\n`)
      }

      let batchOutDir = null

      for (let i = 0; i < tasks.length; i++) {
        const t = tasks[i]
        const isFinal = t.nodeId === finalTaskNodeId

        if (!t.consumesBatch) {
          // ── Case A (ordinary) / Case B (native fan-out, e.g. qwikchop) ──
          const dest = isFinal
            ? outputPath
            : join(tmpdir(), `vb_${randomUUID()}${getTempExt(t.outputType)}`)

          if (!isFinal) {
            tempEntries.push(t.producesBatch
              ? { path: batchDirFor(dest), kind: 'dir' }
              : { path: dest, kind: 'file' })
          }

          const args = buildArgs(t, dest, resolve)
          log(`── Step ${i + 1} / ${tasks.length}: ${t.program}\n`)
          log(`   ${python} ${args.join(' ')}\n\n`, 'command')

          await runStep(python, args, vbRoot, event.sender)

          if (t.producesBatch) {
            // Native fan-out: the program wrote its own files into the
            // extension-stripped dest dir (extract_frames.py/qwikchop.py
            // convention) — discover them now that they exist.
            const dir = batchDirFor(dest)
            const files = listVideoFiles(dir)
            outputs.set(t.nodeId, files)
            log(`\n✓ Step ${i + 1} complete — ${files.length} file(s) in ${dir}\n\n`)
          } else {
            outputs.set(t.nodeId, dest)
            log(`\n✓ Step ${i + 1} complete\n\n`)
          }
        } else {
          // ── Case C: consumes a batch — run once per item ─────────────────
          const items = outputs.get(t.primaryInput.nodeId)

          if (isFinal) {
            batchOutDir = batchDirFor(outputPath)
            rmSync(batchOutDir, { recursive: true, force: true })
            mkdirSync(batchOutDir, { recursive: true })
          }

          const itemResolve = (item) => (ref, what) => {
            if (ref.source === 'node' && ref.nodeId === t.primaryInput.nodeId) return item
            return resolve(ref, what)
          }

          const usedNames = new Set()
          const results = []
          for (let j = 0; j < items.length; j++) {
            const item = items[j]
            let dest
            if (isFinal) {
              const base = parse(item).name
              const ext = finalItemExt(t, outputPath)
              let name = `${base}${ext}`
              let n = 2
              while (usedNames.has(name)) { name = `${base}_${n}${ext}`; n++ }
              usedNames.add(name)
              dest = join(batchOutDir, name)
            } else {
              dest = join(tmpdir(), `vb_${randomUUID()}${getTempExt(t.outputType)}`)
              tempEntries.push({ path: dest, kind: 'file' })
            }

            const args = buildArgs(t, dest, itemResolve(item))
            log(`── Step ${i + 1} / ${tasks.length}: ${t.program}  (item ${j + 1}/${items.length})\n`)
            log(`   ${python} ${args.join(' ')}\n\n`, 'command')

            await runStep(python, args, vbRoot, event.sender)
            results.push(dest)
          }

          log(`\n✓ Step ${i + 1} complete — ${results.length} file(s)\n\n`)
          outputs.set(t.nodeId, results)
        }
      }

      if (finalProducesBatch) {
        const outDir = batchDirFor(outputPath)
        const finalFiles = outputs.get(finalTaskNodeId) || []
        log(`\n✓ Pipeline complete → ${finalFiles.length} file(s) written to ${outDir}\n`, 'success')
        event.sender.send('pipeline:complete', { outputPath, batch: true, fileCount: finalFiles.length, outputDir: outDir })
      } else {
        log(`\n✓ Pipeline complete → ${outputPath}\n`, 'success')
        event.sender.send('pipeline:complete', { outputPath })
      }
    } catch (err) {
      log(`\n✗ ${err.message}\n`, 'error')
      event.sender.send('pipeline:error', { message: err.message })
    } finally {
      // Clean up intermediate temp files/dirs. An entry consumed by more than
      // one downstream task (fan-out) is read multiple times before this
      // runs, which is safe since cleanup only happens after the whole loop
      // ends.
      for (const { path: p, kind } of tempEntries) {
        try {
          if (!existsSync(p)) continue
          if (kind === 'dir') rmSync(p, { recursive: true, force: true })
          else unlinkSync(p)
        } catch {}
      }
    }
  })

  ipcMain.on('pipeline:cancel', () => {
    if (currentProcess) {
      currentProcess.kill('SIGTERM')
      currentProcess = null
    }
  })

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
