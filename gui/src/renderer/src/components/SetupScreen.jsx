import React, { useState, useEffect, useCallback } from 'react'

const styles = {
  overlay: {
    position: 'fixed', inset: 0, background: 'rgba(8,8,8,0.55)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 1000, padding: 24
  },
  panel: {
    background: 'var(--paper)', border: 'var(--border)', borderRadius: 'var(--radius)',
    boxShadow: 'var(--shadow)', maxWidth: 560, width: '100%',
    maxHeight: '90vh', overflowY: 'auto', padding: '24px 28px'
  },
  title: {
    fontFamily: 'var(--font-display)', fontSize: 22, color: 'var(--ink)', marginBottom: 4
  },
  subtitle: {
    fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--muted-dim)', marginBottom: 20
  },
  sectionTitle: {
    fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 12, letterSpacing: '0.06em',
    textTransform: 'uppercase', color: 'var(--ink)', marginBottom: 10, marginTop: 22
  },
  checkRow: {
    display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0',
    fontFamily: 'var(--font-mono)', fontSize: 12
  },
  badge: (ok) => ({
    width: 18, height: 18, borderRadius: '50%', flexShrink: 0,
    background: ok === null ? 'var(--gray)' : ok ? 'var(--lime-bright)' : 'var(--coral)',
    border: '2px solid var(--ink)', display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: 10, fontWeight: 700
  }),
  modelCard: {
    border: 'var(--border)', borderRadius: 'var(--radius-sm)', padding: '10px 12px',
    marginBottom: 8, display: 'flex', alignItems: 'center', gap: 10, background: 'var(--paper)'
  },
  modelLabel: { flex: 1, fontSize: 13, color: 'var(--ink)' },
  button: (accent) => ({
    background: accent || 'var(--yellow)', color: 'var(--ink)',
    padding: '7px 14px', borderRadius: 'var(--radius-sm)',
    fontFamily: 'var(--font-display)', fontSize: 11,
    border: 'var(--border)', boxShadow: 'var(--shadow-sm)',
    cursor: 'pointer', flexShrink: 0
  }),
  buttonSmall: (accent) => ({
    background: accent || 'var(--paper)', color: 'var(--ink)',
    padding: '5px 10px', borderRadius: 'var(--radius-sm)',
    fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 10,
    border: 'var(--border)', boxShadow: 'var(--shadow-sm)',
    cursor: 'pointer', flexShrink: 0
  }),
  progressTrack: {
    height: 8, background: 'var(--paper-dim)', border: '2px solid var(--ink)',
    borderRadius: 4, overflow: 'hidden', marginTop: 6
  },
  footer: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    marginTop: 24, paddingTop: 16, borderTop: '2px dashed var(--gray)'
  }
}

function pressable(e, down) {
  e.currentTarget.style.boxShadow = down ? 'none' : 'var(--shadow-sm)'
  e.currentTarget.style.transform = down ? 'translate(3px, 3px)' : 'none'
}

function Badge({ ok }) {
  return <div style={styles.badge(ok)}>{ok === null ? '' : ok ? '✓' : '✕'}</div>
}

