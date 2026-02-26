import { app, BrowserWindow, ipcMain, dialog } from 'electron'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import { spawn } from 'child_process'
import { unlinkSync, existsSync } from 'fs'
import { tmpdir } from 'os'
import { randomUUID } from 'crypto'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// In the built app: out/main/index.js -> out/ -> gui/ -> videobeaux-main/
const VB_ROOT = join(__dirname, '../../..')

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

app.whenReady().then(() => {
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

  // ── Program discovery ────────────────────────────────────────────────────────

  ipcMain.handle('programs:discover', () => {
    return new Promise((resolve) => {
      const python     = join(VB_ROOT, '.venv', 'Scripts', 'python.exe')
      const fallback   = process.platform === 'win32' ? 'python' : 'python3'
      const interpreter = existsSync(python) ? python : fallback
      const script     = join(VB_ROOT, 'gui', 'discover_programs.py')

      let output = ''
      const proc = spawn(interpreter, [script], {
        cwd: VB_ROOT,
        env: { ...process.env, PYTHONUTF8: '1', PYTHONIOENCODING: 'utf-8' },
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
    // 1. Prefer the venv bundled with the project
    const venvPython = process.platform === 'win32'
      ? join(VB_ROOT, '.venv', 'Scripts', 'python.exe')
      : join(VB_ROOT, '.venv', 'bin', 'python')
    if (existsSync(venvPython)) return venvPython

    // 2. Fall back to system Python
    return process.platform === 'win32' ? 'python' : 'python3'
  }

  // FFmpeg progress stat lines always contain  frame=<digits>.
  // Detected here in the main process so we can buffer/split correctly before
  // sending to the renderer, eliminating all chunking ambiguity.
  const STAT_LINE_RE = /\bframe=\s*\d+/

  function runStep(python, args, cwd, sender) {
    return new Promise((resolve, reject) => {
      const proc = spawn(python, args, {
        cwd,
        env: { ...process.env, PYTHONUNBUFFERED: '1', PYTHONUTF8: '1', PYTHONIOENCODING: 'utf-8' },
        windowsHide: true
      })
      currentProcess = proc

      proc.stdout.on('data', data => {
        sender.send('log:message', { text: data.toString('utf8'), type: 'stdout' })
      })

      // Buffer stderr so we never classify a partial line.
      // Split on \r OR \n so both TTY-style (\r) and pipe-style (\n / \r\n)
      // line endings are handled.  The last (possibly incomplete) segment stays
      // in the buffer until the next chunk or process close.
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

  // ── Pipeline runner ─────────────────────────────────────────────────────────

  ipcMain.on('pipeline:run', async (event, pipeline) => {
    const { inputPath, outputPath, steps } = pipeline
    const python = findPython()
    const tempFiles = []

    const log = (text, type = 'system') => event.sender.send('log:message', { text, type })

    log(`videobeaux pipeline — ${steps.length} step(s)\n`)
    log(`Input:  ${inputPath}\n`)
    log(`Output: ${outputPath}\n\n`)

    let currentInput = inputPath

    try {
      for (let i = 0; i < steps.length; i++) {
        const step = steps[i]
        const isLast = i === steps.length - 1
        const ext = getTempExt(step.outputType)
        const currentOutput = isLast
          ? outputPath
          : join(tmpdir(), `vb_${randomUUID()}${ext}`)

        if (!isLast) tempFiles.push(currentOutput)

        const args = [
          '-m', 'videobeaux.cli',
          '-P', step.program,
          '-i', currentInput,
          '-o', currentOutput,
          '-F'  // always overwrite temp + final output
        ]

        // Append program-specific args
        for (const [key, value] of Object.entries(step.args || {})) {
          const v = String(value).trim()
          if (v !== '' && v !== 'false') {
            if (v === 'true') {
              args.push(`--${key}`)
            } else {
              args.push(`--${key}`, v)
            }
          }
        }

        log(`── Step ${i + 1} / ${steps.length}: ${step.program}\n`)
        log(`   ${python} ${args.join(' ')}\n\n`, 'command')

        await runStep(python, args, VB_ROOT, event.sender)

        log(`\n✓ Step ${i + 1} complete\n\n`)
        currentInput = currentOutput
      }

      log(`\n✓ Pipeline complete → ${outputPath}\n`, 'success')
      event.sender.send('pipeline:complete', { outputPath })
    } catch (err) {
      log(`\n✗ ${err.message}\n`, 'error')
      event.sender.send('pipeline:error', { message: err.message })
    } finally {
      // Clean up intermediate temp files
      for (const f of tempFiles) {
        try { if (existsSync(f)) unlinkSync(f) } catch {}
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
