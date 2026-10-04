import React, { useState, useCallback, useEffect, useMemo, useRef } from 'react'
import {
  ReactFlow,
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  addEdge,
  Background,
  Controls,
  MiniMap,
  useReactFlow,
  useStoreApi,
  useStore,
  Panel
} from '@xyflow/react'

import InputNode  from './components/nodes/InputNode'
import EffectNode from './components/nodes/EffectNode'
import OutputNode from './components/nodes/OutputNode'
import GroupNode  from './components/nodes/GroupNode'
import ClickConnectLine from './components/ClickConnectLine'
import Sidebar    from './components/Sidebar'
import LogPanel   from './components/LogPanel'
import SetupScreen from './components/SetupScreen'
import AppearanceMenu from './components/AppearanceMenu'
import HelpWindow from './components/HelpWindow'
import ConfirmDialog from './components/ConfirmDialog'
import { ProgramsProvider, usePrograms } from './ProgramsContext'
import { SettingsProvider, useSettings } from './SettingsContext'
import { CanvasHistoryContext, useHistory } from './useCanvasHistory'
import { buildPipeline } from './pipeline'
import { useModalLocked, isModalLocked } from './useModalLock'
import { GroupContext, RealEdgesContext } from './GroupContext'
import { useGrouping, deriveGroupView } from './useGrouping'
import tvIcon from './assets/img/tv-icon.png'

const NODE_TYPES = {
  inputNode:  InputNode,
  effectNode: EffectNode,
  outputNode: OutputNode,
  groupNode:  GroupNode
}

// deletable:false keeps Input/Output safe from Backspace/Delete without
// needing to override deleteKeyCode or manually filter in onKeyDown.
const INITIAL_NODES = [
  {
    id: 'input-1',
    type: 'inputNode',
    position: { x: 80, y: 200 },
    data: { filePath: '' },
    deletable: false
  },
  {
    id: 'output-1',
    type: 'outputNode',
    position: { x: 680, y: 200 },
    data: { filePath: '', format: 'mp4' },
    deletable: false
  }
]

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Parse HH:MM:SS.xx → total seconds */
function parseHMS(h, m, s) {
  return parseInt(h, 10) * 3600 + parseInt(m, 10) * 60 + parseFloat(s)
}

/** Render one self-contained progress-bar line for the log console. */
function renderProgressLine(pct, speed) {
  const width = 28
  if (pct === null || pct === undefined) {
    return `⏳ working…${speed ? `  ${speed}` : ''}\n`
  }
  const filled = Math.round((pct / 100) * width)
  const bar = '█'.repeat(filled) + '░'.repeat(width - filled)
  return `⏳ [${bar}] ${pct}%${speed ? `  ${speed}` : ''}\n`
}

// ── Inner canvas (needs ReactFlow hooks) ────────────────────────────────────

let _nodeCounter = 2

