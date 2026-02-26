import React, { createContext, useContext, useState, useEffect } from 'react'
import { CATEGORIES, PROGRAM_MAP as STATIC_MAP, EXCLUDED_FROM_GUI } from './programs'

const ProgramsContext = createContext(null)

/**
 * Merges dynamically-discovered arg schemas from the Python introspection
 * script on top of the static visual metadata in programs.js.
 *
 * - Existing programs: args + description are replaced with live data.
 * - Brand-new programs (not yet in programs.js): added to a "New Programs" category.
 * - If discovery fails: falls back to the static registry silently.
 */
export function ProgramsProvider({ children }) {
  // Strip excluded programs from the static category lists up-front
  const filteredCategories = CATEGORIES.map(cat => ({
    ...cat,
    programs: cat.programs.filter(p => !EXCLUDED_FROM_GUI.has(p.id))
  })).filter(cat => cat.programs.length > 0)

  const filteredMap = Object.fromEntries(
    Object.entries(STATIC_MAP).filter(([id]) => !EXCLUDED_FROM_GUI.has(id))
  )

  const [programMap, setProgramMap] = useState(filteredMap)
  const [categories, setCategories] = useState(filteredCategories)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    window.electronAPI.discoverPrograms()
      .then(discovered => {
        if (!discovered || Object.keys(discovered).length === 0) {
          setReady(true)
          return
        }

        // ── 1. Merge into existing static entries (skip excluded) ─────────
        const merged = {}
        Object.entries(filteredMap).forEach(([id, prog]) => {
          const live = discovered[id]
          merged[id] = {
            ...prog,
            description: (live?.description) || prog.description,
            // Static args win when explicitly defined in programs.js.
            // This preserves hand-crafted metadata (subtype:'dir', help text,
            // correct types, hidden args like batch_dir) that the Python
            // introspection script cannot infer.
            // Live args are only used for programs whose static entry has args:[].
            args:        (prog.args && prog.args.length > 0)
                           ? prog.args
                           : (live && !live.error && live.args?.length > 0 ? live.args : []),
            // Same priority rule for outputType.
            outputType: prog.outputType || (live && !live.error ? live.outputType : null) || 'video',
          }
        })

        // ── 2. Collect programs that aren't in programs.js yet ────────────
        const knownIds  = new Set(Object.keys(STATIC_MAP))
        const newProgs  = []

        Object.entries(discovered).forEach(([id, info]) => {
          if (knownIds.has(id) || info.error || EXCLUDED_FROM_GUI.has(id)) return
          const entry = {
            id,
            label:         id.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
            description:   info.description || '',
            args:          info.args || [],
            outputType:    info.outputType || 'video',
            categoryId:    'new',
            categoryLabel: 'New Programs',
            categoryColor: '#a3a3a3',
          }
          merged[id] = entry
          newProgs.push(entry)
        })

        setProgramMap(merged)

        if (newProgs.length > 0) {
          setCategories(prev => [
            ...prev,
            {
              id:       'new',
              label:    'New Programs',
              color:    '#a3a3a3',
              programs: newProgs,
            },
          ])
        }

        setReady(true)
      })
      .catch(() => setReady(true))   // silent fallback to static data
  }, [])

  return (
    <ProgramsContext.Provider value={{ programMap, categories, ready }}>
      {children}
    </ProgramsContext.Provider>
  )
}

export function usePrograms() {
  const ctx = useContext(ProgramsContext)
  if (!ctx) throw new Error('usePrograms must be used inside <ProgramsProvider>')
  return ctx
}
