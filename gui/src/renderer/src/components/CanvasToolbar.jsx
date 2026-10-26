import React, { useEffect, useRef, useState } from 'react'

/**
 * The row of canvas buttons (Undo … Clear) and the Run button, which shrink with the canvas instead of covering it:
 *   full      ≥ 1100 px   icon + label
 *   compact   ≥  820 px   icon + short label, tighter padding
 *   icon      ≥  560 px   icon only (names in the tooltip)
 *   menu      <  560 px   Undo / Redo + one "☰ Tools" menu
 * A small caret hides the whole row (remembered), so the workspace can be cleared entirely.
 */
export function toolbarMode(width) {
  if (width >= 1100) return 'full'
  if (width >= 820) return 'compact'
  if (width >= 560) return 'icon'
  return 'menu'
}

const HIDE_KEY = 'vb.toolbar.hidden'
const readHidden = () => { try { return window.localStorage.getItem(HIDE_KEY) === '1' } catch { return false } }
const writeHidden = (v) => { try { window.localStorage.setItem(HIDE_KEY, v ? '1' : '0') } catch { /* private mode */ } }

const press = {
  onMouseDown: e => { if (!e.currentTarget.disabled) { e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'translate(3px, 3px)' } },
  onMouseUp: e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' },
  onMouseLeave: e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }
}

function Btn({ mode, icon, label, short, title, onClick, disabled, background = 'var(--paper)', color = 'var(--ink)', wide }) {
  const iconOnly = mode === 'icon'
  const compact = mode === 'compact'
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title || label}
      aria-label={label}
      {...press}
      style={{
        background, color,
        padding: iconOnly ? '7px 0' : compact ? '7px 9px' : '9px 14px',
        width: iconOnly ? 34 : undefined,
        borderRadius: 'var(--radius-sm)', fontFamily: 'var(--font-display)', fontSize: compact ? 11 : 12,
        border: 'var(--border)', boxShadow: 'var(--shadow-sm)', whiteSpace: 'nowrap', flexShrink: 0,
        opacity: disabled ? 0.4 : 1, cursor: disabled ? 'not-allowed' : 'pointer',
        ...(wide && !iconOnly ? { padding: compact ? '7px 12px' : '9px 20px' } : {})
      }}
    >
      {iconOnly ? icon : <>{icon} {mode === 'compact' ? (short || label) : label}</>}
    </button>
  )
}

