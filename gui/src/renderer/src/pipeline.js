/**
 * Shared pipeline helpers — used by both the DAG builder (buildPipeline,
 * below) and EffectNode.jsx (which must agree on exactly which args render
 * a connectable graph handle, or the two would drift out of sync).
 */

/** Args that are both a file picker AND a connectable video-input handle. */
export function videoArgsOf(prog) {
  return (prog?.args || []).filter(a => a.type === 'file' && a.subtype === 'video')
}

// Synthetic key for a node's default/unnamed target handle (the "main"
// video input every effect/output node has).
const PRIMARY = '__primary__'

function describe(node) {
  if (!node) return 'Unknown node'
  if (node.type === 'inputNode') {
    const fname = node.data?.filePath ? node.data.filePath.split(/[\\/]/).pop() : null
    return node.data?.label || fname || 'Input node'
  }
  if (node.type === 'outputNode') return 'Output node'
  return node.data?.program || 'Node'
}

/**
 * Walk the React Flow node/edge graph into a topologically-sorted DAG of
 * execution tasks. Unlike a simple linear chain, any effect node may have
 * MULTIPLE video inputs: one primary (the node's default target handle) plus
 * zero or more "extra" inputs (named handles, one per program arg with
 * type:'file' && subtype:'video'). Each extra input resolves from whichever
 * upstream node is connected to its handle, or falls back to a manually
 * picked literal file path when nothing is connected.
 *
 * Returns { version: 3, outputPath, sources, batchSources, tasks,
 * finalTaskNodeId, finalProducesBatch }.
 * Throws a plain Error with a user-facing message on any invalid graph.
 */
