import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useSettings } from '../SettingsContext'

const styles = {
  overlay: {
    position: 'fixed', inset: 0, background: 'rgba(8,8,8,0.55)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 1000, padding: 24
  },
  panel: {
    background: 'var(--paper)', border: 'var(--border)', borderRadius: 'var(--radius)',
    boxShadow: 'var(--shadow)', maxWidth: 580, width: '100%',
    maxHeight: '90vh', overflowY: 'auto', padding: '24px 28px'
  },
  title: { fontFamily: 'var(--font-display)', fontSize: 22, color: 'var(--ink)', marginBottom: 4 },
  subtitle: { fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--muted-dim)', marginBottom: 18 },
  sectionTitle: {
    fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 12, letterSpacing: '0.06em',
    textTransform: 'uppercase', color: 'var(--ink)', marginBottom: 8, marginTop: 24
  },
  card: {
    border: 'var(--border)', borderRadius: 'var(--radius-sm)', padding: '12px 14px',
    marginBottom: 8, background: 'var(--paper)'
  },
  row: { display: 'flex', alignItems: 'center', gap: 10 },
  badge: (ok) => ({
    width: 18, height: 18, borderRadius: '50%', flexShrink: 0,
    background: ok === null ? 'var(--gray)' : ok ? 'var(--lime-bright)' : 'var(--coral)',
    border: '2px solid var(--ink)', display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: 10, fontWeight: 700
  }),
  mono: { fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--muted-dim)' },
  button: (accent) => ({
    background: accent || 'var(--yellow)', color: 'var(--on-color)',
    padding: '8px 16px', borderRadius: 'var(--radius-sm)',
    fontFamily: 'var(--font-display)', fontSize: 11,
    border: 'var(--border)', boxShadow: 'var(--shadow-sm)', cursor: 'pointer', flexShrink: 0
  }),
  buttonSmall: (accent) => ({
    background: accent || 'var(--paper)', color: accent ? 'var(--on-color)' : 'var(--ink)',
    padding: '5px 10px', borderRadius: 'var(--radius-sm)',
    fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 10,
    border: 'var(--border)', boxShadow: 'var(--shadow-sm)', cursor: 'pointer', flexShrink: 0
  }),
  progressTrack: {
    height: 8, background: 'var(--paper-dim)', border: '2px solid var(--ink)',
    borderRadius: 4, overflow: 'hidden', marginTop: 6
  },
  footer: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12,
    marginTop: 24, paddingTop: 16, borderTop: '2px dashed var(--gray)'
  }
}

function pressable(e, down) {
  e.currentTarget.style.boxShadow = down ? 'none' : 'var(--shadow-sm)'
  e.currentTarget.style.transform = down ? 'translate(3px, 3px)' : 'none'
}
const press = (disabled) => ({
  onMouseDown: e => !disabled && pressable(e, true),
  onMouseUp: e => pressable(e, false),
  onMouseLeave: e => pressable(e, false)
})

function Badge({ ok }) {
  return <div style={styles.badge(ok)}>{ok === null ? '' : ok ? '✓' : '✕'}</div>
}

function Bar({ fraction }) {
  return (
    <div style={styles.progressTrack}>
      {fraction == null
        ? <div style={{ height: '100%', width: '35%', background: 'var(--cyan)', animation: 'vb-indeterminate 1.4s ease-in-out infinite' }} />
        : <div style={{ height: '100%', background: 'var(--cyan)', transition: 'width 0.2s', width: `${Math.min(100, fraction * 100)}%` }} />}
    </div>
  )
}

const mb = (n) => `${Math.round(n / 1e6)} MB`