export default function CanvasToolbar({ width, isRunning, canUndo, canRedo, onUndo, onRedo, onSave, onLoad, onExamples, onSnapshot, onTidy, onClear, tidyLabel }) {
  const mode = toolbarMode(width)
  const [hidden, setHidden] = useState(readHidden)
  const [menu, setMenu] = useState(false)
  const menuRef = useRef(null)
  useEffect(() => { writeHidden(hidden) }, [hidden])
  useEffect(() => {
    if (!menu) return undefined
    const close = (e) => { if (menuRef.current && !menuRef.current.contains(e.target)) setMenu(false) }
    document.addEventListener('mousedown', close, true)
    return () => document.removeEventListener('mousedown', close, true)
  }, [menu])

  if (hidden) {
    return (
      <button onClick={() => setHidden(false)} title="Show the toolbar" aria-label="Show toolbar" {...press}
              style={{ background: 'var(--paper)', color: 'var(--ink)', padding: '5px 9px', borderRadius: 'var(--radius-sm)', border: 'var(--border)',
                       boxShadow: 'var(--shadow-sm)', fontFamily: 'var(--font-display)', fontSize: 12 }}>
        ☰
      </button>
    )
  }

  const undoDisabled = !canUndo || isRunning
  const redoDisabled = !canRedo || isRunning
  const items = [
    { id: 'save', icon: '💾', label: 'Save Preset', short: 'Save', onClick: onSave, disabled: isRunning },
    { id: 'load', icon: '📂', label: 'Load Preset', short: 'Load', onClick: onLoad, disabled: isRunning },
    { id: 'examples', icon: '🧪', label: 'Examples', short: 'Examples', onClick: onExamples, disabled: isRunning },
    { id: 'snap', icon: '📸', label: 'Snapshot', short: 'Snap', title: 'Save a picture of the whole patch (PNG) together with its preset (JSON)', onClick: onSnapshot },
    { id: 'tidy', icon: '✨', label: tidyLabel || 'Tidy', short: tidyLabel || 'Tidy', title: 'Arrange the programs neatly, left to right (⌘⇧L; ⌘Z undoes)', onClick: onTidy, disabled: isRunning },
    { id: 'clear', icon: '🗑', label: 'Clear', short: 'Clear', title: 'Clear the workspace (asks first; ⌘Z undoes)', onClick: onClear, disabled: isRunning }
  ]

  return (
    <div style={{ display: 'flex', gap: mode === 'full' ? 6 : 4, alignItems: 'center' }}>
      <Btn mode={mode === 'menu' ? 'icon' : mode} icon="↶" label="Undo" title="Undo (⌘Z)" onClick={onUndo} disabled={undoDisabled} />
      <Btn mode={mode === 'menu' ? 'icon' : mode} icon="↷" label="Redo" title="Redo (⇧⌘Z)" onClick={onRedo} disabled={redoDisabled} />
      {mode !== 'menu' && items.map(it => <Btn key={it.id} mode={mode} {...it} />)}
      {mode === 'menu' && (
        <div ref={menuRef} style={{ position: 'relative' }}>
          <Btn mode="compact" icon="☰" label="Tools" short="Tools ▾" onClick={() => setMenu(m => !m)} />
          {menu && (
            <div style={{ position: 'absolute', top: 'calc(100% + 6px)', left: 0, zIndex: 20, minWidth: 170, background: 'var(--paper)',
                          border: 'var(--border)', borderRadius: 'var(--radius-sm)', boxShadow: 'var(--shadow)', padding: 6,
                          display: 'flex', flexDirection: 'column', gap: 4 }}>
              {items.map(it => (
                <button key={it.id} disabled={it.disabled} title={it.title || it.label}
                        onClick={() => { setMenu(false); it.onClick() }}
                        style={{ textAlign: 'left', background: 'transparent', color: 'var(--ink)', border: 'none', padding: '6px 8px', borderRadius: 6,
                                 fontFamily: 'var(--font-display)', fontSize: 12, opacity: it.disabled ? 0.4 : 1, cursor: it.disabled ? 'not-allowed' : 'pointer' }}
                        onMouseOver={e => { if (!it.disabled) e.currentTarget.style.background = 'var(--yellow)' }}
                        onMouseOut={e => { e.currentTarget.style.background = 'transparent' }}>
                  {it.icon} {it.label}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
      <button onClick={() => setHidden(true)} title="Hide the toolbar" aria-label="Hide toolbar"
              style={{ background: 'transparent', border: 'none', color: 'var(--muted-dim)', fontSize: 14, padding: '0 4px', cursor: 'pointer', flexShrink: 0 }}>
        ◂
      </button>
    </div>
  )
}

/** Run / Cancel — "▶ Run Pipeline", "▶ Run", then just "▶" as the canvas narrows. */
export function RunButton({ width, isRunning, onRun, onCancel, overwrite }) {
  const mode = toolbarMode(width)
  const label = mode === 'full' ? `▶ Run Pipeline${overwrite ? ' 🔥' : ''}` : mode === 'compact' ? `▶ Run${overwrite ? ' 🔥' : ''}` : (overwrite ? '▶🔥' : '▶')
  const cancel = mode === 'full' || mode === 'compact' ? '■ Cancel' : '■'
  const small = mode === 'icon' || mode === 'menu'
  return (
    <button
      onClick={isRunning ? onCancel : onRun}
      title={isRunning ? 'Cancel the running pipeline' : `Run the pipeline${overwrite ? ' (overwrite is on)' : ''}`}
      aria-label={isRunning ? 'Cancel' : 'Run pipeline'}
      {...press}
      style={{
        background: isRunning ? 'var(--coral)' : 'var(--yellow)', color: '#080808',
        padding: small ? '7px 12px' : mode === 'compact' ? '7px 14px' : '9px 20px', borderRadius: 'var(--radius-sm)',
        fontFamily: 'var(--font-display)', fontSize: mode === 'full' ? 12 : 11,
        border: 'var(--border)', boxShadow: 'var(--shadow-sm)', whiteSpace: 'nowrap'
      }}
    >
      {isRunning ? cancel : label}
    </button>
  )
}
