"use strict";
const electron = require("electron");
electron.contextBridge.exposeInMainWorld("electronAPI", {
  // File dialogs
  openFile: (filters) => electron.ipcRenderer.invoke("dialog:openFile", filters),
  openDirectory: () => electron.ipcRenderer.invoke("dialog:openDirectory"),
  saveFile: (opts) => electron.ipcRenderer.invoke("dialog:saveFile", opts || {}),
  // Program discovery — returns Promise<{ [programId]: { description, args[] } }>
  discoverPrograms: () => electron.ipcRenderer.invoke("programs:discover"),
  // Pipeline execution
  runPipeline: (pipeline) => electron.ipcRenderer.send("pipeline:run", pipeline),
  cancelPipeline: () => electron.ipcRenderer.send("pipeline:cancel"),
  // Event listeners (return cleanup functions)
  onLogMessage: (cb) => {
    const handler = (_, msg) => cb(msg);
    electron.ipcRenderer.on("log:message", handler);
    return () => electron.ipcRenderer.removeListener("log:message", handler);
  },
  onPipelineComplete: (cb) => {
    const handler = (_, data) => cb(data);
    electron.ipcRenderer.on("pipeline:complete", handler);
    return () => electron.ipcRenderer.removeListener("pipeline:complete", handler);
  },
  onPipelineError: (cb) => {
    const handler = (_, data) => cb(data);
    electron.ipcRenderer.on("pipeline:error", handler);
    return () => electron.ipcRenderer.removeListener("pipeline:error", handler);
  }
});