export default function SetupScreen({ onClose }) {
  const { setSetupSeen } = useSettings()

  // ── Core engine status (Python, video tools) — shown as one simple status ──
  const [env, setEnv] = useState(null)               // null while the first check runs
  const [repairing, setRepairing] = useState(false)
  const [repairInfo, setRepairInfo] = useState(null)  // latest progress event
  const [repairError, setRepairError] = useState(null)
  const autoTried = useRef(false)
  const failedBefore = useRef(false)

  const checkEnv = useCallback(async () => {
    const r = await window.electronAPI.checkEnvironment()
    setEnv(r)
    return r
  }, [])

  const runRepair = useCallback(async () => {
    setRepairing(true)
    setRepairError(null)
    setRepairInfo({ message: 'Starting…' })
    const result = await window.electronAPI.repairSetup({ fresh: failedBefore.current })
    setRepairing(false)
    if (result.ok) {
      failedBefore.current = false
      // Program discovery ran before the engine existed — reload so it runs again.
      window.location.reload()
    } else {
      failedBefore.current = true
      setRepairInfo(null)
      setRepairError(result.error)
      checkEnv()
    }
  }, [checkEnv])

  // ── Optional local-AI features ──
  const [info, setInfo] = useState({ modelsDir: '' })
  const [catalog, setCatalog] = useState([])
  const [installedModels, setInstalledModels] = useState([])
  const [optional, setOptional] = useState(null)
  const [wantSpeech, setWantSpeech] = useState(false)
  const [speechId, setSpeechId] = useState(null)
  const [wantVoice, setWantVoice] = useState(false)
  const [wantBgFast, setWantBgFast] = useState(false)
  const [wantBgPeople, setWantBgPeople] = useState(false)
  const [aiBusy, setAiBusy] = useState(false)
  const [aiStatus, setAiStatus] = useState(null)      // { label, received, total }
  const [aiError, setAiError] = useState(null)

  const refreshAi = useCallback(async () => {
    const [models, opt] = await Promise.all([window.electronAPI.listModels(), window.electronAPI.checkOptional()])
    setInstalledModels(models.map(m => m.name))
    setOptional(opt)
  }, [])

  useEffect(() => {
    checkEnv().then(r => {
      // Fresh clone / broken engine: just fix it — no button hunt needed.
      if (r && !r.ready && r.canRepair && !autoTried.current) {
        autoTried.current = true
        runRepair()
      }
    })
    window.electronAPI.getSetupInfo().then(setInfo)
    window.electronAPI.listModelCatalog().then(list => {
      setCatalog(list)
      const rec = list.find(m => /recommended/i.test(m.label)) || list[0]
      if (rec) setSpeechId(rec.id)
    })
    refreshAi()
    const offInstall = window.electronAPI.onInstallProgress(p => setRepairInfo(prev => ({ ...(prev || {}), ...p, line: p.line ?? (p.message ? null : prev?.line) })))
    const offDl = window.electronAPI.onDownloadProgress(({ modelId, received, total, phase }) =>
      setAiStatus(prev => ({ ...(prev || {}), received, total, phase, modelId })))
    return () => { offInstall(); offDl() }
  }, [checkEnv, runRepair, refreshAi])

  const speechInstalled = catalog.some(m => installedModels.includes(m.id))
  const voiceInstalled = !!optional?.kokoro?.models?.ok
  const bgModels = optional?.bgremove?.models || {}
  const bgInstalled = (id) => !!bgModels[id]?.ok
  const anySelected = (wantSpeech && !speechInstalled) || (wantVoice && !voiceInstalled) ||
    (wantBgFast && !bgInstalled('u2netp')) || (wantBgPeople && !bgInstalled('u2net_human_seg'))
  const engineReady = !!env?.ready

  const finish = useCallback(() => { setSetupSeen(true); onClose() }, [setSetupSeen, onClose])

  const handleContinue = async () => {
    setAiError(null)
    setAiBusy(true)
    try {
      if (wantSpeech && !speechInstalled && speechId) {
        const label = catalog.find(m => m.id === speechId)?.label?.split('—')[0].trim() || 'speech model'
        setAiStatus({ label: `Downloading the ${label} speech model…`, received: 0, total: 0 })
        const r = await window.electronAPI.downloadModel(speechId)
        if (!r.ok) throw new Error(`Speech model: ${r.error}`)
      }
      if (wantVoice && !voiceInstalled) {
        setAiStatus({ label: 'Downloading the narration voice…', received: 0, total: 0 })
        const r = await window.electronAPI.downloadKokoro()
        if (!r.ok) throw new Error(`Narration voice: ${r.error}`)
      }
      for (const [want, id, label] of [[wantBgFast, 'u2netp', 'the background-removal model'], [wantBgPeople, 'u2net_human_seg', 'the people background-removal model']]) {
        if (want && !bgInstalled(id)) {
          setAiStatus({ label: `Downloading ${label}…`, received: 0, total: 0 })
          const r = await window.electronAPI.downloadBgModel(id)
          if (!r.ok) throw new Error(`Background removal (${id}): ${r.error}`)
        }
      }
      setAiStatus(null)
      setAiBusy(false)
      finish()
    } catch (err) {
      setAiBusy(false)
      setAiStatus(null)
      setAiError(err.message)
      refreshAi()
    }
  }

  const speechOptions = catalog
  const stepLine = repairInfo?.stepCount > 1 ? `Step ${repairInfo.stepIndex} of ${repairInfo.stepCount} · ` : ''
  const dlFraction = (i) => (i && i.total > 0 ? i.received / i.total : null)

  return (
    <div style={styles.overlay}>
      <div style={styles.panel}>
        <div style={styles.title}>Welcome to Videobeaux</div>
        <div style={styles.subtitle}>Let's make sure everything's ready before you dive in.</div>

        {/* ── Status ─────────────────────────────────────────────────────── */}
        <div style={styles.card}>
          {env === null ? (
            <div style={styles.row}><Badge ok={null} /> Checking…</div>
          ) : repairing ? (
            <div>
              <div style={styles.row}><Badge ok={null} /> <b>Getting things ready…</b></div>
              <div style={{ ...styles.mono, marginTop: 6, color: 'var(--ink)' }}>
                {stepLine}{repairInfo?.step || 'Setting up'}
              </div>
              <div style={styles.mono}>{repairInfo?.message}</div>
              <Bar fraction={repairInfo?.phase?.endsWith('download') ? dlFraction(repairInfo) : null} />
              {repairInfo?.line && (
                <div style={{ ...styles.mono, marginTop: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {repairInfo.line}
                </div>
              )}
              <div style={{ ...styles.mono, marginTop: 6 }}>
                The first time takes a few minutes and needs an internet connection. It only happens once.
              </div>
            </div>
          ) : env.ready ? (
            <div style={styles.row}><Badge ok={true} /> <b>Videobeaux is ready.</b></div>
          ) : (
            <div>
              <div style={styles.row}>
                <Badge ok={false} />
                <span style={{ flex: 1 }}>
                  <b>Something needs fixing.</b>{' '}
                  {env.canRepair ? 'Press Repair and Videobeaux will sort it out.' : 'Please reinstall Videobeaux.'}
                </span>
                {env.canRepair && (
                  <button style={styles.button('var(--cyan)')} onClick={runRepair} {...press(false)}>Repair</button>
                )}
              </div>
              {repairError && (
                <div style={{ fontSize: 11, color: 'var(--coral)', fontFamily: 'var(--font-mono)', marginTop: 8, whiteSpace: 'pre-wrap' }}>
                  ❌ {repairError}
                </div>
              )}
            </div>
          )}
          {env && !repairing && (
            <details style={{ marginTop: 8 }}>
              <summary style={{ ...styles.mono, cursor: 'pointer' }}>Technical details</summary>
              <div style={{ ...styles.mono, marginTop: 4, whiteSpace: 'pre-wrap' }}>
                {`Engine: ${env.python.ok ? 'ok' : env.python.detail || 'not ready'}
Video tools: ${env.ffmpeg.ok && env.ffprobe.ok ? (env.ffmpegCapable ? 'ok' : 'present but missing features') : 'not found'}`}
              </div>
              <button style={{ ...styles.buttonSmall(), marginTop: 6 }} onClick={checkEnv} {...press(false)}>Check again</button>
            </details>
          )}
        </div>

        {/* ── Local AI (opt-in) ──────────────────────────────────────────── */}
        <div style={styles.sectionTitle}>Local AI features — optional</div>
        <div style={{ fontSize: 13, color: 'var(--ink)', lineHeight: 1.5, marginBottom: 10 }}>
          Some advanced Videobeaux modes use AI — for transcription, captions and narration. It all runs
          <b> on your computer, offline</b>: nothing you make is ever uploaded. By pressing Continue, the models you
          tick below are downloaded once to:
          <div style={{ ...styles.mono, margin: '6px 0', color: 'var(--ink)', wordBreak: 'break-all' }}>
            {info.modelsDir || '…'}
          </div>
          After that they work with no internet connection. You can skip this and add them later from Setup.
        </div>

        <div style={styles.card}>
          <label style={{ ...styles.row, cursor: speechInstalled ? 'default' : 'pointer' }}>
            {speechInstalled
              ? <Badge ok={true} />
              : <input type="checkbox" checked={wantSpeech} onChange={e => setWantSpeech(e.target.checked)} disabled={aiBusy}
                  style={{ width: 18, height: 18, accentColor: 'var(--slider)' }} />}
            <span style={{ flex: 1 }}>
              <b>Speech recognition</b> — turns spoken words into text
              <div style={styles.mono}>Used by transcription, caption and “find the spoken word” modes{speechInstalled ? ' · installed' : ''}</div>
            </span>
          </label>
          {wantSpeech && !speechInstalled && speechOptions.length > 0 && (
            <div style={{ marginTop: 8, paddingLeft: 28, display: 'flex', flexDirection: 'column', gap: 4 }}>
              {speechOptions.map(m => (
                <label key={m.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, cursor: 'pointer' }}>
                  <input type="radio" name="speech" checked={speechId === m.id} onChange={() => setSpeechId(m.id)} disabled={aiBusy}
                    style={{ accentColor: 'var(--slider)' }} />
                  {m.label}
                </label>
              ))}
            </div>
          )}
        </div>

        <div style={styles.card}>
          <label style={{ ...styles.row, cursor: voiceInstalled ? 'default' : 'pointer' }}>
            {voiceInstalled
              ? <Badge ok={true} />
              : <input type="checkbox" checked={wantVoice} onChange={e => setWantVoice(e.target.checked)} disabled={aiBusy}
                  style={{ width: 18, height: 18, accentColor: 'var(--slider)' }} />}
            <span style={{ flex: 1 }}>
              <b>Narration voice</b> — reads a script aloud
              <div style={styles.mono}>
                Used by Auto Narrate · {optional ? `~${optional.kokoro?.downloadMB} MB` : ''}{voiceInstalled ? ' · installed' : ''}
              </div>
            </span>
          </label>
        </div>

        <div style={styles.card}>
          <div style={{ ...styles.row, alignItems: 'flex-start' }}>
            <span style={{ flex: 1 }}>
              <b>Background removal</b> — cut subjects out of video
              <div style={styles.mono}>Used by Remove Background (its “static camera” mode needs no download)</div>
              {[['u2netp', wantBgFast, setWantBgFast, 'Fast, general-purpose'], ['u2net_human_seg', wantBgPeople, setWantBgPeople, 'Best for people']].map(([id, want, setWant, label]) => (
                <label key={id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, marginTop: 6, cursor: bgInstalled(id) ? 'default' : 'pointer' }}>
                  {bgInstalled(id)
                    ? <Badge ok={true} />
                    : <input type="checkbox" checked={want} onChange={e => setWant(e.target.checked)} disabled={aiBusy}
                        style={{ width: 16, height: 16, accentColor: 'var(--slider)' }} />}
                  {label} · {optional ? `~${bgModels[id]?.sizeMB ?? '?'} MB` : ''}{bgInstalled(id) ? ' · installed' : ''}
                </label>
              ))}
            </span>
          </div>
        </div>

        <div style={{ ...styles.mono, marginTop: 4 }}>
          Auto Narrate can also draft a script from a topic using the free{' '}
          <a href="#" onClick={e => { e.preventDefault(); window.electronAPI.openExternal('ollama') }} style={{ color: 'var(--purple)' }}>Ollama</a>{' '}
          app{optional?.ollama?.running ? ' (detected ✓)' : ''} — also local and offline, and entirely optional.
        </div>

        {aiBusy && aiStatus && (
          <div style={{ marginTop: 10 }}>
            <div style={styles.mono}>{aiStatus.label}</div>
            <Bar fraction={dlFraction(aiStatus)} />
          </div>
        )}
        {aiError && (
          <div style={{ fontSize: 11, color: 'var(--coral)', fontFamily: 'var(--font-mono)', marginTop: 8 }}>❌ {aiError}</div>
        )}

        <div style={styles.footer}>
          <button style={styles.buttonSmall()} onClick={() => window.electronAPI.openModelsFolder()} {...press(false)}>
            Open models folder…
          </button>
          <span style={{ display: 'flex', gap: 8 }}>
            <button style={styles.button('var(--paper)')} onClick={finish} disabled={aiBusy} {...press(aiBusy)}>
              {anySelected ? 'Skip' : 'Close'}
            </button>
            {anySelected && (
              <button
                style={styles.button('var(--yellow)')}
                disabled={aiBusy}
                onClick={handleContinue}
                {...press(aiBusy)}
              >
                {aiBusy ? 'Downloading…' : 'Continue →'}
              </button>
            )}
          </span>
        </div>
        {!engineReady && env && !repairing && (
          <div style={{ ...styles.mono, marginTop: 8 }}>You can close this and finish setup later — some programs won't run until it's ready.</div>
        )}
        <style>{`@keyframes vb-indeterminate { 0% { margin-left: -35%; } 100% { margin-left: 100%; } }`}</style>
      </div>
    </div>
  )
}
