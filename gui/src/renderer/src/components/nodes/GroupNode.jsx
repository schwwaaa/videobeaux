import React, { useEffect } from 'react'
import { Handle, NodeResizer, Position, useUpdateNodeInternals } from '@xyflow/react'
import { useGroupContext } from '../../GroupContext'
import { GROUP_COLORS } from '../../useGrouping'

const HANDLE_TOP = 58
const HANDLE_GAP = 20

/**
 * A group of programs. Expanded: a tinted, dashed container that moves all its members together.
 * Collapsed: one compact card (name, member chips) with a handle per connection that crosses its boundary.
 */
export default function GroupNode({ id, data, selected }) {
  const { boundary, members, toggleCollapse, ungroup, updateGroup, toggleLock } = useGroupContext()
  const updateNodeInternals = useUpdateNodeInternals()
  const b = boundary[id] || { ins: [], outs: [] }
  const list = members[id] || []
  const color = data.color || GROUP_COLORS[0]
  const sig = `${b.ins.join(',')}|${b.outs.join(',')}|${data.collapsed}`
  useEffect(() => { updateNodeInternals(id) }, [sig, id, updateNodeInternals])

  const header = (
    <div style={{
      background: color, color: 'var(--on-color)', borderBottom: '3px solid var(--ink)',
      borderRadius: data.collapsed ? '9px 9px 0 0' : '9px 9px 0 0',
      padding: '5px 6px 5px 8px', display: 'flex', alignItems: 'center', gap: 6, minHeight: 34, userSelect: 'none'
    }}>
      <span style={{ fontSize: 12 }}>▣</span>
      <input
        className="nodrag"
        value={data.label || ''}
        onChange={e => updateGroup(id, { label: e.target.value })}
        onKeyDown={e => e.stopPropagation()}
        title="Rename group"
        style={{
          flex: 1, minWidth: 0, background: 'transparent', border: '2px solid transparent', color: 'var(--on-color)',
          fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase',
          padding: '1px 3px', borderRadius: 4
        }}
        onFocus={e => { e.currentTarget.style.borderColor = '#080808'; e.currentTarget.style.background = 'rgba(255,253,246,0.55)' }}
        onBlur={e => { e.currentTarget.style.borderColor = 'transparent'; e.currentTarget.style.background = 'transparent' }}
      />
      {!data.collapsed && (
        <button className="nodrag node-caret" onClick={() => toggleLock(id)} style={{ background: data.locked ? 'var(--yellow)' : undefined }}
                title={data.locked ? 'Locked: members move only with the group. Click to unlock.' : 'Lock members together'}>
          {data.locked ? '🔒' : '🔓'}
        </button>
      )}
      <button className="nodrag node-caret" onClick={() => ungroup(id)} title="Ungroup (⇧⌘G)">⇱</button>
      <button className="nodrag node-caret" onClick={() => toggleCollapse(id)} title={data.collapsed ? 'Expand group' : 'Collapse group into one card'}>
        {data.collapsed ? '▸' : '▾'}
      </button>
    </div>
  )

  if (data.collapsed) {
    const rows = Math.max(b.ins.length, b.outs.length)
    return (
      <div style={{
        width: 230, minHeight: Math.max(96, HANDLE_TOP + rows * HANDLE_GAP + 8), background: 'var(--paper)',
        border: '3px solid var(--ink)', borderRadius: 12, boxShadow: 'var(--shadow)', position: 'relative'
      }}>
        {header}
        <div style={{ padding: '8px 10px', display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {list.map((m, i) => (
            <span key={i} title={m.label} style={{
              background: m.color, color: 'var(--on-color)', border: '2px solid var(--ink)', borderRadius: 4,
              padding: '0 5px', fontFamily: 'var(--font-mono)', fontSize: 9, fontWeight: 700, textTransform: 'uppercase',
              maxWidth: 130, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
            }}>{m.label}</span>
          ))}
        </div>
        <div style={{ padding: '0 10px 8px', fontSize: 10, color: 'var(--muted-dim)', fontFamily: 'var(--font-mono)' }}>
          {list.length} program{list.length === 1 ? '' : 's'} · {b.ins.length} in · {b.outs.length} out
        </div>
        {b.ins.map((eid, i) => (
          <Handle key={`in:${eid}`} id={`in:${eid}`} type="target" position={Position.Left} isConnectable={false}
                  style={{ top: HANDLE_TOP + i * HANDLE_GAP, background: color, borderColor: 'var(--ink)', borderWidth: 2 }} />
        ))}
        {b.outs.map((eid, i) => (
          <Handle key={`out:${eid}`} id={`out:${eid}`} type="source" position={Position.Right} isConnectable={false}
                  style={{ top: HANDLE_TOP + i * HANDLE_GAP, background: color, borderColor: 'var(--ink)', borderWidth: 2 }} />
        ))}
      </div>
    )
  }

  return (
    <div style={{
      width: '100%', height: '100%', borderRadius: 12, border: `3px dashed ${color}`, background: `${color}1f`
    }}>
      <NodeResizer isVisible={selected} minWidth={240} minHeight={140} color={color} />
      {header}
      <div style={{ display: 'flex', gap: 5, padding: '5px 8px' }}>
        {GROUP_COLORS.map(c => (
          <button key={c} className="nodrag" title="Group color" onClick={() => updateGroup(id, { color: c })}
                  style={{ width: 14, height: 14, padding: 0, borderRadius: '50%', background: c,
                           border: c === color ? '3px solid var(--ink)' : '2px solid var(--ink)' }} />
        ))}
      </div>
    </div>
  )
}