function FlowCanvas({ isRunning, setIsRunning, setLogs, setLogCollapsed, progress, setProgress, registerCanvasActions }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES)
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const { screenToFlowPosition, getViewport, getNodes, deleteElements } = useReactFlow()
  // React Flow is shown *display* edges (collapsed groups re-route their boundary edges); logic uses the real ones.
  const edgesRef = useRef(edges)
  edgesRef.current = edges
  const flowStore = useStoreApi()
  const { programMap } = usePrograms()
  const { theme, showSelectionBar } = useSettings()
  const modalLocked = useModalLocked()
  const [runError, setRunError] = useState(null)
  const wrapperRef = useRef(null)

  // Undo / redo (⌘Z / ⇧⌘Z, or the buttons in the top-left panel)
  const getSnapshot = useCallback(() => ({ nodes: getNodes(), edges: edgesRef.current }), [getNodes])
  const restore = useCallback((snap) => {
    setNodes(snap.nodes.map(n => ({ ...n, selected: false })))
    setEdges(snap.edges.map(e => ({ ...e, selected: false })))
  }, [setNodes, setEdges])
  const { record, undo, redo, canUndo, canRedo } = useHistory({ getSnapshot, restore })

  // ── Copy / paste / duplicate ───────────────────────────────────────────────
  // ⌘C copies the selected programs (and extra Input nodes) together with the connections
  // between them; ⌘V pastes at the cursor (or offset, when pasted repeatedly); ⌘D duplicates
  // in place. The original Input/Output nodes are never copied. In-memory only.
  const clipboardRef = useRef(null)
  const mouseFlowRef = useRef(null)
  const pasteCountRef = useRef(0)

  const newId = useCallback((kind) => `${kind}-${++_nodeCounter}-${Date.now()}`, [])

  const copySelection = useCallback(() => {
    const all = getNodes()
    const byId = new Map(all.map(n => [n.id, n]))
    const chosen = new Map()
    for (const n of all.filter(n => n.selected && n.deletable !== false)) {
      chosen.set(n.id, n)
      if (n.type === 'groupNode') all.filter(m => m.parentId === n.id).forEach(m => chosen.set(m.id, m))   // a group brings its members
    }
    if (!chosen.size) return false
    const picked = [...chosen.values()].sort((a, b) => (a.type === 'groupNode' ? 0 : 1) - (b.type === 'groupNode' ? 0 : 1))   // parents first
    const ids = new Set(picked.map(n => n.id))
    clipboardRef.current = {
      nodes: picked.map(n => {
        const keepParent = n.parentId && ids.has(n.parentId)
        const parent = n.parentId ? byId.get(n.parentId) : null
        const position = n.parentId && !keepParent && parent
          ? { x: n.position.x + parent.position.x, y: n.position.y + parent.position.y }   // member copied without its group → absolute spot
          : n.position
        return structuredClone({
          oldId: n.id, type: n.type, position, data: n.data, width: n.width, height: n.height, style: n.style,
          parentId: keepParent ? n.parentId : undefined, hidden: n.hidden, draggable: n.draggable
        })
      }),
      edges: structuredClone(edgesRef.current.filter(e => ids.has(e.source) && ids.has(e.target))
        .map(e => ({ source: e.source, target: e.target, sourceHandle: e.sourceHandle, targetHandle: e.targetHandle, type: e.type })))
    }
    pasteCountRef.current = 0
    return true
  }, [getNodes])

  const pasteClipboard = useCallback((place = 'cursor') => {
    const clip = clipboardRef.current
    if (!clip || !clip.nodes.length) return
    const top = clip.nodes.filter(n => !n.parentId)
    const minX = Math.min(...top.map(n => n.position.x))
    const minY = Math.min(...top.map(n => n.position.y))
    pasteCountRef.current += 1
    const nudge = (pasteCountRef.current - 1) * 30
    const target = place === 'cursor' && mouseFlowRef.current
      ? { x: mouseFlowRef.current.x + nudge, y: mouseFlowRef.current.y + nudge }
      : { x: minX + 40 * pasteCountRef.current, y: minY + 40 * pasteCountRef.current }
    const idMap = new Map()
    const fresh = clip.nodes.map(n => {
      const id = newId(n.type === 'inputNode' ? 'input' : n.type === 'groupNode' ? 'group' : 'effect')
      idMap.set(n.oldId, id)
      const isMember = !!n.parentId
      return {
        id, type: n.type, data: structuredClone(n.data), selected: !isMember,
        position: isMember ? n.position : { x: n.position.x - minX + target.x, y: n.position.y - minY + target.y },
        ...(n.width != null ? { width: n.width } : {}), ...(n.height != null ? { height: n.height } : {}),
        ...(n.style ? { style: n.style } : {}), ...(n.hidden ? { hidden: true } : {}),
        ...(n.draggable === false ? { draggable: false } : {}),
        ...(isMember ? { parentId: idMap.get(n.parentId), expandParent: true } : {}),
        ...(n.type === 'groupNode' ? { zIndex: -1 } : {})
      }
    })
    const freshEdges = clip.edges.map((e, i) => ({
      id: `e-paste-${Date.now()}-${i}`, source: idMap.get(e.source), target: idMap.get(e.target),
      sourceHandle: e.sourceHandle, targetHandle: e.targetHandle, type: e.type || 'smoothstep'
    }))
    record()
    setNodes(nds => [...nds.map(n => (n.selected ? { ...n, selected: false } : n)), ...fresh])
    setEdges(eds => [...eds.map(e => (e.selected ? { ...e, selected: false } : e)), ...freshEdges])
  }, [record, setNodes, setEdges, newId])

  const duplicateSelection = useCallback(() => {
    if (copySelection()) pasteClipboard('offset')
  }, [copySelection, pasteClipboard])

  // ── Grouping ───────────────────────────────────────────────────────────────
  const grouping = useGrouping({ setNodes, getNodes, record, newId })
  const groupView = useMemo(() => deriveGroupView(nodes, edges, programMap), [nodes, edges, programMap])
  const groupCtx = useMemo(() => ({
    boundary: groupView.boundary, members: groupView.members,
    toggleCollapse: grouping.toggleCollapse, ungroup: grouping.ungroup,
    updateGroup: grouping.updateGroup, toggleLock: grouping.toggleLock
  }), [groupView, grouping.toggleCollapse, grouping.ungroup, grouping.updateGroup, grouping.toggleLock])
  // Edge changes on a re-routed (proxy) edge apply to the real edge underneath.
  const handleEdgesChange = useCallback((changes) => {
    onEdgesChange(changes.map(c => (typeof c.id === 'string' && c.id.startsWith('proxy:') ? { ...c, id: c.id.slice(6) } : c)))
  }, [onEdgesChange])

  // ── Clear workspace (confirmed, undoable) ──────────────────────────────────
  const [confirmClear, setConfirmClear] = useState(false)
  const clearWorkspace = useCallback((alsoPaths) => {
    record()
    const current = new Map(getNodes().map(n => [n.id, n]))
    setNodes(INITIAL_NODES.map(n => {
      const cur = current.get(n.id)
      if (!cur) return n
      return alsoPaths ? { ...n, position: cur.position } : { ...n, position: cur.position, data: cur.data }
    }))
    setEdges([])
    setRunError(null)
    setConfirmClear(false)
  }, [record, getNodes, setNodes, setEdges])

  const clearSelection = useCallback(() => {
    setNodes(ns => ns.some(n => n.selected) ? ns.map(n => (n.selected ? { ...n, selected: false } : n)) : ns)
    setEdges(es => es.some(e => e.selected) ? es.map(e => (e.selected ? { ...e, selected: false } : e)) : es)
  }, [setNodes, setEdges])

  useEffect(() => {
    const onKey = (e) => {
      if (isModalLocked()) return          // a helper window is open: it owns the keyboard
      const t = e.target
      if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' || t.isContentEditable)) return
      if (e.key === 'Escape') {
        flowStore.setState({ connectionClickStartHandle: null })
        clearSelection()
        return
      }
      if (!(e.metaKey || e.ctrlKey) || e.altKey) return
      const k = e.key.toLowerCase()
      if (k === 'z' && !e.shiftKey) { e.preventDefault(); undo() }
      else if ((k === 'z' && e.shiftKey) || k === 'y') { e.preventDefault(); redo() }
      else if (k === 'a') {
        e.preventDefault()
        setNodes(ns => ns.map(n => (n.selected ? n : { ...n, selected: true })))
      }
      else if (k === 'c') { if (copySelection()) e.preventDefault() }
      else if (k === 'v') { if (clipboardRef.current) { e.preventDefault(); pasteClipboard('cursor') } }
      else if (k === 'd') { e.preventDefault(); duplicateSelection() }
      else if (k === 'g') { e.preventDefault(); if (e.shiftKey) grouping.ungroupSelection(); else grouping.groupSelection() }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [undo, redo, clearSelection, setNodes, flowStore, copySelection, pasteClipboard, duplicateSelection, grouping])

  const connecting = useStore(st => !!st.connectionClickStartHandle)
  const selectedNodes = nodes.filter(n => n.selected)
  const selectedEdges = edges.filter(e => e.selected)
  const deletableSelected = selectedNodes.filter(n => n.deletable !== false)
  const canGroup = selectedNodes.filter(n => n.type === 'effectNode' && !n.parentId).length >= 2
  const canUngroup = selectedNodes.some(n => n.type === 'groupNode')
  const selectionCount = selectedNodes.length + selectedEdges.length
  const deleteSelection = useCallback(() => {
    deleteElements({ nodes: deletableSelected.map(n => ({ id: n.id })), edges: selectedEdges.map(e => ({ id: e.id })) })
  }, [deleteElements, deletableSelected, selectedEdges])

  // Synchronous mirror of `progress` (React state updates aren't readable
  // synchronously) and the index of the in-place-updating progress line
  // currently shown in the log console, if any.
  const progressRef = useRef(null)
  useEffect(() => { progressRef.current = progress }, [progress])
  const liveLineIndexRef = useRef(null)

  // One output socket may feed many downstream nodes (fan-out, for DAG
  // branches); one input socket may only ever receive a single connection.
  // So we dedupe by TARGET, not source — the inverse of a simple linear chain.
  const onConnect = useCallback(
    (params) => { record(); setEdges(eds => {
      const withoutOld = eds.filter(e =>
        !(e.target === params.target &&
          (e.targetHandle ?? null) === (params.targetHandle ?? null))
      )
      return addEdge({ ...params, type: 'smoothstep' }, withoutOld)
    }) },
    [setEdges, record]
  )

  const isValidConnection = useCallback(
    (conn) => conn.source !== conn.target,
    []
  )

  const onDragOver = useCallback(e => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'copy'
  }, [])

  // Shared by drag-drop (onDrop below) and double-click-to-add (Sidebar, via
  // registerCanvasActions) — the only difference between the two entry points
  // is how `position` gets computed.
  const addProgramNode = useCallback((programId, position) => {
    const id = `effect-${++_nodeCounter}-${Date.now()}`
    // Seed args with each field's default so the node's actual data matches
    // what its form fields visually show from the moment it's added —
    // otherwise a required arg with a default (e.g. a select the user never
    // touches) looks filled in but is silently missing until edited.
    const initialArgs = {}
    for (const a of (programMap[programId]?.args || [])) {
      if (a.default !== undefined) initialArgs[a.name] = a.default
    }
    record()
    setNodes(nds => [...nds, {
      id,
      type: 'effectNode',
      position,
      data: { program: programId, args: initialArgs }
    }])
  }, [setNodes, programMap, record])

  // Extra source videos are numbered "Input 2", "Input 3", … (the original
  // Input node is "Input 1" in spirit). Pick the lowest number not already
  // taken rather than counting nodes, so deleting Input 2 and adding another
  // yields Input 2 again instead of a duplicate "Input 3".
  const addInputNode = useCallback((position) => {
    const id = `input-${++_nodeCounter}-${Date.now()}`
    record()
    setNodes(nds => {
      const used = new Set([1])
      for (const n of nds) {
        if (n.type !== 'inputNode') continue
        const m = /^Input (\d+)$/.exec(n.data?.label || '')
        if (m) used.add(parseInt(m[1], 10))
      }
      let num = 2
      while (used.has(num)) num++
      return [...nds, {
        id,
        type: 'inputNode',
        position,
        data: { filePath: '', label: `Input ${num}` }
      }]
    })
  }, [setNodes, record])

  // Current visible center of the canvas in flow coordinates, with a small
  // jitter so repeated double-clicks don't stack nodes exactly on top of
  // each other.
  const viewportCenterPosition = useCallback(() => {
    const rect = wrapperRef.current?.getBoundingClientRect()
    const center = rect
      ? { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 }
      : { x: window.innerWidth / 2, y: window.innerHeight / 2 }
    const jitter = () => (Math.random() - 0.5) * 60
    return screenToFlowPosition({ x: center.x + jitter(), y: center.y + jitter() })
  }, [screenToFlowPosition])

  useEffect(() => {
    registerCanvasActions?.({
      addProgram: (programId) => addProgramNode(programId, viewportCenterPosition()),
      addInput: () => addInputNode(viewportCenterPosition())
    })
  }, [registerCanvasActions, addProgramNode, addInputNode, viewportCenterPosition])

  const onDrop = useCallback(e => {
    e.preventDefault()

    const nodeKind = e.dataTransfer.getData('application/videobeaux-node')
    if (nodeKind === 'inputNode') {
      addInputNode(screenToFlowPosition({ x: e.clientX, y: e.clientY }))
      return
    }

    const programId = e.dataTransfer.getData('application/videobeaux-program')
    if (!programId) return
    addProgramNode(programId, screenToFlowPosition({ x: e.clientX, y: e.clientY }))
  }, [screenToFlowPosition, addInputNode, addProgramNode])

  // IPC event listeners
  useEffect(() => {
    const removeLog = window.electronAPI.onLogMessage(({ text, type }) => {

      // ── FFmpeg progress stat lines (pre-classified by main process) ───────
      // The main process buffers stderr, splits on \r/\n, and sends stat lines
      // (containing time=<HH:MM:SS>) as type:'progress'. These never go into
      // the log as normal entries — instead they update one dedicated
      // "live" line in place (see liveLineIndexRef below), so the console
      // shows a single progress bar that fills in place rather than a new,
      // ever-longer line per update.
      if (type === 'progress') {
        const timeM  = text.match(/time=\s*(\d+):(\d+):(\d+\.\d+)/)
        const speedM = text.match(/speed=\s*([\d.]+)x/)
        if (timeM) {
          const current  = parseHMS(timeM[1], timeM[2], timeM[3])
          const speed    = speedM ? `${speedM[1]}×` : ''
          const duration = progressRef.current?.duration ?? null
          const pct = duration
            ? Math.min(99, Math.round((current / duration) * 100))
            : null

          setProgress(prev => (prev ? { ...prev, current, pct, speed } : null))

          const barText = renderProgressLine(pct, speed)
          setLogs(prev => {
            const idx = liveLineIndexRef.current
            if (idx !== null && prev[idx]?.type === 'progress-line') {
              const next = prev.slice()
              next[idx] = { text: barText, type: 'progress-line' }
              return next
            }
            liveLineIndexRef.current = prev.length
            return [...prev, { text: barText, type: 'progress-line' }]
          })
        }
        return
      }

      // ── Normal output ──────────────────────────────────────────────────────

      // Parse our own step-start marker:  ── Step X / Y: program_name
      const stepM = text.match(/── Step (\d+) \/ (\d+): (.+)/)
      if (stepM) {
        // Previous step's final progress line stays behind as history;
        // the next progress update starts a fresh live line.
        liveLineIndexRef.current = null
        setProgress(prev => prev && ({
          ...prev,
          step:     parseInt(stepM[1], 10),
          total:    parseInt(stepM[2], 10),
          name:     stepM[3].trim(),
          pct:      null,
          speed:    '',
          duration: null,
          current:  0,
        }))
      }

      // Parse FFmpeg's own "Duration: HH:MM:SS.ss" banner, when present
      // (only shown if a program runs ffmpeg with its stderr visible).
      const durM = text.match(/Duration:\s*(\d+):(\d+):(\d+\.\d+)/)
      if (durM) {
        const dur = parseHMS(durM[1], durM[2], durM[3])
        setProgress(prev => prev ? { ...prev, duration: dur } : null)
      }

      // Parse the videobeaux CLI's own "Input duration: N.NN seconds" line
      // (stdout, printed unconditionally by run_ffmpeg_with_progress before
      // it invokes ffmpeg) — this is the duration source that actually
      // fires in practice, since ffmpeg's own stderr banner above is
      // normally suppressed (stderr=DEVNULL) unless show_ffmpeg_output=True.
      const inputDurM = text.match(/Input duration:\s*([\d.]+)\s*seconds/)
      if (inputDurM) {
        const dur = parseFloat(inputDurM[1])
        setProgress(prev => prev ? { ...prev, duration: dur } : null)
      }

      setLogs(prev => [...prev, { text, type }])
    })

    const removeComplete = window.electronAPI.onPipelineComplete(() => {
      setIsRunning(false)
      setProgress(null)
    })

    const removeError = window.electronAPI.onPipelineError(({ message }) => {
      setIsRunning(false)
      setRunError(message)
      setProgress(null)
    })

    return () => { removeLog(); removeComplete(); removeError() }
  }, [setIsRunning, setLogs, setProgress])

  const handleRun = async () => {
    setRunError(null)
    let pipeline
    try {
      pipeline = buildPipeline(nodes, edges, programMap)
    } catch (err) {
      setRunError(err.message)
      return
    }

    // Pre-flight: ask before silently overwriting an existing output file or
    // a non-empty batch output folder. A "Cancel" here just quietly aborts —
    // same as never having clicked Run.
    const { proceed } = await window.electronAPI.confirmOverwrite({
      outputPath: pipeline.outputPath,
      isBatch: pipeline.finalProducesBatch
    })
    if (!proceed) return

    setLogs([])
    liveLineIndexRef.current = null
    setLogCollapsed(false)
    setIsRunning(true)
    // Seed progress state with total step count; step details fill in as log arrives
    setProgress({
      step: 0, total: pipeline.tasks.length, name: '',
      pct: null, speed: '', duration: null, current: 0
    })
    window.electronAPI.runPipeline(pipeline)
  }

  const handleCancel = () => {
    window.electronAPI.cancelPipeline()
    setIsRunning(false)
    setProgress(null)
    setLogs(prev => [...prev, { text: '\nCancelled by user.\n', type: 'error' }])
  }

  // Only id/type/position/data(/deletable) are persisted — everything else on
  // a React Flow node (measured, selected, dragging, …) is transient render
  // state that gets recomputed on next render, not part of the pipeline.
  const handleSave = async () => {
    const cleanNodes = nodes.map(({ id, type, position, data, deletable }) => ({
      id, type, position, data,
      ...(deletable === false ? { deletable } : {})
    }))
    const cleanEdges = edges.map(({ id, source, target, sourceHandle, targetHandle, type }) => ({
      id, source, target,
      sourceHandle: sourceHandle ?? null,
      targetHandle: targetHandle ?? null,
      type
    }))
    try {
      const savedPath = await window.electronAPI.savePreset({
        presetFormatVersion: 1,
        savedAt: new Date().toISOString(),
        nodes: cleanNodes,
        edges: cleanEdges
      })
      if (savedPath) {
        setLogs(prev => [...prev, { text: `💾 Saved preset to ${savedPath}\n`, type: 'log' }])
      }
    } catch (err) {
      setLogs(prev => [...prev, { text: `❌ Could not save preset: ${err.message}\n`, type: 'error' }])
    }
  }

  const handleLoad = async () => {
    let result
    try {
      result = await window.electronAPI.loadPreset()
    } catch (err) {
      setLogs(prev => [...prev, { text: `❌ Could not read preset file: ${err.message}\n`, type: 'error' }])
      return
    }
    if (!result) return

    const { data } = result
    if (!data || !Array.isArray(data.nodes) || !Array.isArray(data.edges)) {
      setLogs(prev => [...prev, { text: '❌ Not a valid preset file.\n', type: 'error' }])
      return
    }

    const canvasHasWork = nodes.length > 2 || edges.length > 0 ||
      nodes.some(n => n.type !== 'effectNode' && (n.data?.filePath || ''))
    if (canvasHasWork && !window.confirm('Loading a preset replaces the current canvas. Continue?')) {
      return
    }

    const missing = [...new Set(
      data.nodes.filter(n => n.type === 'effectNode' && !programMap[n.data?.program])
        .map(n => n.data?.program)
    )]
    if (missing.length) {
      setLogs(prev => [...prev, {
        text: `⚠️  Preset references unknown program(s): ${missing.join(', ')} — those nodes will show as "Unknown" until fixed or removed.\n`,
        type: 'log'
      }])
    }

    record()
    setNodes(data.nodes)
    setEdges(data.edges)
    setRunError(null)

    // Keep newly-dropped node IDs from colliding with the loaded ones.
    const maxSuffix = data.nodes.reduce((max, n) => {
      const m = /-(\d+)(?:-\d+)?$/.exec(n.id)
      return m ? Math.max(max, parseInt(m[1], 10)) : max
    }, _nodeCounter)
    _nodeCounter = maxSuffix
  }

  return (
    <CanvasHistoryContext.Provider value={{ record }}>
    <GroupContext.Provider value={groupCtx}>
    <RealEdgesContext.Provider value={edges}>
    <div
      ref={wrapperRef}
      style={{ flex: 1, position: 'relative', overflow: 'hidden' }}
      onMouseMove={e => { mouseFlowRef.current = screenToFlowPosition({ x: e.clientX, y: e.clientY }) }}
      onMouseLeave={() => { mouseFlowRef.current = null }}
    >
      <ReactFlow
        nodes={nodes}
        edges={groupView.displayEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={onConnect}
        onNodeDragStart={() => record()}
        onPaneClick={() => flowStore.setState({ connectionClickStartHandle: null })}
        onBeforeDelete={async (d) => {
          const folded = d.nodes.filter(n => n.type === 'groupNode' && n.data?.collapsed)
          if (folded.length && !window.confirm(`Delete ${folded.length === 1 ? `the group “${folded[0].data.label}”` : `${folded.length} groups`} and all the programs inside?`)) return false
          record()
          return d
        }}
        isValidConnection={isValidConnection}
        onDrop={onDrop}
        onDragOver={onDragOver}
        nodeTypes={NODE_TYPES}
        deleteKeyCode={modalLocked ? null : ['Backspace', 'Delete']}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        defaultEdgeOptions={{ type: 'smoothstep' }}
        colorMode={theme === 'dark' ? 'dark' : 'light'}
      >
        <ClickConnectLine />
        <Background color={theme === 'dark' ? '#34323c' : '#d8d4c2'} gap={24} size={1.5} />
        <Controls />
        <MiniMap
          nodeColor={n => {
            if (n.type === 'inputNode')  return '#32b9df'
            if (n.type === 'outputNode') return '#ff6847'
            const prog = programMap[n.data?.program]
            return prog?.categoryColor || '#8a8a80'
          }}
          maskColor={theme === 'dark' ? 'rgba(243,241,231,0.25)' : 'rgba(8,8,8,0.35)'}
        />

        {/* Save / Load preset panel */}
        <Panel position="top-left">
          <div style={{ display: 'flex', gap: 6 }}>
            {[['↶ Undo', undo, canUndo, 'Undo (⌘Z)'], ['↷ Redo', redo, canRedo, 'Redo (⇧⌘Z)']].map(([label, fn, enabled, tip]) => (
              <button
                key={label}
                onClick={fn}
                disabled={!enabled || isRunning}
                title={tip}
                style={{
                  background: 'var(--paper)', color: 'var(--ink)',
                  padding: '9px 12px', borderRadius: 'var(--radius-sm)',
                  fontFamily: 'var(--font-display)', fontSize: 12,
                  border: 'var(--border)', boxShadow: 'var(--shadow-sm)',
                  opacity: (!enabled || isRunning) ? 0.4 : 1, cursor: (!enabled || isRunning) ? 'not-allowed' : 'pointer'
                }}
                onMouseDown={e => { if (enabled && !isRunning) { e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'translate(3px, 3px)' } }}
                onMouseUp={e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }}
                onMouseLeave={e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }}
              >
                {label}
              </button>
            ))}
            <button
              onClick={handleSave}
              disabled={isRunning}
              style={{
                background: 'var(--paper)', color: 'var(--ink)',
                padding: '9px 16px', borderRadius: 'var(--radius-sm)',
                fontFamily: 'var(--font-display)', fontSize: 12,
                border: 'var(--border)', boxShadow: 'var(--shadow-sm)',
                opacity: isRunning ? 0.5 : 1, cursor: isRunning ? 'not-allowed' : 'pointer'
              }}
              onMouseDown={e => { if (!isRunning) { e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'translate(3px, 3px)' } }}
              onMouseUp={e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }}
              onMouseLeave={e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }}
            >
              💾 Save Preset
            </button>
            <button
              onClick={handleLoad}
              disabled={isRunning}
              style={{
                background: 'var(--paper)', color: 'var(--ink)',
                padding: '9px 16px', borderRadius: 'var(--radius-sm)',
                fontFamily: 'var(--font-display)', fontSize: 12,
                border: 'var(--border)', boxShadow: 'var(--shadow-sm)',
                opacity: isRunning ? 0.5 : 1, cursor: isRunning ? 'not-allowed' : 'pointer'
              }}
              onMouseDown={e => { if (!isRunning) { e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'translate(3px, 3px)' } }}
              onMouseUp={e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }}
              onMouseLeave={e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }}
            >
              📂 Load Preset
            </button>
            <button
              onClick={() => setConfirmClear(true)}
              disabled={isRunning}
              title="Clear the workspace (asks first; ⌘Z undoes)"
              style={{
                background: 'var(--paper)', color: 'var(--ink)',
                padding: '9px 14px', borderRadius: 'var(--radius-sm)',
                fontFamily: 'var(--font-display)', fontSize: 12,
                border: 'var(--border)', boxShadow: 'var(--shadow-sm)',
                opacity: isRunning ? 0.5 : 1, cursor: isRunning ? 'not-allowed' : 'pointer'
              }}
              onMouseDown={e => { if (!isRunning) { e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'translate(3px, 3px)' } }}
              onMouseUp={e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }}
              onMouseLeave={e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }}
            >
              🗑 Clear
            </button>
          </div>
        </Panel>

        {/* Run / Cancel panel */}
        <Panel position="top-right">
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
            {isRunning ? (
              <button
                onClick={handleCancel}
                style={{
                  background: 'var(--coral)', color: '#080808',
                  padding: '9px 20px', borderRadius: 'var(--radius-sm)',
                  fontFamily: 'var(--font-display)', fontSize: 12,
                  border: 'var(--border)', boxShadow: 'var(--shadow-sm)'
                }}
                onMouseDown={e => { e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'translate(3px, 3px)' }}
                onMouseUp={e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }}
                onMouseLeave={e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }}
              >
                ■ Cancel
              </button>
            ) : (
              <button
                onClick={handleRun}
                style={{
                  background: 'var(--yellow)', color: '#080808',
                  padding: '9px 20px', borderRadius: 'var(--radius-sm)',
                  fontFamily: 'var(--font-display)', fontSize: 12,
                  border: 'var(--border)', boxShadow: 'var(--shadow-sm)'
                }}
                onMouseDown={e => { e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'translate(3px, 3px)' }}
                onMouseUp={e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }}
                onMouseLeave={e => { e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; e.currentTarget.style.transform = 'none' }}
              >
                ▶ Run Pipeline
              </button>
            )}

            {runError && (
              <div style={{
                background: 'var(--paper)', border: '2px solid var(--coral)',
                borderRadius: 'var(--radius-sm)', padding: '7px 12px',
                fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--coral)',
                maxWidth: 300, lineHeight: 1.5, boxShadow: 'var(--shadow-sm)'
              }}>
                {runError}
              </div>
            )}
          </div>
        </Panel>

        {selectionCount > 0 && showSelectionBar && (
          <Panel position="bottom-left" style={{ marginLeft: 56, marginBottom: 12 }}>
            <div className="selection-pill">
              <span className="selection-pill__count" title={`${selectedNodes.length} program(s), ${selectedEdges.length} connection(s) selected`}>
                {selectionCount} selected
              </span>
              <button onClick={() => { copySelection() }} disabled={deletableSelected.length === 0}
                      title="Copy (⌘C) — then paste with ⌘V">⎘</button>
              <button onClick={duplicateSelection} disabled={isRunning || deletableSelected.length === 0}
                      title="Duplicate (⌘D)">⧉</button>
              {canGroup && (
                <button onClick={grouping.groupSelection} disabled={isRunning} title="Group the selected programs (⌘G)">▣ Group</button>
              )}
              {canUngroup && (
                <button onClick={grouping.ungroupSelection} disabled={isRunning} title="Ungroup (⇧⌘G)">⇱ Ungroup</button>
              )}
              <button className="selection-pill__delete" onClick={deleteSelection}
                      disabled={isRunning || (deletableSelected.length === 0 && selectedEdges.length === 0)}
                      title="Delete (Backspace / Delete)">⌫</button>
              <button onClick={clearSelection} title="Deselect (Esc)">✕</button>
            </div>
          </Panel>
        )}

      </ReactFlow>
      {confirmClear && (
        <ConfirmDialog
          title="Clear the workspace?"
          danger
          confirmLabel="Clear"
          message={<>
            This removes {nodes.filter(n => n.type === 'effectNode').length} program(s)
            {nodes.some(n => n.type === 'groupNode') ? `, ${nodes.filter(n => n.type === 'groupNode').length} group(s)` : ''}
            {nodes.filter(n => n.type === 'inputNode' && n.deletable !== false).length ? ', the extra inputs' : ''} and {edges.length} connection(s).
            You can undo it with ⌘Z.
          </>}
          checkboxLabel="Also clear the Input / Output file paths"
          onConfirm={clearWorkspace}
          onCancel={() => setConfirmClear(false)}
        />
      )}
    </div>
    </RealEdgesContext.Provider>
    </GroupContext.Provider>
    </CanvasHistoryContext.Provider>
  )
}

