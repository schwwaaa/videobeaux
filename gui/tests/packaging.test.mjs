import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const pkg = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'))
const script = readFileSync(new URL('../scripts/build-python-env.mjs', import.meta.url), 'utf8')

test('every folder the stager puts under gui/resources is packaged by electron-builder', () => {
  const listed = new Set(pkg.build.extraResources.map(r => r.from.replace(/^resources\//, '')))
  // join(RESOURCES, 'name', …) occurrences in the stager = directories it creates
  const staged = new Set([...script.matchAll(/join\(RESOURCES,\s*'([a-z_]+)'/g)].map(m => m[1]))
  staged.delete('_python.tar.gz'); staged.delete('_requirements.filtered.txt')
  for (const dir of staged) assert.ok(listed.has(dir), `resources/${dir} is staged but missing from build.extraResources`)
})

test('the installer resolves ffmpeg before deleting anything', () => {
  const main = script.slice(script.indexOf('async function main()'))
  assert.ok(main.indexOf('resolveFfmpeg()') > 0 && main.indexOf('resolveFfmpeg()') < main.indexOf('rmrf(RESOURCES)'),
    'resolveFfmpeg() must run before rmrf(RESOURCES)')
})

test('the installer never falls back to the third-party (devFallback) ffmpeg', () => {
  assert.equal(/allowFallback\s*:\s*true/.test(script), false)
})
