import React, { useState } from 'react'
import { usePrograms } from '../ProgramsContext'

const ICON = {
  glitch:      '⚡',
  temporal:    '⏱',
  visual:      '✦',
  composition: '⊞',
  utility:     '⚙',
  ai:          '◈'
}

export default function Sidebar() {
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
      background: '#141414',
      borderRight: '1px solid #242424',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      userSelect: 'none'
    }}>
      {/* Search */}
      <div style={{ padding: '10px 10px 8px', borderBottom: '1px solid #242424' }}>
        <input
          type="text"
          placeholder="Search programs…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{
            width: '100%',
            background: '#1e1e1e',
            border: '1px solid #333',
            borderRadius: 5,
            color: '#e0e0e0',
            padding: '5px 9px',
            fontSize: 12,
            outline: 'none'
          }}
        />
      </div>

      {/* Program list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '6px 0' }}>
        {!ready && (
          <div style={{ padding: '16px 12px', fontSize: 11, color: '#555', fontStyle: 'italic' }}>
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
                  padding: '5px 10px 4px',
                  cursor: 'pointer',
                  textAlign: 'left',
                  borderRadius: 0
                }}
              >
                <span style={{ fontSize: 12 }}>{ICON[cat.id] || '◆'}</span>
                <span style={{
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: cat.color,
                  flex: 1
                }}>
                  {cat.label}
                </span>
                <span style={{ fontSize: 10, color: '#444' }}>
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
                      title={prog.description || prog.label}
                      style={{
                        padding: '5px 12px 5px 22px',
                        fontSize: 12,
                        color: '#ccc',
                        cursor: 'grab',
                        borderRadius: 4,
                        margin: '0 4px',
                        transition: 'background 0.1s, color 0.1s',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6
                      }}
                      onMouseOver={e => {
                        e.currentTarget.style.background = `${cat.color}18`
                        e.currentTarget.style.color = '#fff'
                      }}
                      onMouseOut={e => {
                        e.currentTarget.style.background = 'transparent'
                        e.currentTarget.style.color = '#ccc'
                      }}
                    >
                      <span style={{
                        width: 6, height: 6,
                        borderRadius: '50%',
                        background: cat.color,
                        flexShrink: 0,
                        opacity: 0.7
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
                            style={{ fontSize: 9, color: '#555', background: '#222', borderRadius: 3, padding: '1px 4px', cursor: 'help' }}
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
        borderTop: '1px solid #1e1e1e',
        fontSize: 10,
        color: '#444',
        textAlign: 'center',
        lineHeight: 1.5
      }}>
        Drag programs onto the canvas
      </div>
    </aside>
  )
}
