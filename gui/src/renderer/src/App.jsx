import React, { useState, useCallback, useEffect } from 'react'
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
  Panel
} from '@xyflow/react'

import InputNode  from './components/nodes/InputNode'
import EffectNode from './components/nodes/EffectNode'
import OutputNode from './components/nodes/OutputNode'
import Sidebar    from './components/Sidebar'
import LogPanel   from './components/LogPanel'
import { ProgramsProvider, usePrograms } from './ProgramsContext'

const NODE_TYPES = {
  inputNode:  InputNode,
  effectNode: EffectNode,
  outputNode: OutputNode
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

// ── Pipeline builder ─────────────────────────────────────────────────────────

function buildPipeline(nodes, edges, programMap) {
  const inputNode  = nodes.find(n => n.type === 'inputNode')
  const outputNode = nodes.find(n => n.type === 'outputNode')

  if (!inputNode)  throw new Error('No Input node found on the canvas.')
  if (!outputNode) throw new Error('No Output node found on the canvas.')
  if (!inputNode.data.filePath)  throw new Error('Input node: no video file selected.')
  if (!outputNode.data.filePath) throw new Error('Output node: no output path set.')

  const adj = {}
  edges.forEach(e => {
    if (!adj[e.source]) adj[e.source] = []
    adj[e.source].push(e.target)
  })

  const steps = []
  let currentId = inputNode.id
  const visited = new Set()

  while (currentId !== outputNode.id) {
    if (visited.has(currentId)) throw new Error('Cycle detected in the pipeline.')
    visited.add(currentId)

    const nextIds = adj[currentId]
    if (!nextIds || nextIds.length === 0) {
      throw new Error('Pipeline is not fully connected from Input to Output.')
    }
    if (nextIds.length > 1) {
      throw new Error('Branching pipelines are not yet supported. Each node should connect to exactly one next node.')
    }

    const nextId   = nextIds[0]
    const nextNode = nodes.find(n => n.id === nextId)
    if (!nextNode) throw new Error(`Node ${nextId} not found.`)

    if (nextNode.type === 'effectNode') {
      const prog = programMap?.[nextNode.data.program]
      steps.push({
        program:    nextNode.data.program,
        args:       nextNode.data.args || {},
        outputType: prog?.outputType || 'video'
      })
    }

    currentId = nextId
  }

  return {
    inputPath:  inputNode.data.filePath,
    outputPath: outputNode.data.filePath,
    steps
  }
}

// ── Inner canvas (needs ReactFlow hooks) ────────────────────────────────────

let _nodeCounter = 2

function FlowCanvas({ isRunning, setIsRunning, setLogs, setLogCollapsed, setProgress }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES)
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const { screenToFlowPosition } = useReactFlow()
  const { programMap } = usePrograms()
  const [runError, setRunError] = useState(null)

  const onConnect = useCallback(
    (params) => setEdges(eds => {
      const withoutOld = eds.filter(e =>
        !(e.source === params.source &&
          (e.sourceHandle ?? null) === (params.sourceHandle ?? null))
      )
      return addEdge({ ...params, type: 'smoothstep' }, withoutOld)
    }),
    [setEdges]
  )

  const onDragOver = useCallback(e => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'copy'
  }, [])

  const onDrop = useCallback(e => {
    e.preventDefault()
    const programId = e.dataTransfer.getData('application/videobeaux-program')
    if (!programId) return
    const position = screenToFlowPosition({ x: e.clientX, y: e.clientY })
    const id = `effect-${++_nodeCounter}-${Date.now()}`
    setNodes(nds => [...nds, {
      id,
      type: 'effectNode',
      position,
      data: { program: programId, args: {} }
    }])
  }, [screenToFlowPosition, setNodes])

  // IPC event listeners
  useEffect(() => {
    const removeLog = window.electronAPI.onLogMessage(({ text, type }) => {

      // ── FFmpeg progress stat lines (pre-classified by main process) ───────
      // The main process buffers stderr, splits on \r/\n, and sends stat lines
      // (containing frame=<digits>) as type:'progress'.  We never log them.
      if (type === 'progress') {
        const timeM  = text.match(/time=\s*(\d+):(\d+):(\d+\.\d+)/)
        const speedM = text.match(/speed=\s*([\d.]+)x/)
        if (timeM) {
          const current = parseHMS(timeM[1], timeM[2], timeM[3])
          const speed   = speedM ? `${speedM[1]}×` : ''
          setProgress(prev => {
            if (!prev) return null
            const pct = prev.duration
              ? Math.min(99, Math.round((current / prev.duration) * 100))
              : null
            return { ...prev, current, pct, speed }
          })
        }
        return
      }

      // ── Normal output ──────────────────────────────────────────────────────

      // Parse our own step-start marker:  ── Step X / Y: program_name
      const stepM = text.match(/── Step (\d+) \/ (\d+): (.+)/)
      if (stepM) {
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

      // Parse FFmpeg Duration: so we can calculate % within a step
      const durM = text.match(/Duration:\s*(\d+):(\d+):(\d+\.\d+)/)
      if (durM) {
        const dur = parseHMS(durM[1], durM[2], durM[3])
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

  const handleRun = () => {
    setRunError(null)
    try {
      const pipeline = buildPipeline(nodes, edges, programMap)
      setLogs([])
      setLogCollapsed(false)
      setIsRunning(true)
      // Seed progress state with total step count; step details fill in as log arrives
      setProgress({
        step: 0, total: pipeline.steps.length, name: '',
        pct: null, speed: '', duration: null, current: 0
      })
      window.electronAPI.runPipeline(pipeline)
    } catch (err) {
      setRunError(err.message)
    }
  }

  const handleCancel = () => {
    window.electronAPI.cancelPipeline()
    setIsRunning(false)
    setProgress(null)
    setLogs(prev => [...prev, { text: '\nCancelled by user.\n', type: 'error' }])
  }

  return (
    <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onDrop={onDrop}
        onDragOver={onDragOver}
        nodeTypes={NODE_TYPES}
        deleteKeyCode={['Backspace', 'Delete']}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        defaultEdgeOptions={{ type: 'smoothstep' }}
        colorMode="dark"
      >
        <Background color="#1e1e1e" gap={24} size={1} />
        <Controls />
        <MiniMap
          nodeColor={n => {
            if (n.type === 'inputNode')  return '#22c55e'
            if (n.type === 'outputNode') return '#ef4444'
            const prog = programMap[n.data?.program]
            return prog?.categoryColor || '#555'
          }}
          maskColor="rgba(0,0,0,0.6)"
        />

        {/* Run / Cancel panel */}
        <Panel position="top-right">
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
            {isRunning ? (
              <button
                onClick={handleCancel}
                style={{
                  background: '#ef4444', color: '#fff',
                  padding: '8px 20px', borderRadius: 6,
                  fontWeight: 700, fontSize: 13, border: 'none',
                  cursor: 'pointer', boxShadow: '0 2px 8px rgba(239,68,68,0.4)'
                }}
              >
                ■ Cancel
              </button>
            ) : (
              <button
                onClick={handleRun}
                style={{
                  background: '#22c55e', color: '#0f0f0f',
                  padding: '8px 20px', borderRadius: 6,
                  fontWeight: 700, fontSize: 13, border: 'none',
                  cursor: 'pointer', boxShadow: '0 2px 8px rgba(34,197,94,0.35)'
                }}
              >
                ▶ Run Pipeline
              </button>
            )}

            {runError && (
              <div style={{
                background: '#1a0a0a', border: '1px solid #ef444488',
                borderRadius: 6, padding: '7px 12px',
                fontSize: 12, color: '#ef4444', maxWidth: 300, lineHeight: 1.5
              }}>
                {runError}
              </div>
            )}
          </div>
        </Panel>

        <Panel position="bottom-center">
          <div style={{ fontSize: 11, color: '#2a2a2a', pointerEvents: 'none' }}>
            Drag programs from the sidebar → connect → Run Pipeline
          </div>
        </Panel>
      </ReactFlow>
    </div>
  )
}

// ── App root ─────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <ProgramsProvider>
      <AppInner />
    </ProgramsProvider>
  )
}

function AppInner() {
  const [logs, setLogs]                 = useState([])
  const [isRunning, setIsRunning]       = useState(false)
  const [logCollapsed, setLogCollapsed] = useState(false)
  // progress: null when idle, object while running
  // { step, total, name, pct (0-100|null), speed, duration (s|null), current (s) }
  const [progress, setProgress]         = useState(null)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* Header */}
      <header style={{
        height: 44, background: '#111', borderBottom: '1px solid #1e1e1e',
        display: 'flex', alignItems: 'center', padding: '0 16px', gap: 12,
        flexShrink: 0, WebkitAppRegion: 'drag'
      }}>
        <span style={{
          fontSize: 15, fontWeight: 800, letterSpacing: '0.04em',
          background: 'linear-gradient(90deg, #22c55e, #06b6d4)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'
        }}>
          videobeaux
        </span>
        <span style={{ fontSize: 11, color: '#333', fontStyle: 'italic' }}>
          node editor
        </span>
      </header>

      {/* Main body */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0 }}>
        <Sidebar />

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
          <ReactFlowProvider>
            <FlowCanvas
              isRunning={isRunning}
              setIsRunning={setIsRunning}
              setLogs={setLogs}
              setLogCollapsed={setLogCollapsed}
              setProgress={setProgress}
            />
          </ReactFlowProvider>

          <LogPanel
            logs={logs}
            isRunning={isRunning}
            progress={progress}
            collapsed={logCollapsed}
            onToggle={() => setLogCollapsed(c => !c)}
            onClear={() => setLogs([])}
          />
        </div>
      </div>
    </div>
  )
}
