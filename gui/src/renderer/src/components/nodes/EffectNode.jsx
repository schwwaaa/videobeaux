import React, { useState } from 'react'
import { Handle, Position, useReactFlow } from '@xyflow/react'
import { usePrograms } from '../../ProgramsContext'

// ── Arg field renderer ──────────────────────────────────────────────────────

function ArgField({ arg, value, onChange }) {
  const inputStyle = {
    width: '100%',
    padding: '4px 7px',
    fontSize: 12,
    background: '#111',
    border: '1px solid #333',
    borderRadius: 5,
    color: '#e0e0e0'
  }

  if (arg.type === 'file') {
    // subtype:'dir' → open a folder picker, otherwise file picker
    const isDir = arg.subtype === 'dir'

    const handleBrowse = async () => {
      const picked = isDir
        ? await window.electronAPI.openDirectory()
        : await window.electronAPI.openFile([{ name: 'All Files', extensions: ['*'] }])
      if (picked != null) onChange(picked)
    }

    return (
      <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
        <input
          className="nodrag"
          type="text"
          style={{ ...inputStyle, flex: 1, minWidth: 0 }}
          value={value || ''}
          placeholder={isDir ? 'Directory path…' : 'File path…'}
          onChange={e => onChange(e.target.value)}
          title={value || ''}
        />
        <button
          className="nodrag"
          onClick={handleBrowse}
          title={isDir ? 'Choose directory' : 'Choose file'}
          style={{
            background: '#2a2a2a',
            border: '1px solid #444',
            borderRadius: 5,
            color: '#aaa',
            padding: '4px 8px',
            fontSize: 11,
            cursor: 'pointer',
            flexShrink: 0
          }}
        >
          …
        </button>
      </div>
    )
  }

  if (arg.type === 'select') {
    return (
      <select
        className="nodrag"
        style={{ ...inputStyle, cursor: 'pointer' }}
        value={value !== undefined && value !== '' ? value : (arg.default || arg.choices[0])}
        onChange={e => onChange(e.target.value)}
      >
        {arg.choices.map(c => <option key={c} value={c}>{c}</option>)}
      </select>
    )
  }

  if (arg.type === 'number') {
    return (
      <input
        className="nodrag"
        type="number"
        style={inputStyle}
        value={value !== undefined && value !== '' ? value : (arg.default !== undefined ? arg.default : '')}
        min={arg.min}
        max={arg.max}
        step={arg.step || 'any'}
        placeholder={arg.default !== undefined ? String(arg.default) : ''}
        onChange={e => onChange(e.target.value)}
      />
    )
  }

  if (arg.type === 'checkbox') {
    return (
      <label className="nodrag" style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
        <input
          type="checkbox"
          className="nodrag"
          checked={!!value}
          onChange={e => onChange(e.target.checked)}
          style={{ accentColor: '#22c55e', cursor: 'pointer' }}
        />
        <span style={{ fontSize: 11, color: '#aaa' }}>Enabled</span>
      </label>
    )
  }

  // default: text
  return (
    <input
      className="nodrag"
      type="text"
      style={inputStyle}
      value={value || ''}
      placeholder={arg.default !== undefined ? String(arg.default) : ''}
      onChange={e => onChange(e.target.value)}
    />
  )
}

// ── EffectNode ──────────────────────────────────────────────────────────────

export default function EffectNode({ id, data, selected }) {
  const { updateNodeData, deleteElements } = useReactFlow()
  const { programMap }     = usePrograms()
  const [expanded, setExpanded] = useState(true)

  const prog = programMap[data.program]
  if (!prog) return <div style={{ color: 'red', padding: 8 }}>Unknown: {data.program}</div>

  const color = prog.categoryColor || '#888'
  const args  = prog.args || []

  const setArg = (name, value) => {
    updateNodeData(id, { args: { ...(data.args || {}), [name]: value } })
  }

  const handleDelete = (e) => {
    e.stopPropagation()
    deleteElements({ nodes: [{ id }] })
  }

  // Selected: brighter border + subtle glow
  const borderColor = selected ? color : `${color}55`
  const boxShadow   = selected
    ? `0 0 0 2px ${color}88, 0 4px 16px rgba(0,0,0,0.5)`
    : `0 0 0 1px ${color}10, 0 4px 16px rgba(0,0,0,0.4)`

  return (
    <div style={{
      background: '#1e1e1e',
      border: `1px solid ${borderColor}`,
      borderRadius: 8,
      minWidth: 230,
      maxWidth: 280,
      boxShadow,
      transition: 'border-color 0.1s, box-shadow 0.1s'
    }}>
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: color, borderColor: '#0f0f0f' }}
      />

      {/* Header */}
      <div
        style={{
          background: `${color}18`,
          borderBottom: `1px solid ${color}33`,
          borderRadius: args.length > 0 ? '7px 7px 0 0' : 7,
          padding: '7px 8px 7px 10px',
          display: 'flex',
          alignItems: 'center',
          gap: 7,
          cursor: args.length > 0 ? 'pointer' : 'default',
          userSelect: 'none'
        }}
        onClick={() => args.length > 0 && setExpanded(x => !x)}
      >
        {/* Colour dot */}
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />

        {/* Program label */}
        <span style={{
          fontSize: 11, fontWeight: 700,
          letterSpacing: '0.07em',
          textTransform: 'uppercase',
          color,
          flex: 1
        }}>
          {prog.label}
        </span>

        {/* Collapse chevron */}
        {args.length > 0 && (
          <span style={{
            fontSize: 10, color: '#555',
            transform: expanded ? 'rotate(0deg)' : 'rotate(-90deg)',
            transition: 'transform 0.15s',
            marginRight: 4
          }}>▼</span>
        )}

        {/* Delete button */}
        <button
          className="nodrag"
          onClick={handleDelete}
          title="Remove node"
          style={{
            background: 'transparent',
            border: 'none',
            color: '#444',
            fontSize: 14,
            lineHeight: 1,
            padding: '0 2px',
            cursor: 'pointer',
            borderRadius: 3,
            flexShrink: 0,
            display: 'flex',
            alignItems: 'center',
            transition: 'color 0.1s'
          }}
          onMouseEnter={e => e.currentTarget.style.color = '#ef4444'}
          onMouseLeave={e => e.currentTarget.style.color = '#444'}
        >
          ✕
        </button>
      </div>

      {/* Arg fields */}
      {args.length > 0 && expanded && (
        <div style={{ padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 7 }}>
          {args.map(arg => (
            <div key={arg.name}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 3 }}>
                <span style={{ fontSize: 11, color: '#999' }}>{arg.label}</span>
                {arg.required && <span style={{ fontSize: 10, color: '#ef4444' }}>*</span>}
                {arg.help && (
                  <span
                    title={arg.help}
                    style={{
                      fontSize: 9,
                      color: '#3b82f6',
                      cursor: 'help',
                      lineHeight: 1,
                      opacity: 0.7,
                      userSelect: 'none'
                    }}
                  >
                    ⓘ
                  </span>
                )}
              </div>
              <ArgField
                arg={arg}
                value={(data.args || {})[arg.name]}
                onChange={v => setArg(arg.name, v)}
              />
            </div>
          ))}
        </div>
      )}

      {/* No-args description */}
      {args.length === 0 && (
        <div style={{ padding: '6px 10px 8px', fontSize: 11, color: '#555', fontStyle: 'italic' }}>
          {prog.description}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Right}
        style={{ background: color, borderColor: '#0f0f0f' }}
      />
    </div>
  )
}
