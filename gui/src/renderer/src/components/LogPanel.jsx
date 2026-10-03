import React, { useEffect, useRef, useState } from 'react'

const TYPE_STYLE = {
  stdout:          { color: 'var(--paper)' },
  stderr:          { color: 'var(--yellow)' },
  system:          { color: 'var(--cyan)', fontStyle: 'italic' },
  command:         { color: '#7a7a72', fontFamily: 'var(--font-mono)', fontSize: 11 },
  success:         { color: 'var(--lime-bright)', fontWeight: 700 },
  error:           { color: 'var(--coral)', fontWeight: 700 },
  'progress-line': { color: 'var(--cyan)', fontFamily: 'var(--font-mono)' }
}

// ── Progress section ──────────────────────────────────────────────────────────
//
// Overall % = ((step - 1) + within_step_pct / 100) / total
// This gives a smooth fill across the whole pipeline:
//   step 1 of 2 starting  →  0 %
//   step 1 of 2 at 50 %   → 25 %
//   step 1 of 2 at 100%   → 50 %  (snap when step message arrives)
//   step 2 of 2 at 80 %   → 90 %
//   done                  → bar hides

function ProgressBar({ progress }) {
  if (!progress) return null

  const { step, total, name, pct, speed } = progress
  const hasPct = pct !== null && pct !== undefined

  // Compute a real bar fill using completed steps + within-step progress
  const overallPct = total > 0
    ? Math.round(((step - 1) + (hasPct ? pct / 100 : 0)) / total * 100)
    : 0

  const stepLabel = step > 0
    ? `Step ${step} / ${total}`
    : `${total} step${total !== 1 ? 's' : ''} queued`

  return (
    <div style={{
      padding: '7px 12px 8px',
      borderBottom: '2px solid #000',
      display: 'flex',
      flexDirection: 'column',
      gap: 5,
      background: 'var(--screen-dim)',
      flexShrink: 0
    }}>
      {/* Label row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
        <span style={{
          fontFamily: 'var(--font-mono)', fontWeight: 600,
          fontSize: 11, color: 'var(--cyan)', flex: 1,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
        }}>
          {stepLabel}{name ? ` — ${name}` : ''}
        </span>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexShrink: 0 }}>
          {speed && (
            <span style={{ fontSize: 10, color: '#8a8a80', fontFamily: 'var(--font-mono)' }}>{speed}</span>
          )}
          <span style={{
            fontFamily: 'var(--font-mono)', fontWeight: 700,
            fontSize: 10, color: 'var(--yellow)',
            fontVariantNumeric: 'tabular-nums', minWidth: 28, textAlign: 'right'
          }}>
            {overallPct}%
          </span>
        </div>
      </div>

      {/* Progress track */}
      <div style={{ height: 6, background: '#000', borderRadius: 3, overflow: 'hidden', border: '1px solid #000' }}>
        <div style={{
          height: '100%',
          width: `${overallPct}%`,
          background: 'linear-gradient(90deg, var(--lime-bright), var(--cyan))',
          borderRadius: 2,
          transition: 'width 0.35s ease'
        }} />
      </div>
    </div>
  )
}

// ── LogPanel ──────────────────────────────────────────────────────────────────

