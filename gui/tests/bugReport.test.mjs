import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync, mkdtempSync, existsSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { execFileSync } from 'node:child_process'
import { redactPaths, buildReportFiles, createReportZip } from '../src/main/bugReport.js'

const src = name => readFileSync(new URL(`../src/${name}`, import.meta.url), 'utf8')

test('redaction removes the tester’s folder names, on Mac and Windows', () => {
  assert.equal(redactPaths('open /Users/bozer/Movies/clip.mp4', { home: '/Users/bozer' }), 'open ~/Movies/clip.mp4')
  assert.equal(redactPaths('C:\\Users\\Anna Lee\\Videos\\a.mov', { home: 'C:\\Users\\Anna Lee' }), '%USERPROFILE%\\Videos\\a.mov')
  assert.equal(redactPaths('C:\\Users\\Anna Lee\\Videos\\a.mov'), 'C:\\Users\\<user>\\Videos\\a.mov')
})

test('redaction replaces other people’s user names, and leaves file names alone', () => {
  assert.equal(redactPaths('/Users/sam/x.mp4 /home/kim/y.mov'), '/Users/<user>/x.mp4 /home/<user>/y.mov')
  assert.equal(redactPaths('interesting_clip_final.mp4'), 'interesting_clip_final.mp4')
  assert.equal(redactPaths(undefined), '')
})

test('a report always has report.txt with the description, and only the parts that were ticked', () => {
  const bare = buildReportFiles({ description: 'it froze' })
  assert.deepEqual(bare.map(f => f.name), ['report.txt'])
  assert.match(bare[0].content, /it froze/)
  assert.match(bare[0].content, /\(this report, no other parts\)/)

  const full = buildReportFiles({ description: 'x', includeLog: true, logText: 'step 1', includeCanvas: true,
                                  canvasJson: '{"nodes":[]}', screenshotPng: Buffer.from([137, 80, 78, 71]), home: '/Users/bozer' })
  assert.deepEqual(full.map(f => f.name), ['report.txt', 'log.txt', 'canvas.vbpreset.json', 'screenshot.png'])
})

test('text parts are redacted when they are written into the report', () => {
  const files = buildReportFiles({ description: 'see /Users/bozer/clip.mp4', includeLog: true, logText: 'reading /Users/bozer/a.mp4',
                                   includeCanvas: true, canvasJson: '{"filePath":"/Users/bozer/b.mp4"}', home: '/Users/bozer' })
  for (const f of files.filter(f => typeof f.content === 'string')) {
    assert.doesNotMatch(f.content, /\/Users\/bozer/, f.name)
  }
})

test('the report zip is created and contains the report', { skip: process.platform === 'linux' && 'zipping is checked on macOS and Windows' }, () => {
  const root = mkdtempSync(join(tmpdir(), 'vb-report-'))
  const { zip, folder } = createReportZip({ files: buildReportFiles({ description: 'zip test' }), rootDir: root, stamp: 'test' })
  assert.ok(zip && existsSync(zip), 'zip written')
  assert.equal(folder, null, 'the loose folder is removed once zipped')
  if (process.platform === 'darwin') {
    const listing = execFileSync('unzip', ['-l', zip]).toString()
    assert.match(listing, /report\.txt/)
  }
})

test('the switch exists and is a boolean', () => {
  const flags = JSON.parse(readFileSync(new URL('../feature-flags.json', import.meta.url), 'utf8'))
  assert.equal(typeof flags.bugReport, 'boolean')
  assert.equal(typeof flags.bugReportEmail, 'string')
})

test('every part of the feature is marked, so removing it is complete', () => {
  const marked = ['main/index.js', 'preload/index.js', 'renderer/src/App.jsx', 'renderer/src/components/HelpWindow.jsx', 'renderer/src/components/SetupScreen.jsx']
  for (const f of marked) assert.match(src(f), /BUG-REPORT/, `${f} has no BUG-REPORT marker`)
  for (const f of ['main/bugReport.js', 'renderer/src/bugReport/BugReportButton.jsx', 'renderer/src/bugReport/BugReportDialog.jsx']) {
    assert.ok(existsSync(new URL(`../src/${f}`, import.meta.url)), f)
  }
  assert.deepEqual(readdirSync(new URL('../src/renderer/src/bugReport/', import.meta.url)).sort(), ['BugReportButton.jsx', 'BugReportDialog.jsx'])
})
