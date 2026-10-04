import { contextBridge, ipcRenderer, webUtils } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  // File dialogs
  openFile:      (filters) => ipcRenderer.invoke('dialog:openFile', filters),
  openDirectory: ()        => ipcRenderer.invoke('dialog:openDirectory'),
  saveFile:      (opts)    => ipcRenderer.invoke('dialog:saveFile', opts || {}),

  // Preset (canvas snapshot) save/load
  savePreset: (data, defaultName) => ipcRenderer.invoke('presets:save', { data, defaultName }),
  loadPreset: () => ipcRenderer.invoke('presets:load'),

  // App settings (theme, shadow style) — small persisted prefs
  getSettings: () => ipcRenderer.invoke('settings:get'),
  setSettings: (settings) => ipcRenderer.invoke('settings:set', settings),

  // Program discovery — returns Promise<{ [programId]: { description, args[] } }>
  discoverPrograms: () => ipcRenderer.invoke('programs:discover'),

  // Model picker — returns Promise<{ name, path }[]>, scanned fresh each call
  listModels: () => ipcRenderer.invoke('models:list'),

  // Batch — video files in a folder (folder-mode Input's live count, and
  // reused by the pipeline runner for batch-source seeding)
  listVideoFiles: (dirPath) => ipcRenderer.invoke('files:listVideos', dirPath),

  // Ollama model picker — optional path only (auto_narrate's --topic mode).
  // Returns Promise<{name, size}[]>, empty if Ollama isn't reachable.
  listOllamaModels: () => ipcRenderer.invoke('ollama:listModels'),

  // kokoro-tts voice picker — queries kokoro-tts's own --help-voices.
  // Returns Promise<string[]>, empty if kokoro-tts isn't installed.
  listKokoroVoices: () => ipcRenderer.invoke('kokoro:listVoices'),

  // Helper windows (Lagkage layout editor, ...)
  // Electron 32 removed File.path — this is how a dropped File maps back to its location on disk.
  pathForFile: (file) => { try { return webUtils.getPathForFile(file) } catch { return '' } },
  readImageDataUrl: (path, layoutPath) => ipcRenderer.invoke('files:readDataUrl', { path, layoutPath }),
  probeMedia: (path, layoutPath) => ipcRenderer.invoke('media:probe', { path, layoutPath }),
  writeLayout: (name, json) => ipcRenderer.invoke('layouts:write', { name, json }),
  readLayout: (path) => ipcRenderer.invoke('layouts:read', path),

  // Pre-flight overwrite check — resolves { proceed: boolean }
  confirmOverwrite: (opts) => ipcRenderer.invoke('run:confirmOverwrite', opts),

  // First-run setup — environment health check + Vosk model download
  listModelCatalog: () => ipcRenderer.invoke('setup:listModelCatalog'),
  checkEnvironment: () => ipcRenderer.invoke('setup:checkEnvironment'),
  downloadModel: (modelId) => ipcRenderer.invoke('setup:downloadModel', modelId),
  openModelsFolder: () => ipcRenderer.invoke('setup:openModelsFolder'),
  checkOptional: () => ipcRenderer.invoke('setup:checkOptional'),
  repairSetup: (opts) => ipcRenderer.invoke('setup:repair', opts),
  getSetupInfo: () => ipcRenderer.invoke('setup:getInfo'),
  onInstallProgress: (cb) => {
    const handler = (_, data) => cb(data)
    ipcRenderer.on('setup:installProgress', handler)
    return () => ipcRenderer.removeListener('setup:installProgress', handler)
  },
  downloadKokoro: () => ipcRenderer.invoke('setup:downloadKokoro'),
  downloadBgModel: (id) => ipcRenderer.invoke('setup:downloadBgModel', id),
  openExternal: (key) => ipcRenderer.invoke('shell:openExternal', key),
  onDownloadProgress: (cb) => {
    const handler = (_, data) => cb(data)
    ipcRenderer.on('setup:downloadProgress', handler)
    return () => ipcRenderer.removeListener('setup:downloadProgress', handler)
  },

  // Pipeline execution
  runPipeline: (pipeline) => ipcRenderer.send('pipeline:run', pipeline),
  cancelPipeline: () => ipcRenderer.send('pipeline:cancel'),

  // Event listeners (return cleanup functions)
  onLogMessage: (cb) => {
    const handler = (_, msg) => cb(msg)
    ipcRenderer.on('log:message', handler)
    return () => ipcRenderer.removeListener('log:message', handler)
  },
  onPipelineComplete: (cb) => {
    const handler = (_, data) => cb(data)
    ipcRenderer.on('pipeline:complete', handler)
    return () => ipcRenderer.removeListener('pipeline:complete', handler)
  },
  onPipelineError: (cb) => {
    const handler = (_, data) => cb(data)
    ipcRenderer.on('pipeline:error', handler)
    return () => ipcRenderer.removeListener('pipeline:error', handler)
  }
})
