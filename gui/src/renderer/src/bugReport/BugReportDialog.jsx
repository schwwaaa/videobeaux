// BUG-REPORT (test phase) — writes a report zip on this computer. Nothing is sent by the app. See gui/src/main/bugReport.js.
import React, { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { lockModal } from '../useModalLock'
import flags from '../../../../feature-flags.json'

const sleep = ms => new Promise(r => setTimeout(r, ms))

export default function BugReportDialog({ onClose, logText = '', canvasJson = '' }) {
  useEffect(() => lockModal(), [])
  const [description, setDescription] = useState('')
  const [includeLog, setIncludeLog] = useState(!!logText)
  const [includeCanvas, setIncludeCanvas] = useState(!!canvasJson)
  const [includeScreenshot, setIncludeScreenshot] = useState(true)
  const [hidden, setHidden] = useState(false)     // the dialog steps out of the way while the screenshot is taken
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const onKey = e => { if (e.key === 'Escape' && !busy && !hidden) { e.preventDefault(); e.stopPropagation(); onClose() } }
    window.addEventListener('keydown', onKey, true)
    return () => window.removeEventListener('keydown', onKey, true)
  }, [busy, hidden, onClose])

  async function create() {
    setBusy(true); setError('')
    try {
      if (includeScreenshot) { setHidden(true); await sleep(250) }
      const res = await window.electronAPI.createBugReport({
        description,
        includeLog: includeLog && !!logText, logText,
        includeCanvas: includeCanvas && !!canvasJson, canvasJson,
        captureScreenshot: includeScreenshot
      })
      setResult(res)
    } catch (e) {
      setError(e?.message || 'Could not create the report.')
    } finally {
      setHidden(false); setBusy(false)
    }
  }

  function emailIt() {
    const to = flags.bugReportEmail
    const where = result.zip || result.folder
    const body = `${description.slice(0, 800)}\n\nThe report is saved at:\n${where}\n\n(Drag that file into this email to attach it.)`
    const url = `mailto:${to}?subject=${encodeURIComponent('videobeaux bug report')}&body=${encodeURIComponent(body)}`
    window.electronAPI.openMailto(url)
  }

  if (hidden) return null

  const box = { border: '2px solid var(--ink)', borderRadius: 8, padding: '10px 12px', background: 'var(--paper)' }
  const label = { display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 13, lineHeight: 1.4, cursor: 'pointer' }
  const primary = { padding: '7px 14px', fontSize: 13, background: 'var(--yellow)', border: '2px solid var(--ink)', borderRadius: 8, boxShadow: '3px 3px 0 var(--ink)' }
  const quiet = { padding: '7px 14px', fontSize: 13 }

  return createPortal(
    <div style={{ position: 'fixed', inset: 0, zIndex: 1100, background: 'rgba(8,8,8,0.55)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}
         onMouseDown={e => { if (e.target === e.currentTarget && !busy) onClose() }}>
      <div role="dialog" aria-label="Send a bug report" style={{ width: 'min(520px, 100%)', background: 'var(--paper)', color: 'var(--ink)', border: 'var(--border)', borderRadius: 'var(--radius)', boxShadow: 'var(--shadow)', overflow: 'hidden' }}>
        <div style={{ padding: '10px 14px', background: 'var(--magenta)', color: '#fff', borderBottom: 'var(--border)', fontFamily: 'var(--font-display)', fontSize: 15 }}>
          Send a bug report
        </div>

        <div style={{ padding: 16, display: 'grid', gap: 12 }}>
          {!result && (
            <>
              <p style={{ margin: 0, fontSize: 12, lineHeight: 1.45 }}>
                <b>Nothing is sent.</b> This makes a report file on your computer. You decide what to do with it. Personal folder
                names are removed; file names are kept, since they're often part of the problem.
              </p>

              <label style={{ display: 'grid', gap: 4, fontSize: 13 }}>
                <span>What happened? What did you expect?</span>
                <textarea value={description} onChange={e => setDescription(e.target.value)} rows={5} disabled={busy}
                          placeholder="For example: I dropped in a clip, pressed Run, and the progress bar stopped at step 2."
                          style={{ width: '100%', padding: 8, fontSize: 13, fontFamily: 'inherit', border: '2px solid var(--ink)', borderRadius: 6, resize: 'vertical' }} />
              </label>

              <div style={{ ...box, display: 'grid', gap: 8 }}>
                <label style={label}>
                  <input type="checkbox" checked={includeLog && !!logText} disabled={!logText || busy} onChange={e => setIncludeLog(e.target.checked)} />
                  <span>Include the recent log {logText ? '(the last ~1000 lines of the bottom bar)' : '(nothing to include here)'}</span>
                </label>
                <label style={label}>
                  <input type="checkbox" checked={includeCanvas && !!canvasJson} disabled={!canvasJson || busy} onChange={e => setIncludeCanvas(e.target.checked)} />
                  <span>Include the canvas: which program modes are wired and how</span>
                </label>
                <label style={label}>
                  <input type="checkbox" checked={includeScreenshot} disabled={busy} onChange={e => setIncludeScreenshot(e.target.checked)} />
                  <span>Include a screenshot of the window. The dialog steps aside to take it.</span>
                </label>
              </div>

              {error && <div style={{ color: 'var(--coral)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>❌ {error}</div>}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                <button onClick={onClose} disabled={busy} style={quiet}>Cancel</button>
                <button onClick={create} disabled={busy} style={primary}>{busy ? 'Making the report…' : 'Make the report'}</button>
              </div>
            </>
          )}

          {result && (
            <>
              <p style={{ margin: 0, fontSize: 13, lineHeight: 1.45 }}>
                {result.zip ? 'The report is ready.' : 'The report is ready, as a folder (zipping didn’t work on this computer).'}
              </p>
              <div style={{ ...box, fontFamily: 'var(--font-mono)', fontSize: 11, wordBreak: 'break-all' }}>
                {result.zip || result.folder}
              </div>
              <p style={{ margin: 0, fontSize: 12, lineHeight: 1.45 }}>
                Send that file to the person who gave you the app, or attach it to an email or message.
              </p>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, flexWrap: 'wrap' }}>
                <button onClick={() => window.electronAPI.showItem(result.zip || result.folder)} style={quiet}>Show in folder</button>
                {flags.bugReportEmail && <button onClick={emailIt} style={primary}>Email it</button>}
                <button onClick={onClose} style={quiet}>Done</button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>,
    document.body
  )
}