export default function LogPanel({ logs, isRunning, progress, onClear, onToggle, collapsed }) {
  const bottomRef = useRef(null)
  const [dragBlocked, setDragBlocked] = useState(false)

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs])

  // This is not a drop target — programs get added to the canvas, not here.
  // Dropping a sidebar program was already a silent no-op (nothing wired an
  // onDrop here), but there was no feedback explaining why; this makes that
  // explicit with a "no-drop" cursor and a highlighted border while dragging.
  const isProgramDrag = (e) =>
    e.dataTransfer.types.includes('application/videobeaux-program') ||
    e.dataTransfer.types.includes('application/videobeaux-node')

  const onDragOver = (e) => {
    if (!isProgramDrag(e)) return
    e.preventDefault()
    e.dataTransfer.dropEffect = 'none'
  }
  const onDragEnter = (e) => {
    if (!isProgramDrag(e)) return
    e.preventDefault()
    setDragBlocked(true)
  }
  const onDragLeave = (e) => {
    if (e.currentTarget.contains(e.relatedTarget)) return
    setDragBlocked(false)
  }
  const onDrop = (e) => {
    if (!isProgramDrag(e)) return
    e.preventDefault()
    setDragBlocked(false)
  }

  return (
    <div
      onDragOver={onDragOver}
      onDragEnter={onDragEnter}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      style={{
        background: 'var(--screen)',
        borderTop: dragBlocked ? '3px dashed var(--coral)' : 'var(--border)',
        boxShadow: dragBlocked ? 'inset 0 0 0 3px var(--coral)' : 'none',
        display: 'flex',
        flexDirection: 'column',
        height: collapsed ? 34 : 220,
        transition: 'height 0.2s ease',
        overflow: 'hidden',
        position: 'relative'
      }}
    >
      {dragBlocked && (
        <div style={{
          position: 'absolute', inset: 0, zIndex: 5,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(8,8,8,0.75)', pointerEvents: 'none',
          fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 11,
          color: 'var(--coral)', letterSpacing: '0.04em', textTransform: 'uppercase'
        }}>
          🚫 Drop on the canvas, not here
        </div>
      )}
      {/* Toolbar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '0 12px',
        height: 34,
        borderBottom: collapsed ? 'none' : '2px solid #000',
        flexShrink: 0
      }}>
        <button
          onClick={onToggle}
          style={{
            background: 'transparent', color: 'var(--paper)', border: 'none',
            padding: '2px 4px', fontSize: 11, cursor: 'pointer', borderRadius: 3, lineHeight: 1
          }}
          title={collapsed ? 'Expand log' : 'Collapse log'}
        >
          {collapsed ? '▲' : '▼'}
        </button>

        <span style={{
          fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: 'var(--lime-bright)',
          letterSpacing: '0.1em', textTransform: 'uppercase'
        }}>
          Signal Out
        </span>

        {/* Running pulse dot */}
        {isRunning && (
          <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 10, color: 'var(--magenta)' }}>
            <span style={{
              width: 6, height: 6, borderRadius: '50%', background: 'var(--magenta)', display: 'inline-block',
              animation: 'vb-pulse 1s ease-in-out infinite'
            }} />
          </span>
        )}

        {!isRunning && logs.length > 0 && (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#6a6a62' }}>
            {logs.length} line{logs.length !== 1 ? 's' : ''}
          </span>
        )}

        <div style={{ flex: 1 }} />

        {logs.length > 0 && (
          <button
            onClick={onClear}
            style={{
              background: 'transparent', color: '#8a8a80', border: 'none',
              fontFamily: 'var(--font-mono)', fontSize: 11, cursor: 'pointer', padding: '2px 6px', borderRadius: 3
            }}
            onMouseOver={e => e.currentTarget.style.color = 'var(--yellow)'}
            onMouseOut={e => e.currentTarget.style.color = '#8a8a80'}
          >
            Clear
          </button>
        )}
      </div>

      {/* Progress bar — only while running */}
      {!collapsed && isRunning && progress && (
        <ProgressBar progress={progress} />
      )}

      {/* Log text */}
      {!collapsed && (
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '6px 12px 8px',
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          lineHeight: 1.6,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all'
        }}>
          {logs.length === 0 ? (
            <span style={{ color: '#5a5a52', fontStyle: 'italic' }}>
              Log output will appear here when the pipeline runs…
            </span>
          ) : (
            logs.map((entry, i) => (
              <span key={i} style={TYPE_STYLE[entry.type] || TYPE_STYLE.stdout}>
                {entry.text}
              </span>
            ))
          )}
          <div ref={bottomRef} />
        </div>
      )}

      <style>{`
        @keyframes vb-pulse {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.25; }
        }
      `}</style>
    </div>
  )
}
