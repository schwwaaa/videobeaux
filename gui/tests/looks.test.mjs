import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync, existsSync } from 'node:fs'
import { FAMILIES, FAMILY_COLOR, familyOf, familyOfCategory, MOTIFS, motifOf, categoryMotif } from '../src/renderer/src/looks/registry.js'
import { CATEGORIES } from '../src/renderer/src/programs.js'

const SRC = new URL('../src/renderer/src/', import.meta.url)

test('every program in every category resolves to a known family', () => {
  const unknown = []
  for (const cat of CATEGORIES) for (const p of cat.programs) {
    if (!FAMILIES[familyOf(p.id, cat.id)]) unknown.push(p.id)
  }
  assert.deepEqual(unknown, [])
})

test('every category has a default family and every family has a chip colour', () => {
  for (const cat of CATEGORIES) assert.ok(FAMILIES[familyOfCategory(cat.id)], cat.id)
  for (const f of Object.keys(FAMILIES)) assert.match(FAMILY_COLOR[f] || '', /^#[0-9a-f]{6}$/i, f)
})

test('registry overrides only name programs that exist (typo guard)', () => {
  const known = new Set(CATEGORIES.flatMap(c => c.programs.map(p => p.id)))
  const src = readFileSync(new URL('looks/registry.js', SRC), 'utf8')
  const block = src.slice(src.indexOf('const OVERRIDES'), src.indexOf('const OVERRIDE_MAP'))
  const ids = [...block.matchAll(/'([a-z0-9_]+)'/g)].map(m => m[1]).filter(id => !(id in FAMILIES))
  const missing = [...new Set(ids)].filter(id => !known.has(id))
  assert.deepEqual(missing, [])
})

test('every family has a pattern in the generated CSS and a default glyph', () => {
  const css = readFileSync(new URL('looks/shared/patterns.css', SRC), 'utf8')
  for (const f of Object.keys(FAMILIES)) assert.ok(css.includes(`--pat-${f}:`), `pattern for ${f}`)
  const glyphs = readFileSync(new URL('looks/signatures/glyphs.js', SRC), 'utf8')
  for (const f of Object.keys(FAMILIES)) assert.match(glyphs, new RegExp(`\\b${f}:\\s+svg\\(`), `glyph for ${f}`)
})

test('look CSS is scoped: nothing in a look stylesheet applies without data-look', () => {
  for (const look of ['patterns', 'motifs', 'signatures', 'output-art']) {
    const css = readFileSync(new URL(`looks/${look}/look.css`, SRC), 'utf8')
      .replace(/\/\*[\s\S]*?\*\//g, '')
    const selectors = css.split('}').map(b => b.split('{')[0].trim()).filter(Boolean)
    const unscoped = selectors.filter(s => s.split(',').some(p => !p.includes('data-look') && !p.trim().startsWith('.art-preview')))
    assert.deepEqual(unscoped, [], `${look} has unscoped selectors`)
  }
})

test('generated art (when present) matches its manifest', { skip: !existsSync(new URL('looks/output-art/manifest.json', SRC)) }, () => {
  const manifest = JSON.parse(readFileSync(new URL('looks/output-art/manifest.json', SRC), 'utf8'))
  const files = new Set(readdirSync(new URL('looks/output-art/art/', SRC)))
  for (const [id, m] of Object.entries(manifest.programs)) assert.ok(files.has(m.file), `${id} → ${m.file}`)
})

// ── header motifs: a pattern has a reason, and never crosses a category ──────────────────────────────────────────────
test('every module has its own motif (no silent fallback) and a motif is never shared across categories', () => {
  const byMotif = new Map()
  const missing = []
  for (const cat of CATEGORIES) for (const p of cat.programs) {
    const m = motifOf(p.id, null)
    if (!m) { missing.push(p.id); continue }
    if (!byMotif.has(m)) byMotif.set(m, new Set())
    byMotif.get(m).add(cat.id)
  }
  assert.deepEqual(missing, [])
  const crossing = [...byMotif].filter(([, cats]) => cats.size > 1).map(([m, cats]) => `${m}: ${[...cats].join('+')}`)
  assert.deepEqual(crossing, [], 'a motif may only be used by modules of one category')
})

test('every motif is used, explained, drawn, and matches the category it declares', () => {
  const used = new Set()
  for (const cat of CATEGORIES) for (const p of cat.programs) {
    const m = motifOf(p.id, null)
    used.add(m)
    assert.equal(MOTIFS[m].category, cat.id, `${p.id} → ${m}`)
  }
  const css = readFileSync(new URL('looks/shared/motifs.css', SRC), 'utf8')
  for (const [id, meta] of Object.entries(MOTIFS)) {
    assert.ok(used.has(id), `${id} is unused`)
    assert.ok(meta.reason && meta.reason.length > 10, `${id} needs a reason`)
    assert.ok(css.includes(`--mot-${id}:`), `${id} has no drawing`)
  }
  for (const cat of CATEGORIES) assert.equal(MOTIFS[categoryMotif(cat.id)].category, cat.id, `category chip motif for ${cat.id}`)
})
