// Stubbed Electron bridge so the real renderer runs in a plain browser (screenshots / checks).
(function () {
  const q = new URLSearchParams(location.search)
  const demo = q.get('demo')
  if (demo) { try { const x = new XMLHttpRequest(); x.open('GET', '/__ws/' + demo + '.json', false); x.send(); if (x.status === 200) { localStorage.setItem('vb.workspace.v1', x.responseText); localStorage.removeItem('vb.workspace.off') } } catch (e) {} }
  else { try { localStorage.removeItem('vb.workspace.v1') } catch (e) {} }
  const settings = { setupSeen: true, look: q.get('look') || 'classic', theme: q.get('theme') || undefined }
  const done = (v) => () => Promise.resolve(v)
  const api = {
    openFile: done(null), openDirectory: done(null), saveFile: done(null), savePreset: done({ ok: true }), loadPreset: done(null),
    getSettings: () => Promise.resolve(settings), setSettings: done({}),
    discoverPrograms: () => fetch('/__programs.json').then(r => r.json()),
    listFonts: () => fetch('/__fonts.json').then(r => r.json()),
    listModels: done([]), listVideoFiles: done([]), listOllamaModels: done([]), listKokoroVoices: done([]),
    saveSnapshot: done(null), artStatus: done({ generated: false }), artGenerate: done({}), artCancel: done({}), artReset: done({}),
    onArtProgress: () => () => {}, grabFrame: done(null), mediaUrl: (p) => '/__file?p=' + encodeURIComponent(p), pathForFile: () => '', readImageDataUrl: done(null),
    probeMedia: done(null), writeLayout: done(null), readLayout: done(null), confirmOverwrite: done({ proceed: true }),
    listModelCatalog: done([]), checkEnvironment: done({ ready: true, python: { ok: true }, ffmpeg: { ok: true }, ffprobe: { ok: true }, ffmpegCapable: true }), downloadModel: done({}), openModelsFolder: done({}),
    checkOptional: done({}), repairSetup: done({}), getSetupInfo: done({}), onInstallProgress: () => () => {},
    downloadKokoro: done({}), downloadBgModel: done({}), openExternal: done({}), onDownloadProgress: () => () => {}
  }
  // fake pipeline run: ?run=1 clicks Run, ?keys=j,b presses ⌘J / ⌘B after load (collapse console / sidebar)
  const L = { log: [], done: [], err: [] }
  api.onLogMessage = (cb) => { L.log.push(cb); return () => {} }
  api.onPipelineComplete = (cb) => { L.done.push(cb); return () => {} }
  api.onPipelineError = (cb) => { L.err.push(cb); return () => {} }
  const emit = (t, text, type) => setTimeout(() => L.log.forEach(f => f({ text, type: type || 'log' })), t)
  api.runPipeline = (p) => {
    const names = (p.tasks || []).map(t => t.program || t.name || 'step')
    const n = names.length || 3
    names.forEach((nm, i) => {
      const t0 = 150 + i * 700
      emit(t0, `\n── Step ${i + 1} / ${n}: ${nm}\n`)
      for (let k = 1; k <= 4; k++) emit(t0 + k * 130, `frame=  ${k * 60} fps= 30 q=-1.0 size=  ${k * 400}kB time=00:00:0${k}.00 bitrate= 900kbits/s speed=${(1.2 + k / 4).toFixed(1)}x`, 'progress')
    })
    setTimeout(() => L.done.forEach(f => f({})), 150 + n * 700 + 300)
  }
  if (q.get('search')) setTimeout(() => { const i = document.querySelector('input[placeholder^="Search"]'); if (i) { Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(i, q.get('search')); i.dispatchEvent(new Event('input', { bubbles: true })) } }, 900)
  if (q.get('click')) setTimeout(() => { const re = new RegExp(q.get('click'), 'i'); const b = [...document.querySelectorAll('button')].find(x => re.test(x.textContent)); b && b.click() }, 1500)
  if (q.get('fit')) setTimeout(() => { const b = document.querySelector('.react-flow__controls-fitview'); b && b.click() }, 3000)
  if (q.get('run')) setTimeout(() => { const b = [...document.querySelectorAll('button')].find(x => /(^|\s)run(\s|$)/i.test(x.textContent.replace(/[^A-Za-z ]/g, " "))); b && b.click() }, 1200)
  if (q.get('keys')) q.get('keys').split(',').forEach((k, i) => setTimeout(() => window.dispatchEvent(new KeyboardEvent('keydown', k === 'sl' ? { key: 'L', shiftKey: true, metaKey: true, bubbles: true } : { key: k, metaKey: true, bubbles: true })), +(q.get('keyat') || 1500) + i * 300))
  window.electronAPI = new Proxy(api, { get: (t, k) => (k in t ? t[k] : (String(k).startsWith('on') ? (() => () => {}) : (() => Promise.resolve(null)))) })
})()