export default function SetupScreen({ onClose }) {
  const [env, setEnv] = useState({ python: { ok: null }, ffmpeg: { ok: null }, ffprobe: { ok: null } })
  const [checking, setChecking] = useState(false)
  const [catalog, setCatalog] = useState([])
  const [installed, setInstalled] = useState([])
  const [downloading, setDownloading] = useState(null) // modelId currently downloading
  const [progress, setProgress] = useState(null) // { received, total, phase }
  const [downloadError, setDownloadError] = useState(null)
  // Optional features (narration voice, Ollama) — fetched separately so the
  // slower checks never delay the required-environment badges above.
  const [optional, setOptional] = useState(null)
  const [kokoroDownloading, setKokoroDownloading] = useState(false)
  const [kokoroProgress, setKokoroProgress] = useState(null)
  const [kokoroError, setKokoroError] = useState(null)

  const runCheck = useCallback(async () => {
    setChecking(true)
    const result = await window.electronAPI.checkEnvironment()
    setEnv(result)
    setChecking(false)
    window.electronAPI.checkOptional().then(setOptional).catch(() => {})
  }, [])

  const refreshInstalled = useCallback(async () => {
    const models = await window.electronAPI.listModels()
    setInstalled(models.map(m => m.name))
  }, [])

  useEffect(() => {
    runCheck()
    refreshInstalled()
    window.electronAPI.listModelCatalog().then(setCatalog)
    const removeProgress = window.electronAPI.onDownloadProgress(({ modelId, received, total, phase }) => {
      if (modelId === 'kokoro-tts') setKokoroProgress({ received, total, phase })
      else setProgress({ received, total, phase })
    })
    return () => removeProgress()
  }, [runCheck, refreshInstalled])

  const handleDownload = async (modelId) => {
    setDownloading(modelId)
    setDownloadError(null)
    setProgress({ received: 0, total: 0, phase: 'downloading' })
    const result = await window.electronAPI.downloadModel(modelId)
    setDownloading(null)
    setProgress(null)
    if (result.ok) {
      refreshInstalled()
    } else {
      setDownloadError(`${modelId}: ${result.error}`)
    }
  }

  const handleKokoroDownload = async () => {
    setKokoroDownloading(true)
    setKokoroError(null)
    setKokoroProgress({ received: 0, total: 0, phase: 'downloading' })
    const result = await window.electronAPI.downloadKokoro()
    setKokoroDownloading(false)
    setKokoroProgress(null)
    if (!result.ok) setKokoroError(result.error)
    window.electronAPI.checkOptional().then(setOptional).catch(() => {})
  }

  const envOk = env.python.ok && env.ffmpeg.ok && env.ffprobe.ok

  return (
    <div style={styles.overlay}>
      <div style={styles.panel}>
        <div style={styles.title}>Welcome to Videobeaux</div>
        <div style={styles.subtitle}>Let's make sure everything's working before you dive in.</div>

        <div style={styles.sectionTitle}>Environment</div>
        <div style={styles.checkRow}>
          <Badge ok={env.python.ok} /> Python {checking && env.python.ok === null ? '(checking…)' : env.python.ok ? 'ready' : env.python.detail || 'not found'}
        </div>
        <div style={styles.checkRow}>
          <Badge ok={env.ffmpeg.ok} /> ffmpeg {env.ffmpeg.ok ? 'ready' : (checking ? '(checking…)' : 'not found')}
        </div>
        <div style={styles.checkRow}>
          <Badge ok={env.ffprobe.ok} /> ffprobe {env.ffprobe.ok ? 'ready' : (checking ? '(checking…)' : 'not found')}
        </div>
        <button
          style={{ ...styles.buttonSmall(), marginTop: 8 }}
          onClick={runCheck}
          onMouseDown={e => pressable(e, true)} onMouseUp={e => pressable(e, false)} onMouseLeave={e => pressable(e, false)}
        >
          {checking ? 'Checking…' : 'Check Again'}
        </button>

        <div style={styles.sectionTitle}>Speech Model (for transcription-based effects)</div>
        {catalog.map(m => {
          const isInstalled = installed.includes(m.id)
          const isDownloading = downloading === m.id
          return (
            <div key={m.id} style={styles.modelCard}>
              <div style={styles.modelLabel}>
                {m.label}
                {isDownloading && progress && (
                  <div style={styles.progressTrack}>
                    <div style={{
                      height: '100%', background: 'var(--cyan)',
                      width: progress.total ? `${Math.min(100, (progress.received / progress.total) * 100)}%` : '30%',
                      transition: 'width 0.2s'
                    }} />
                  </div>
                )}
                {isDownloading && (
                  <span style={{ fontSize: 10, color: 'var(--muted-dim)' }}>
                    {progress?.phase === 'extracting' ? 'Extracting…' : 'Downloading…'}
                  </span>
                )}
              </div>
              {isInstalled ? (
                <span style={{ ...styles.badge(true), position: 'static' }}>✓</span>
              ) : (
                <button
                  style={styles.buttonSmall(downloading ? 'var(--gray)' : 'var(--cyan)')}
                  disabled={!!downloading}
                  onClick={() => handleDownload(m.id)}
                  onMouseDown={e => !downloading && pressable(e, true)} onMouseUp={e => pressable(e, false)} onMouseLeave={e => pressable(e, false)}
                >
                  {isDownloading ? '…' : 'Download'}
                </button>
              )}
            </div>
          )
        })}
        {downloadError && (
          <div style={{ fontSize: 11, color: 'var(--coral)', fontFamily: 'var(--font-mono)', marginTop: 4 }}>
            ❌ {downloadError}
          </div>
        )}
        <div style={styles.sectionTitle}>Optional features</div>
        <div style={{ fontSize: 11, color: 'var(--muted-dim)', fontFamily: 'var(--font-mono)', marginBottom: 8 }}>
          Only a couple of programs use these — skip them if you don't need those.
        </div>

        <div style={{ ...styles.modelCard, flexDirection: 'column', alignItems: 'stretch', gap: 6 }}>
          <div style={{ ...styles.modelLabel, fontWeight: 700 }}>
            Narration voice <span style={{ fontWeight: 400, color: 'var(--muted-dim)' }}>— Auto Narrate</span>
          </div>
          <div style={styles.checkRow}>
            <Badge ok={optional ? optional.kokoro.engine.ok : null} />
            Voice engine {optional ? (optional.kokoro.engine.ok
              ? `ready${optional.kokoro.engine.source === 'bundled' ? ' (built in)' : ''}`
              : 'not installed') : '(checking…)'}
          </div>
          {optional && !optional.kokoro.engine.ok && (
            <div style={{ fontSize: 10, color: 'var(--muted-dim)', fontFamily: 'var(--font-mono)' }}>
              Install it with: <code>uv tool install kokoro-tts</code> (then Check Again).
            </div>
          )}
          <div style={styles.checkRow}>
            <Badge ok={optional ? optional.kokoro.models.ok : null} />
            <span style={{ flex: 1 }}>
              Voice models {optional ? (optional.kokoro.models.ok ? 'downloaded' : `(~${optional.kokoro.downloadMB} MB, one time)`) : '(checking…)'}
              {kokoroDownloading && kokoroProgress && (
                <div style={styles.progressTrack}>
                  <div style={{
                    height: '100%', background: 'var(--cyan)',
                    width: kokoroProgress.total ? `${Math.min(100, (kokoroProgress.received / kokoroProgress.total) * 100)}%` : '30%',
                    transition: 'width 0.2s'
                  }} />
                </div>
              )}
            </span>
            {optional && !optional.kokoro.models.ok && (
              <button
                style={styles.buttonSmall(kokoroDownloading ? 'var(--gray)' : 'var(--cyan)')}
                disabled={kokoroDownloading}
                onClick={handleKokoroDownload}
                onMouseDown={e => !kokoroDownloading && pressable(e, true)} onMouseUp={e => pressable(e, false)} onMouseLeave={e => pressable(e, false)}
              >
                {kokoroDownloading
                  ? (kokoroProgress?.total ? `${Math.round((kokoroProgress.received / kokoroProgress.total) * 100)}%` : '…')
                  : 'Download'}
              </button>
            )}
          </div>
          {kokoroError && (
            <div style={{ fontSize: 11, color: 'var(--coral)', fontFamily: 'var(--font-mono)' }}>❌ {kokoroError}</div>
          )}
        </div>

        <div style={{ ...styles.modelCard, flexDirection: 'column', alignItems: 'stretch', gap: 6 }}>
          <div style={{ ...styles.modelLabel, fontWeight: 700 }}>
            Ollama <span style={{ fontWeight: 400, color: 'var(--muted-dim)' }}>— AI-drafted narration scripts (Auto Narrate → Topic)</span>
          </div>
          <div style={styles.checkRow}>
            <Badge ok={optional ? (optional.ollama.running ? true : null) : null} />
            <span style={{ flex: 1 }}>
              {!optional ? '(checking…)'
                : optional.ollama.running ? 'Running'
                : optional.ollama.installed ? 'Installed but not running — open the Ollama app'
                : 'Not installed'}
            </span>
            {optional && !optional.ollama.installed && (
              <button
                style={styles.buttonSmall()}
                onClick={() => window.electronAPI.openExternal('ollama')}
                onMouseDown={e => pressable(e, true)} onMouseUp={e => pressable(e, false)} onMouseLeave={e => pressable(e, false)}
              >
                Get Ollama
              </button>
            )}
          </div>
          <div style={{ fontSize: 10, color: 'var(--muted-dim)', fontFamily: 'var(--font-mono)' }}>
            Optional. Auto Narrate works fully offline with a script you type yourself.
          </div>
        </div>

        <button
          style={{ ...styles.buttonSmall(), marginTop: 4 }}
          onClick={() => window.electronAPI.openModelsFolder()}
          onMouseDown={e => pressable(e, true)} onMouseUp={e => pressable(e, false)} onMouseLeave={e => pressable(e, false)}
        >
          Open Models Folder…
        </button>

        <div style={styles.footer}>
          <span style={{ fontSize: 10, color: 'var(--muted)', fontFamily: 'var(--font-mono)' }}>
            {envOk ? '✓ Everything looks good.' : 'You can continue and fix issues later.'}
          </span>
          <button
            style={styles.button('var(--yellow)')}
            onClick={onClose}
            onMouseDown={e => pressable(e, true)} onMouseUp={e => pressable(e, false)} onMouseLeave={e => pressable(e, false)}
          >
            Continue →
          </button>
        </div>
      </div>
    </div>
  )
}
