import React, { useEffect } from 'react'
import { createPortal } from 'react-dom'
import { lockModal } from '../useModalLock'
import { HELP_SECTIONS } from '../helpContent'

// **bold** and *italic* only — enough for the help text without a markdown dependency.
function rich(text) {
  return text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g).map((part, i) => {
    if (part.startsWith('**')) return <b key={i}>{part.slice(2, -2)}</b>
    if (part.startsWith('*')) return <i key={i}>{part.slice(1, -1)}</i>
    return part
  })
}

/** Simple help: basic usage, handy tips, shortcuts and what to do when stuck. Opened with the ? button, F1 or ?. */
export default function HelpWindow({ onClose }) {
  useEffect(() => lockModal(), [])
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape' || e.key === 'F1') { e.preventDefault(); e.stopPropagation(); onClose() }
    }
    window.addEventListener('keydown', onKey, true)
    return () => window.removeEventListener('keydown', onKey, true)
  }, [onClose])

  return createPortal(
    <div style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(8,8,8,0.55)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}
         onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}>
      <div role="dialog" aria-label="Help" style={{ width: 'min(680px, 100%)', maxHeight: '100%', display: 'flex', flexDirection: 'column', background: 'var(--paper)',
                                                   color: 'var(--ink)', border: 'var(--border)', borderRadius: 'var(--radius)', boxShadow: 'var(--shadow)', overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', background: 'var(--cyan)', color: 'var(--on-color)', borderBottom: 'var(--border)' }}>
          <span style={{ fontFamily: 'var(--font-display)', fontSize: 15 }}>Help</span>
          <span style={{ fontSize: 11, opacity: 0.85 }}>the short version</span>
          <span style={{ flex: 1 }} />
          <button onClick={onClose} title="Close (Esc)" style={{ padding: '2px 9px' }}>✕</button>
        </div>
        <div style={{ overflowY: 'auto', padding: '6px 18px 18px', fontSize: 13, lineHeight: 1.55 }}>
          {HELP_SECTIONS.map(sec => (
            <section key={sec.title} style={{ marginTop: 14 }}>
              <h3 style={{ fontFamily: 'var(--font-mono)', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', margin: '0 0 6px', color: 'var(--purple)' }}>{sec.title}</h3>
              {sec.steps && (
                <ol style={{ margin: 0, paddingLeft: 20 }}>
                  {sec.steps.map((s, i) => <li key={i} style={{ marginBottom: 4 }}>{rich(s)}</li>)}
                </ol>
              )}
              {sec.bullets && (
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  {sec.bullets.map((s, i) => <li key={i} style={{ marginBottom: 4 }}>{rich(s)}</li>)}
                </ul>
              )}
              {sec.keys && (
                <div style={{ display: 'grid', gridTemplateColumns: 'max-content 1fr', columnGap: 16, rowGap: 3, fontSize: 12 }}>
                  {sec.keys.map(([k, d]) => (
                    <React.Fragment key={k}>
                      <code style={{ fontFamily: 'var(--font-mono)', background: 'var(--paper-dim)', border: '1.5px solid var(--ink)', borderRadius: 4, padding: '0 6px' }}>{k}</code>
                      <span>{d}</span>
                    </React.Fragment>
                  ))}
                </div>
              )}
            </section>
          ))}
        </div>
      </div>
    </div>,
    document.body
  )
}
