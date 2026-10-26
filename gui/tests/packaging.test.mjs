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

test('tests/ is not shipped, and the smoke runner that the app needs is staged into tools/', () => {
  assert.equal(pkg.build.extraResources.some(r => /tests/.test(r.from) || /tests/.test(r.to)), false)
  assert.match(script, /join\(RESOURCES, 'tools', 'run_smoke\.py'\)/)
})

test('the per-slider response curves are staged next to discover_programs.py', () => {
  assert.match(script, /copyFileSync\(join\(GUI_ROOT, 'slider_curves\.json'\), join\(guiDest, 'slider_curves\.json'\)\)/)
})

test('the bundled Python is checked for broken symlinks before packaging', () => {
  assert.match(script, /assertNoBrokenLinks\(pythonDir\)/)
})

test('macOS builds get an afterPack hook that seals the app, and the hook file exists', async () => {
  assert.equal(pkg.build.afterPack, 'scripts/after-pack.cjs')
  const { createRequire } = await import('node:module')
  const hook = createRequire(import.meta.url)('../scripts/after-pack.cjs')
  // a configured identity (Developer ID, later) turns the ad-hoc step off entirely
  await hook({ electronPlatformName: 'darwin', appOutDir: '/does/not/exist', packager: { platformSpecificBuildOptions: { identity: 'Developer ID Application: Example' }, appInfo: { productFilename: 'x' } } })
  // other platforms are untouched
  await hook({ electronPlatformName: 'win32', appOutDir: '/does/not/exist', packager: { platformSpecificBuildOptions: {}, appInfo: { productFilename: 'x' } } })
})

test('the afterPack hook finds Mach-O binaries by their header and ignores everything else', async () => {
  const { createRequire } = await import('node:module')
  const { machoFiles } = createRequire(import.meta.url)('../scripts/after-pack.cjs')
  const { mkdtempSync, writeFileSync, mkdirSync, symlinkSync } = await import('node:fs')
  const { tmpdir } = await import('node:os')
  const { join } = await import('node:path')
  const d = mkdtempSync(join(tmpdir(), 'afterpack-'))
  mkdirSync(join(d, 'lib'))
  writeFileSync(join(d, 'python3'), Buffer.from([0xcf, 0xfa, 0xed, 0xfe, 0, 0]))            // thin 64-bit Mach-O
  writeFileSync(join(d, 'lib', 'mod.so'), Buffer.from([0xca, 0xfe, 0xba, 0xbe, 0, 0]))      // fat / universal
  writeFileSync(join(d, 'readme.txt'), 'hello')
  writeFileSync(join(d, 'short'), Buffer.from([0xcf]))                                       // too short to be a header
  symlinkSync(join(d, 'python3'), join(d, 'python3.link'))                                  // symlinks are left alone
  const found = machoFiles(d).map(p => p.slice(d.length + 1)).sort()
  assert.deepEqual(found, ['lib/mod.so', 'python3'])
})
