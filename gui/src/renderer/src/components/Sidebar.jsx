import React, { useState } from 'react'
import { usePrograms } from '../ProgramsContext'

const ICON = {
  glitch:   '⚡',
  trails:   '≋',
  temporal: '⏱',
  look:     '✦',
  vision:   '◉',
  layout:   '⊞',
  edit:     '✂',
  speech:   '◈',
  media:    '⚙'
}

export default function Sidebar({ canvasActions }) {
  const { categories, ready } = usePrograms()
  const [open, setOpen] = useState({})
  const [search, setSearch] = useState('')

  // Open all categories once data arrives (runs once when ready flips true)
  React.useEffect(() => {
    if (ready) setOpen(Object.fromEntries(categories.map(c => [c.id, true])))
  }, [ready]) // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = (id) => setOpen(s => ({ ...s, [id]: !s[id] }))

  const q = search.trim().toLowerCase()

  const onDragStart = (e, programId) => {
    e.dataTransfer.setData('application/videobeaux-program', programId)
    e.dataTransfer.effectAllowed = 'copy'
  }

  return (
    <aside style={{
      width: 240,
      background: 'var(--paper)',
      borderRight: 'var(--border)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      userSelect: 'none'
    }}>
      {/* Sources — add another Input node to feed a second/third video into a
          multi-input effect (e.g. stack_2x's second clip). Pinned above the
          search box so it's always reachable regardless of the filter. */}
      <div style={{ padding: '10px 10px 8px', borderBottom: '2px solid var(--ink)' }}>
        <div
          draggable
          onDragStart={e => {
            e.dataTransfer.setData('application/videobeaux-node', 'inputNode')
            e.dataTransfer.effectAllowed = 'copy'
          }}
          onDoubleClick={() => canvasActions?.addInput()}
          title="Drag onto the canvas, or double-click, to add another video source"
          style={{
            display: 'flex', alignItems: 'center', gap: 7,
            padding: '6px 10px', cursor: 'grab',
            background: 'var(--paper)', border: '2px solid var(--ink)', borderRadius: 6
          }}
        >
          <span style={{
            width: 9, height: 9, borderRadius: '50%',
            background: 'var(--cyan)', border: '1.5px solid var(--ink)', flexShrink: 0
          }} />
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700,
            letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink)'
          }}>
            + Input Video
          </span>
        </div>
      </div>

      {/* Search */}
      <div style={{ padding: '10px 10px 8px', borderBottom: '2px solid var(--ink)' }}>
        <input
          type="text"
          placeholder="Search programs…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{
            width: '100%',
            background: 'var(--paper)',
            border: '2px solid var(--ink)',
            borderRadius: 6,
            color: 'var(--ink)',
            padding: '5px 9px',
            fontSize: 12,
            outline: 'none'
          }}
        />
      </div>

      {/* Program list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '6px 0' }}>
        {!ready && (
          <div style={{ padding: '16px 12px', fontSize: 11, color: 'var(--muted)', fontStyle: 'italic' }}>
            Discovering programs…
          </div>
        )}
        {categories.map(cat => {
          const filtered = q
            ? cat.programs.filter(p =>
                p.label.toLowerCase().includes(q) ||
                p.id.toLowerCase().includes(q) ||
                (p.description || '').toLowerCase().includes(q)
              )
            : cat.programs

          if (filtered.length === 0) return null

          return (
            <div key={cat.id}>
              {/* Category header */}
              <button
                onClick={() => toggle(cat.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  width: '100%',
                  background: 'transparent',
                  border: 'none',
                  padding: '6px 10px 5px',
                  cursor: 'pointer',
                  textAlign: 'left',
                  borderRadius: 0
                }}
              >
                <span style={{ fontSize: 12 }}>{ICON[cat.id] || '◆'}</span>
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: 'var(--on-color)',
                  background: cat.color,
                  border: '2px solid var(--ink)',
                  borderRadius: 4,
                  padding: '1px 6px',
                  flex: 1
                }}>
                  {cat.label}
                </span>
                <span style={{ fontSize: 10, color: 'var(--ink)' }}>
                  {open[cat.id] ? '▾' : '▸'}
                </span>
              </button>

              {/* Programs */}
              {(open[cat.id] || q) && (
                <div style={{ paddingBottom: 4 }}>
                  {filtered.map(prog => (
                    <div
                      key={prog.id}
                      draggable
                      onDragStart={e => onDragStart(e, prog.id)}
                      onDoubleClick={() => canvasActions?.addProgram(prog.id)}
                      title={`${prog.description || prog.label}\n\nDrag onto the canvas, or double-click to add at center.`}
                      style={{
                        padding: '5px 12px 5px 22px',
                        fontSize: 12,
                        color: 'var(--ink)',
                        cursor: 'grab',
                        borderRadius: 5,
                        margin: '0 4px',
                        transition: 'background 0.1s, color 0.1s',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6
                      }}
                      onMouseOver={e => {
                        e.currentTarget.style.background = `${cat.color}33`
                        e.currentTarget.style.color = 'var(--ink)'
                      }}
                      onMouseOut={e => {
                        e.currentTarget.style.background = 'transparent'
                        e.currentTarget.style.color = 'var(--ink)'
                      }}
                    >
                      <span style={{
                        width: 7, height: 7,
                        borderRadius: '50%',
                        background: cat.color,
                        border: '1.5px solid var(--ink)',
                        flexShrink: 0
                      }} />
                      <span style={{ flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {prog.label}
                      </span>
                      {prog.args && prog.args.length > 0 && (() => {
                        const reqCount = prog.args.filter(a => a.required).length
                        const optCount = prog.args.length - reqCount
                        const tip = reqCount > 0
                          ? `${reqCount} required arg${reqCount !== 1 ? 's' : ''}${optCount > 0 ? `, ${optCount} optional` : ''} — configure in node`
                          : `${optCount} optional arg${optCount !== 1 ? 's' : ''} — configure in node`
                        return (
                          <span
                            title={tip}
                            style={{
                              fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--ink)',
                              background: 'var(--gray)', border: '1.5px solid var(--ink)',
                              borderRadius: 3, padding: '1px 4px', cursor: 'help'
                            }}
                          >
                            {reqCount > 0 ? '⚙' : '•'}
                          </span>
                        )
                      })()}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Footer hint */}
      <div style={{
        padding: '8px 10px',
        borderTop: '2px solid var(--ink)',
        fontFamily: 'var(--font-mono)',
        fontSize: 10,
        color: 'var(--muted-dim)',
        textAlign: 'center',
        lineHeight: 1.5
      }}>
        Drag onto the canvas, or double-click to add
      </div>
    </aside>
  )
}