export function buildPipeline(nodes, edges, programMap) {
  const byId = new Map(nodes.map(n => [n.id, n]))

  const outputNodes = nodes.filter(n => n.type === 'outputNode')
  if (outputNodes.length === 0) throw new Error('No Output node found on the canvas.')
  if (outputNodes.length > 1) throw new Error('Only one Output node is supported. Remove the extra Output node(s).')
  const outputNode = outputNodes[0]
  if (!outputNode.data.filePath) throw new Error('Output node: no output path set.')

  // incoming: targetNodeId -> handleKey -> edge
  const incoming = new Map()
  for (const e of edges) {
    const key = e.targetHandle ?? PRIMARY
    if (!incoming.has(e.target)) incoming.set(e.target, new Map())
    const slot = incoming.get(e.target)
    if (slot.has(key)) {
      throw new Error(`${describe(byId.get(e.target))}: two connections into the same input. Each input accepts one connection.`)
    }
    slot.set(key, e)
  }

  // Reverse-reachability from Output over ALL incoming edges (primary + named).
  // Nodes outside this set are orphan branches — silently skipped, matching
  // the previous linear builder's "only the Input→Output path matters".
  const reachable = new Set()
  const stack = [outputNode.id]
  while (stack.length) {
    const id = stack.pop()
    if (reachable.has(id)) continue
    reachable.add(id)
    for (const e of (incoming.get(id)?.values() ?? [])) {
      if (!byId.has(e.source)) throw new Error(`Node ${e.source} not found.`)
      stack.push(e.source)
    }
  }

  // Validate + resolve each reachable node.
  const sources      = {}          // nodeId -> literal path (file-mode Input nodes)
  const batchSources = {}          // nodeId -> folder path (folder-mode Input nodes)
  const resolved = new Map()       // effect nodeId -> task (sans topo order)
  for (const id of reachable) {
    const n = byId.get(id)
    const slot = incoming.get(id) ?? new Map()

    if (n.type === 'inputNode') {
      if (n.data.mode === 'folder') {
        if (!n.data.folderPath) throw new Error(`${describe(n)}: no folder selected.`)
        batchSources[id] = n.data.folderPath
      } else {
        if (!n.data.filePath) throw new Error(`${describe(n)}: no video file selected.`)
        sources[id] = n.data.filePath
      }
      continue
    }

    if (n.type === 'outputNode') {
      if (!slot.has(PRIMARY)) throw new Error('Output node has no incoming connection.')
      continue
    }

    if (n.type === 'effectNode') {
      const prog = programMap?.[n.data.program]
      if (!prog) throw new Error(`Unknown program "${n.data.program}".`)

      // Primary input has no arg fallback — it must be a graph connection.
      const pEdge = slot.get(PRIMARY)
      if (!pEdge) throw new Error(`${describe(n)}: main video input is not connected.`)
      const primaryInput = { source: 'node', nodeId: pEdge.source }

      // Extra video inputs — edge wins, else a manually picked literal path.
      const vArgs = videoArgsOf(prog)
      const extraInputs = []
      for (const a of vArgs) {
        const e = slot.get(a.name)
        if (e) {
          extraInputs.push({ argName: a.name, ref: { source: 'node', nodeId: e.source } })
          continue
        }
        const literal = String(n.data.args?.[a.name] ?? '').trim()
        if (literal) {
          extraInputs.push({ argName: a.name, ref: { source: 'path', path: literal } })
        } else if (a.required) {
          throw new Error(`${describe(n)} → ${a.label}: connect a video or choose a file.`)
        }
        // optional and unset -> omit entirely
      }

      // Non-video args. Resolved against the FULL arg list (not just what's
      // present in data.args) so a required arg with a default — e.g. a
      // select the user never touched — still gets sent. ArgField only ever
      // writes to data.args on user interaction; ArgField's displayed value
      // (which does fall back to arg.default) is otherwise purely visual.
      const vNames = new Set(vArgs.map(a => a.name))
      const args = {}
      for (const a of (prog.args || [])) {
        if (vNames.has(a.name)) continue
        const v = n.data.args?.[a.name]
        if (v !== undefined && v !== '') {
          args[a.name] = v
        } else if (a.default !== undefined) {
          args[a.name] = a.default
        } else if (a.required) {
          throw new Error(`${describe(n)} → ${a.label}: this field is required.`)
        }
      }

      resolved.set(id, {
        nodeId: id,
        program: n.data.program,
        outputType: prog.outputType || 'video',
        primaryInput,
        extraInputs,
        args
      })
      continue
    }

    throw new Error(`Unsupported node type "${n.type}".`)
  }

  // Forward adjacency (only within the reachable subgraph) for Kahn's algorithm.
  const forward = new Map()
  for (const id of reachable) forward.set(id, [])
  for (const id of reachable) {
    for (const e of (incoming.get(id)?.values() ?? [])) {
      forward.get(e.source)?.push(id)
    }
  }
  const indeg = new Map()
  for (const id of reachable) indeg.set(id, incoming.get(id)?.size ?? 0)

  // Deterministic order: seed/insert by canvas position so the execution
  // order the log reports reads the way the graph looks (left-to-right).
  const byPosition = (a, b) => {
    const na = byId.get(a), nb = byId.get(b)
    return (na.position.x - nb.position.x) || (na.position.y - nb.position.y) || a.localeCompare(b)
  }

  const queue = [...reachable].filter(id => indeg.get(id) === 0).sort(byPosition)
  const tasks = []
  let seen = 0
  while (queue.length) {
    const id = queue.shift()
    seen++
    if (resolved.has(id)) tasks.push(resolved.get(id))
    for (const s of forward.get(id) || []) {
      indeg.set(s, indeg.get(s) - 1)
      if (indeg.get(s) === 0) {
        const i = queue.findIndex(other => byPosition(s, other) < 0)
        if (i === -1) queue.push(s); else queue.splice(i, 0, s)
      }
    }
  }
  if (seen < reachable.size) {
    throw new Error('Cycle detected in the pipeline — a node eventually feeds back into itself.')
  }

  // ── Batch annotation ──────────────────────────────────────────────────────
  // A task "consumes" a batch if its primary input traces to a batch source
  // (a folder-mode Input, or an upstream task that itself produces one); it
  // "produces" a batch if it consumes one (batch-ness propagates downstream
  // through ordinary single-in/single-out effects) or its own program
  // natively fans one input out into many files (qwikchop today). tasks are
  // already topo-sorted, so a task's primary-input producer always appears
  // earlier in the array.
  const batchProducerIds = new Set(Object.keys(batchSources))
  for (const t of tasks) {
    t.consumesBatch = batchProducerIds.has(t.primaryInput.nodeId)
    t.producesBatch = !!programMap?.[t.program]?.batchOutput || t.consumesBatch
    if (t.producesBatch) batchProducerIds.add(t.nodeId)
  }

  // v1 constraint: a batch may only flow through primary-input chains — it
  // can never fill a secondary (extraInputs) handle, sidestepping the much
  // harder problem of fanning in batches of different lengths/shapes.
  for (const t of tasks) {
    for (const ex of t.extraInputs) {
      if (ex.ref.source === 'node' && batchProducerIds.has(ex.ref.nodeId)) {
        const prog = programMap?.[t.program]
        const argLabel = prog?.args?.find(a => a.name === ex.argName)?.label || ex.argName
        throw new Error(
          `${describe(byId.get(t.nodeId))} → ${argLabel}: this input comes from a batch source ` +
          `(multiple files). Batch connections can only feed a node's main video input — pick a ` +
          `single file, or insert an effect before this connection instead.`
        )
      }
    }
  }

  // v1 constraint: a native fan-out program (qwikchop) can't itself be fed a
  // batch — nested batches are out of scope for now.
  for (const t of tasks) {
    if (t.consumesBatch && programMap?.[t.program]?.batchOutput) {
      const prog = programMap?.[t.program]
      throw new Error(
        `${describe(byId.get(t.nodeId))}: "${prog?.label || t.program}" natively splits its input ` +
        `into multiple files and can't itself be fed a batch (multiple files) as input in this ` +
        `version. Feed it a single file, or run it before the batch step.`
      )
    }
  }

  const finalTaskNodeId = incoming.get(outputNode.id).get(PRIMARY).source
  if (byId.get(finalTaskNodeId).type !== 'effectNode') {
    throw new Error('Pipeline has no effects — connect at least one program between Input and Output.')
  }
  const finalProducesBatch = !!resolved.get(finalTaskNodeId)?.producesBatch

  return {
    version: 3,
    outputPath: outputNode.data.filePath,
    sources,
    batchSources,
    tasks,
    finalTaskNodeId,
    finalProducesBatch
  }
}

/**
 * Live editing-time check: does this node's primary input ultimately trace
 * back to a batch source (a folder-mode Input, or a program that natively
 * fans out, e.g. qwikchop)? Used only for the canvas UI badge — a cheap
 * linear walk backward along primary-handle edges, since v1 batch chains
 * are constrained to be strictly linear (see buildPipeline's validation).
 */
export function upstreamIsBatch(nodeId, nodes, edges, programMap) {
  const byId = new Map(nodes.map(n => [n.id, n]))
  const seen = new Set()
  let currentId = nodeId

  while (true) {
    if (seen.has(currentId)) return false
    seen.add(currentId)

    const incomingEdge = edges.find(e => e.target === currentId && (e.targetHandle ?? PRIMARY) === PRIMARY)
    if (!incomingEdge) return false

    const upstream = byId.get(incomingEdge.source)
    if (!upstream) return false

    if (upstream.type === 'inputNode') return upstream.data?.mode === 'folder'

    if (upstream.type === 'effectNode') {
      if (programMap?.[upstream.data?.program]?.batchOutput) return true
      currentId = upstream.id
      continue
    }

    return false
  }
}
