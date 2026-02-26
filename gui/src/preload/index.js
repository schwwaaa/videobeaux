import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  // File dialogs
  openFile:      (filters) => ipcRenderer.invoke('dialog:openFile', filters),
  openDirectory: ()        => ipcRenderer.invoke('dialog:openDirectory'),
  saveFile:      (opts)    => ipcRenderer.invoke('dialog:saveFile', opts || {}),

  // Program discovery — returns Promise<{ [programId]: { description, args[] } }>
  discoverPrograms: () => ipcRenderer.invoke('programs:discover'),

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