// ── App root ─────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <SettingsProvider>
      <ProgramsProvider>
        <AppInner />
      </ProgramsProvider>
    </SettingsProvider>
  )
}

function AppInner() {
  const [logs, setLogs]                 = useState([])
  const [isRunning, setIsRunning]       = useState(false)
  // progress: null when idle, object while running
  // { step, total, name, pct (0-100|null), speed, duration (s|null), current (s) }
  const [progress, setProgress]         = useState(null)
  const [showSetup, setShowSetup]       = useState(false)
  const [showHelp, setShowHelp]         = useState(false)
  const { sidebarCollapsed, setSidebarCollapsed, consoleCollapsed, setConsoleCollapsed } = useSettings()
  const logCollapsed = consoleCollapsed
  const setLogCollapsed = useCallback((v) => setConsoleCollapsed(typeof v === 'function' ? v(consoleCollapsed) : v), [consoleCollapsed, setConsoleCollapsed])
  // Set by FlowCanvas once it's mounted (it owns node state) — lets Sidebar
  // add a node via double-click without prop-drilling node state itself.
  const [canvasActions, setCanvasActions] = useState(null)
  const registerCanvasActions = useCallback(actions => setCanvasActions(actions), [])


  // App-level shortcuts: ⌘B programs list, ⌘J console, F1 / ? help.
  useEffect(() => {
    const onKey = (e) => {
      if (isModalLocked()) return
      const t = e.target
      const typing = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' || t.isContentEditable)
      if (e.key === 'F1' || (e.key === '?' && !typing && !e.metaKey && !e.ctrlKey)) { e.preventDefault(); setShowHelp(true); return }
      if (!(e.metaKey || e.ctrlKey) || e.altKey || e.shiftKey || typing) return
      const k = e.key.toLowerCase()
      if (k === 'b') { e.preventDefault(); setSidebarCollapsed(!sidebarCollapsed) }
      else if (k === 'j') { e.preventDefault(); setConsoleCollapsed(!consoleCollapsed) }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [sidebarCollapsed, consoleCollapsed, setSidebarCollapsed, setConsoleCollapsed])

  // Show Setup the first time the app runs (to offer the optional local-AI downloads) and any
  // time the core engine isn't ready (fresh clone, broken install) — it then repairs itself.
  const { ready: settingsReady, setupSeen } = useSettings()
  useEffect(() => {
    if (!settingsReady) return
    window.electronAPI.checkEnvironment().then(env => {
      if (!env.ready || !setupSeen) setShowSetup(true)
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [settingsReady])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* Header — left padding clears the macOS traffic-light buttons, which
          float over the content area under titleBarStyle:'hiddenInset'. */}
      <header style={{
        height: 52, background: 'var(--paper)', borderBottom: 'var(--border)',
        display: 'flex', alignItems: 'center', padding: '0 16px 0 84px', gap: 10,
        flexShrink: 0, WebkitAppRegion: 'drag'
      }}>
        <img src={tvIcon} alt="" width={32} height={32} style={{ flexShrink: 0 }} />
        <span style={{
          fontFamily: 'var(--font-display)',
          fontSize: 17, letterSpacing: '0.01em', color: 'var(--ink)'
        }}>
          videobeaux
        </span>
        <span style={{
          fontFamily: 'var(--font-mono)', fontWeight: 600,
          fontSize: 10, letterSpacing: '0.06em', textTransform: 'uppercase',
          color: 'var(--paper)', background: 'var(--purple)',
          border: '2px solid var(--ink)', borderRadius: 5, padding: '2px 6px'
        }}>
          by schwwaaa
        </span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, WebkitAppRegion: 'no-drag' }}>
          <AppearanceMenu />
          <button
            onClick={() => setShowSetup(true)}
            style={{
              background: 'var(--paper)', color: 'var(--ink)',
              padding: '5px 10px', borderRadius: 'var(--radius-sm)',
              fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 11,
              border: '2px solid var(--ink)', cursor: 'pointer'
            }}
          >
            ⚙ Setup
          </button>
          <button
            onClick={() => setShowHelp(true)}
            title="Help (F1)"
            aria-label="Help"
            style={{
              background: 'var(--paper)', color: 'var(--ink)',
              width: 30, padding: '5px 0', borderRadius: 'var(--radius-sm)',
              fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 13,
              border: '2px solid var(--ink)', cursor: 'pointer'
            }}
          >
            ?
          </button>
        </div>
      </header>

      {showSetup && <SetupScreen onClose={() => setShowSetup(false)} />}
      {showHelp && <HelpWindow onClose={() => setShowHelp(false)} />}

      {/* Main body */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0 }}>
        <Sidebar canvasActions={canvasActions} collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
          <ReactFlowProvider>
            <FlowCanvas
              registerCanvasActions={registerCanvasActions}
              isRunning={isRunning}
              setIsRunning={setIsRunning}
              setLogs={setLogs}
              setLogCollapsed={setLogCollapsed}
              progress={progress}
              setProgress={setProgress}
            />
          </ReactFlowProvider>

          <LogPanel
            logs={logs}
            isRunning={isRunning}
            progress={progress}
            collapsed={logCollapsed}
            onToggle={() => setConsoleCollapsed(!consoleCollapsed)}
            onClear={() => setLogs([])}
          />
        </div>
      </div>
    </div>
  )
}
