import { existsSync, mkdirSync, readFileSync, renameSync, rmSync, writeFileSync } from 'fs'
import { join } from 'path'
import { spawn } from 'child_process'
import { tmpdir } from 'os'
import { downloadToFile } from './download.js'

/**
 * One-click Python setup for source/dev checkouts.
 *
 * Downloads the same pinned python-build-standalone interpreter the installer
 * bundles (see gui/python-runtime.json), extracts it to <repo>/venv — where
 * the app already looks — and pip-installs requirements.txt into it. Pure
 * Node with injectable pieces so it can be tested without Electron.
 */

let busy = false

export function findVenvPython(venvDir, platform = process.platform) {
  const candidates = platform === 'win32'
    ? [join(venvDir, 'python.exe'), join(venvDir, 'Scripts', 'python.exe')]
    : [join(venvDir, 'bin', 'python3')]
  return candidates.find(existsSync) || null
}

export function runtimeAssetKey(platform = process.platform, arch = process.arch) {
  return `${platform}_${arch === 'arm64' ? 'arm64' : 'x64'}`
}

/** Run a command, calling onLine for every output line; resolves { code, tail }. */
function run(cmd, args, { cwd, onLine } = {}) {
  return new Promise((resolve, reject) => {
    const proc = spawn(cmd, args, {
      cwd,
      windowsHide: true,
      env: { ...process.env, PYTHONUTF8: '1', PYTHONIOENCODING: 'utf-8', PIP_DISABLE_PIP_VERSION_CHECK: '1' }
    })
    const tail = []
    let buf = ''
    const feed = (chunk) => {
      buf += chunk.toString('utf8')
      const lines = buf.split(/\r?\n|\r/)
      buf = lines.pop() ?? ''
      for (const line of lines) {
        if (!line.trim()) continue
        tail.push(line)
        if (tail.length > 12) tail.shift()
        onLine?.(line)
      }
    }
    proc.stdout.on('data', feed)
    proc.stderr.on('data', feed)
    proc.on('error', reject)
    proc.on('close', code => {
      if (buf.trim()) { tail.push(buf); onLine?.(buf) }
      resolve({ code, tail })
    })
  })
}

/**
 * @param {object} o
 * @param {string} o.vbRoot        repo root (contains requirements.txt; venv/ goes here)
 * @param {object} o.runtime       contents of gui/python-runtime.json
 * @param {boolean} [o.fresh]      move an existing venv aside and start over
 * @param {(p: object) => void} [o.onProgress]  { phase, message?, received?, total?, line? }
 * @param {string} [o.verifyImports] Python statement proving the packages work
 * @returns {Promise<{ok: true, python: string} | {ok: false, error: string}>}
 */
export async function installPython({
  vbRoot, runtime, fresh = false, onProgress = () => {},
  platform = process.platform, arch = process.arch,
  requirementsPath = join(vbRoot, 'requirements.txt'),
  verifyImports = 'import vosk, numpy, PIL',
  download = downloadToFile
}) {
  if (busy) return { ok: false, error: 'Python setup is already running.' }
  busy = true
  const venvDir = join(vbRoot, 'venv')
  const stamp = Date.now()
  let created = false
  const tmpFiles = []
  try {
    if (fresh && existsSync(venvDir)) {
      renameSync(venvDir, `${venvDir}.old-${stamp}`)
      onProgress({ phase: 'prepare', message: 'Moved the old Python folder aside (venv.old-*).' })
    }

    let py = findVenvPython(venvDir, platform)
    if (!py) {
      const key = runtimeAssetKey(platform, arch)
      const asset = runtime.assets[key]
      if (!asset) throw new Error(`No Python build is available for this platform (${key}).`)
      const url = `${runtime.urlBase}/${runtime.release}/${asset}`
      const tarball = join(tmpdir(), `videobeaux-python-${stamp}.tar.gz`)
      tmpFiles.push(tarball)

      onProgress({ phase: 'python-download', message: `Downloading Python ${runtime.version}…`, received: 0, total: 0 })
      await download(url, tarball, {
        onProgress: ({ received, total }) =>
          onProgress({ phase: 'python-download', message: `Downloading Python ${runtime.version}…`, received, total })
      })

      onProgress({ phase: 'python-unpack', message: 'Unpacking Python…' })
      const extractDir = join(vbRoot, `.python-extract-${stamp}`)
      tmpFiles.push(extractDir)
      mkdirSync(extractDir, { recursive: true })
      const tar = await run('tar', ['-xzf', tarball, '-C', extractDir])
      if (tar.code !== 0) throw new Error(`Could not unpack Python: ${tar.tail.slice(-2).join(' ')}`)

      // A venv/ folder with no interpreter in it is unusable — set it aside rather than overwrite it.
      if (existsSync(venvDir)) renameSync(venvDir, `${venvDir}.old-${stamp}`)
      renameSync(join(extractDir, 'python'), venvDir)
      created = true
      py = findVenvPython(venvDir, platform)
      if (!py) throw new Error('Python was unpacked but its interpreter could not be found.')
    }

    // requirements.txt's "-e ./videobeaux" line is dev-only (editable install);
    // videobeaux runs from the repo root, so it isn't needed here.
    const reqs = readFileSync(requirementsPath, 'utf8')
      .split('\n').filter(l => !l.trim().startsWith('-e ')).join('\n')
    const reqFile = join(tmpdir(), `videobeaux-requirements-${stamp}.txt`)
    writeFileSync(reqFile, reqs)
    tmpFiles.push(reqFile)

    onProgress({ phase: 'pip', message: 'Installing packages — this is the long part, one time only…' })
    const pip = await run(py, ['-m', 'pip', 'install', '--progress-bar', 'off', '-r', reqFile], {
      cwd: vbRoot,
      onLine: line => onProgress({ phase: 'pip', line })
    })
    if (pip.code !== 0) {
      throw new Error(`Installing packages failed:\n${pip.tail.slice(-4).join('\n')}`)
    }

    onProgress({ phase: 'verify', message: 'Checking everything works…' })
    const check = await run(py, ['-c', verifyImports], { cwd: vbRoot })
    if (check.code !== 0) {
      throw new Error(`Packages installed but a check failed: ${check.tail.slice(-1)[0] || 'unknown error'}`)
    }

    onProgress({ phase: 'done', message: 'Python is ready.' })
    return { ok: true, python: py }
  } catch (err) {
    // Only remove what this run built itself; a pre-existing venv is left alone.
    if (created) { try { rmSync(venvDir, { recursive: true, force: true }) } catch { /* ignore */ } }
    return { ok: false, error: err.message }
  } finally {
    for (const f of tmpFiles) { try { rmSync(f, { recursive: true, force: true }) } catch { /* ignore */ } }
    busy = false
  }
}
