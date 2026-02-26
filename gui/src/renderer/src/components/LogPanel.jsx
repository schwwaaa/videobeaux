import React, { useEffect, useRef } from 'react'

const TYPE_STYLE = {
  stdout:  { color: '#e0e0e0' },
  stderr:  { color: '#fbbf24' },
  system:  { color: '#3b82f6', fontStyle: 'italic' },
  command: { color: '#555', fontFamily: 'var(--font-mono, monospace)', fontSize: 11 },
  success: { color: '#22c55e', fontWeight: 700 },
  error:   { color: '#ef4444', fontWeight: 700 }
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
      borderBottom: '1px solid #1a1a1a',
      display: 'flex',
      flexDirection: 'column',
      gap: 5,
      background: '#0d0d0d',
      flexShrink: 0
    }}>
      {/* Label row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
        <span style={{ fontSize: 11, color: '#3b82f6', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {stepLabel}{name ? ` — ${name}` : ''}
        </span>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexShrink: 0 }}>
          {speed && (
            <span style={{ fontSize: 10, color: '#555', fontFamily: 'monospace' }}>{speed}</span>
          )}
          <span style={{ fontSize: 10, color: '#666', fontVariantNumeric: 'tabular-nums', minWidth: 28, textAlign: 'right' }}>
            {overallPct}%
          </span>
        </div>
      </div>

      {/* Progress track */}
      <div style={{ height: 3, background: '#1e1e1e', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: `${overallPct}%`,
          background: 'linear-gradient(90deg, #22c55e, #06b6d4)',
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

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs])

  return (
    <div style={{
      background: '#0a0a0a',
      borderTop: '1px solid #242424',
      display: 'flex',
      flexDirection: 'column',
      height: collapsed ? 32 : 220,
      transition: 'height 0.2s ease',
      overflow: 'hidden'
    }}>
      {/* Toolbar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '0 12px',
        height: 32,
        borderBottom: collapsed ? 'none' : '1px solid #1a1a1a',
        flexShrink: 0
      }}>
        <button
          onClick={onToggle}
          style={{
            background: 'transparent', color: '#555', border: 'none',
            padding: '2px 4px', fontSize: 11, cursor: 'pointer', borderRadius: 3, lineHeight: 1
          }}
          title={collapsed ? 'Expand log' : 'Collapse log'}
        >
          {collapsed ? '▲' : '▼'}
        </button>

        <span style={{
          fontSize: 11, fontWeight: 600, color: '#555',
          letterSpacing: '0.08em', textTransform: 'uppercase'
        }}>
          Log
        </span>

        {/* Running pulse dot */}
        {isRunning && (
          <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 10, color: '#3b82f6' }}>
            <span style={{
              width: 5, height: 5, borderRadius: '50%', background: '#3b82f6', display: 'inline-block',
              animation: 'vb-pulse 1s ease-in-out infinite'
            }} />
          </span>
        )}

        {!isRunning && logs.length > 0 && (
          <span style={{ fontSize: 10, color: '#444' }}>
            {logs.length} line{logs.length !== 1 ? 's' : ''}
          </span>
        )}

        <div style={{ flex: 1 }} />

        {logs.length > 0 && (
          <button
            onClick={onClear}
            style={{
              background: 'transparent', color: '#444', border: 'none',
              fontSize: 11, cursor: 'pointer', padding: '2px 6px', borderRadius: 3
            }}
            onMouseOver={e => e.currentTarget.style.color = '#888'}
            onMouseOut={e => e.currentTarget.style.color = '#444'}
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
          fontFamily: 'var(--font-mono, "Cascadia Code", "Fira Code", Consolas, monospace)',
          fontSize: 11,
          lineHeight: 1.6,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all'
        }}>
          {logs.length === 0 ? (
            <span style={{ color: '#333', fontStyle: 'italic' }}>
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
