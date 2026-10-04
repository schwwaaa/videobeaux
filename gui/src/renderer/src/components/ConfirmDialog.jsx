import React, { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { lockModal } from '../useModalLock'

/** A small in-app confirmation dialog (keyboard-safe: the canvas ignores keys while it is open). */
export default function ConfirmDialog({ title, message, checkboxLabel, confirmLabel = 'OK', danger = false, onConfirm, onCancel }) {
  const [checked, setChecked] = useState(false)

  useEffect(() => lockModal(), [])
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); onCancel() }
      else if (e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); onConfirm(checked) }
    }
    window.addEventListener('keydown', onKey, true)
    return () => window.removeEventListener('keydown', onKey, true)
  }, [onCancel, onConfirm, checked])

  return createPortal(
    <div style={{ position: 'fixed', inset: 0, zIndex: 1100, background: 'rgba(8,8,8,0.55)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
         onMouseDown={e => { if (e.target === e.currentTarget) onCancel() }}>
      <div role="dialog" aria-label={title} style={{ width: 380, background: 'var(--paper)', color: 'var(--ink)', border: 'var(--border)',
                                                   borderRadius: 'var(--radius)', boxShadow: 'var(--shadow)', overflow: 'hidden' }}>
        <div style={{ background: danger ? 'var(--coral)' : 'var(--cyan)', color: 'var(--on-color)', padding: '8px 14px',
                      borderBottom: 'var(--border)', fontFamily: 'var(--font-display)', fontSize: 13 }}>{title}</div>
        <div style={{ padding: '14px 16px', fontSize: 13, lineHeight: 1.5 }}>
          {message}
          {checkboxLabel && (
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 12, fontSize: 12 }}>
              <input type="checkbox" checked={checked} onChange={e => setChecked(e.target.checked)} />
              {checkboxLabel}
            </label>
          )}
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, padding: '0 16px 14px' }}>
          <button onClick={onCancel} style={{ padding: '6px 14px' }}>Cancel</button>
          <button autoFocus onClick={() => onConfirm(checked)}
                  style={{ padding: '6px 14px', background: danger ? 'var(--coral)' : 'var(--yellow)', color: 'var(--on-color)' }}>{confirmLabel}</button>
        </div>
      </div>
    </div>,
    document.body
  )
}
