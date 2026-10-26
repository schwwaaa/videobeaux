import test from 'node:test'
import assert from 'node:assert/strict'
import { CATEGORIES, EXCLUDED_FROM_GUI } from '../src/renderer/src/programs.js'

// Program modes that are homages to LZX Industries designs stay out of the app until release (CLI still works).
const HIDDEN_UNTIL_RELEASE = ['beauxtrix', 'topobeaux', 'shape_synth', 'stackadelic']

test('the LZX homage program modes are hidden from the app', () => {
  for (const id of HIDDEN_UNTIL_RELEASE) assert.ok(EXCLUDED_FROM_GUI.has(id), `${id} must be in EXCLUDED_FROM_GUI`)
})

test('any program mode that mentions LZX is hidden from the app', () => {
  const visible = CATEGORIES.flatMap(c => c.programs).filter(p => !EXCLUDED_FROM_GUI.has(p.id))
  const leaks = visible.filter(p => /lzx/i.test(`${p.label} ${p.description || ''}`)).map(p => p.id)
  assert.deepEqual(leaks, [], 'these mention LZX but are still visible — add them to EXCLUDED_FROM_GUI')
})
