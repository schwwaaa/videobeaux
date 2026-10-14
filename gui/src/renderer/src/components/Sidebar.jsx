import React, { useState } from 'react'
import { usePrograms } from '../ProgramsContext'
import { useSettings } from '../SettingsContext'
import { familyOf, familyOfCategory, FAMILIES, FAMILY_COLOR, motifOf, categoryMotif } from '../looks/registry'
import { resolveLook } from '../looks'
import { artFor, useArtVersion } from '../looks/output-art/art'

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

export default function Sidebar({ canvasActions, collapsed = false, onToggle = () => {} }) {
  const { categories: categoryList, ready } = usePrograms()
  const { look } = useSettings()
  useArtVersion()
  const [open, setOpen] = useState({})
  const [search, setSearch] = useState('')
  // "Group by family" only exists in the non-Classic looks.
  const canGroup = resolveLook(look) !== 'classic'
  const [groupBy, setGroupByState] = useState(() => { try { return localStorage.getItem('vb.sidebar.groupBy') || 'category' } catch { return 'category' } })
  const setGroupBy = (g) => { setGroupByState(g); try { localStorage.setItem('vb.sidebar.groupBy', g) } catch { /* private mode etc. */ } }
  const byFamily = canGroup && groupBy === 'family'
  const [preview, setPreview] = useState(null)   // { id, label, description, y } — only in the Output art look
  const showPreviews = canGroup                  // every non-Classic look: branded preview card instead of the system tooltip
  const categories = React.useMemo(() => {
    if (!byFamily) return categoryList
    const groups = new Map()
    for (const cat of categoryList) {
      for (const p of cat.programs) {
        const fam = familyOf(p.id, cat.id)
        if (!groups.has(fam)) groups.set(fam, { id: fam, label: FAMILIES[fam]?.label || fam, color: FAMILY_COLOR[fam] || cat.color, programs: [] })
        groups.get(fam).programs.push({ ...p, categoryId: p.categoryId || cat.id })
      }
    }
    return Object.keys(FAMILIES).filter(f => groups.has(f)).map(f => groups.get(f))
  }, [categoryList, byFamily])

  // Open all categories once data arrives (runs once when ready flips true)
  React.useEffect(() => {
    if (ready) setOpen(Object.fromEntries(categoryList.map(c => [c.id, true])))
  }, [ready]) // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = (id) => setOpen(s => ({ ...s, [id]: !s[id] }))

  const q = search.trim().toLowerCase()

  const onDragStart = (e, programId) => {
    e.dataTransfer.setData('application/videobeaux-program', programId)
    e.dataTransfer.effectAllowed = 'copy'
  }

  if (collapsed) {
    return (
      <aside style={{ width: 38, background: 'var(--paper)', borderRight: 'var(--border)', display: 'flex', flexDirection: 'column',
                      alignItems: 'center', paddingTop: 8, gap: 10, userSelect: 'none', flexShrink: 0 }}>
        <button className="node-caret" onClick={onToggle} title="Show programs (⌘B)">▸</button>
        <span style={{ writingMode: 'vertical-rl', fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.14em',
                       textTransform: 'uppercase', color: 'var(--muted-dim)' }}>Programs</span>
      </aside>
    )
  }

  return (
    <aside style={{
      width: 240,
      flexShrink: 0,
      background: 'var(--paper)',
      borderRight: 'var(--border)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      userSelect: 'none'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 10px 0' }}>
        <span style={{ flex: 1, fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--muted-dim)' }}>Programs</span>
        <button className="node-caret" onClick={onToggle} title="Hide programs (⌘B)">◂</button>
      </div>

      {canGroup && (
        <div style={{ display: 'flex', gap: 5, padding: '6px 10px 0' }}>
          {[['category', 'By category'], ['family', 'By family']].map(([id, label]) => (
            <button key={id} onClick={() => setGroupBy(id)}
                    title={id === 'family' ? 'Group modules by what they look like and do — glitch, trails, texture…' : 'Group modules by category'}
                    style={{ flex: 1, padding: '2px 4px', fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 700, borderRadius: 999,
                             background: groupBy === id ? 'var(--select)' : 'var(--paper)', color: groupBy === id ? '#080808' : 'var(--ink)',
                             border: '2px solid var(--ink)', cursor: 'pointer' }}>
              {label}
            </button>
          ))}
        </div>
      )}

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
                onClick={() => setOpen(s => ({ ...s, [cat.id]: !(s[cat.id] ?? true) }))}
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
                <span className="cat-chip" data-family={FAMILIES[cat.id] ? cat.id : familyOfCategory(cat.id)}
                      data-motif={FAMILIES[cat.id] ? undefined : (categoryMotif(cat.id) || undefined)} style={{
                  '--node-color': cat.color,
                  fontFamily: 'var(--font-mono)',
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: 'var(--on-color)',
                  backgroundColor: cat.color,
                  border: '2px solid var(--ink)',
                  borderRadius: 4,
                  padding: '1px 6px',
                  flex: 1
                }}>
                  {cat.label}
                </span>
                <span style={{ fontSize: 10, color: 'var(--ink)' }}>
                  {(open[cat.id] ?? true) ? '▾' : '▸'}
                </span>
              </button>

              {/* Programs */}
              {((open[cat.id] ?? true) || q) && (
                <div style={{ paddingBottom: 4 }}>
                  {filtered.map(prog => (
                    <div
                      key={prog.id}
                      draggable
                      onDragStart={e => onDragStart(e, prog.id)}
                      onDoubleClick={() => canvasActions?.addProgram(prog.id)}
                      title={showPreviews ? undefined : `${prog.description || prog.label}\n\nDrag onto the canvas, or double-click to add at center.`}
                      data-no-tip={showPreviews ? '' : undefined}
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
                        if (showPreviews) {
                          const r = e.currentTarget.getBoundingClientRect()
                          setPreview({ id: prog.id, label: prog.label, description: prog.description, y: Math.min(r.top, window.innerHeight - 190) })
                        }
                      }}
                      onMouseOut={e => {
                        e.currentTarget.style.background = 'transparent'
                        e.currentTarget.style.color = 'var(--ink)'
                        setPreview(null)
                      }}
                    >
                      <span className="prog-dot" data-family={familyOf(prog.id, prog.categoryId || cat.id)}
                            data-motif={motifOf(prog.id, prog.categoryId || cat.id) || undefined} style={{
                        width: 7, height: 7,
                        borderRadius: '50%',
                        backgroundColor: cat.color,
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
                              fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 700, color: 'var(--ink)',
                              background: reqCount > 0 ? 'var(--yellow)' : 'var(--gray)', border: '1.5px solid var(--ink)',
                              borderRadius: 3, padding: '1px 5px', cursor: 'help'
                            }}
                          >
                            {reqCount > 0 ? '⚙ ' : ''}{prog.args.length}
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

      {preview && (
        <div className="art-preview" style={{ left: 250, top: preview.y }}>
          {artFor(preview.id) && <img src={artFor(preview.id)} alt="" />}
          <b>{preview.label}</b>
          <span>{(preview.description || '').slice(0, 220)}</span>
          <span style={{ fontStyle: 'italic', color: 'var(--muted)' }}>Drag onto the canvas, or double-click to add.</span>
        </div>
      )}

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
