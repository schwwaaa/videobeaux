// Bug reports (test phase). Everything about a report lives here and in gui/src/renderer/src/bugReport/. The whole feature is
// switched on or off in gui/feature-flags.json. Nothing in this file sends anything anywhere: it writes a zip on the tester's
// computer, and the tester decides what to do with it.
import { spawnSync } from 'child_process'
import { mkdirSync, rmSync, writeFileSync, existsSync, statSync } from 'fs'
import { join } from 'path'

// The part of a path that names the person: /Users/<name>/… (macOS), C:\Users\<name>\… (Windows), /home/<name>/… (Linux).
// Windows folder names can contain spaces, so they run to the next backslash; Mac and Linux names are matched up to a slash.
const MAC_USER = /\/Users\/[^/\s"'`<>|*?]+/g
const WIN_USER = /([A-Za-z]:)?\\Users\\[^\\\r\n"'`<>|*?]+/gi
const LINUX_USER = /\/home\/[^/\s"'`<>|*?]+/g

/**
 * Replace the tester's own folder with ~ (or %USERPROFILE% on Windows), and any other user's name with <user>.
 * File names are kept (they're usually what a bug is about); folder names that reveal a person are not.
 */
export function redactPaths(text, { home = '' } = {}) {
  let s = String(text ?? '')
  if (home) {
    const win = home.includes('\\')
    s = s.split(home).join(win ? '%USERPROFILE%' : '~')
    s = s.split(home.replace(/\\/g, '/')).join(win ? '%USERPROFILE%' : '~')
  }
  return s
    .replace(WIN_USER, (m, drive = '') => `${drive}\\Users\\<user>`)
    .replace(MAC_USER, '/Users/<user>')
    .replace(LINUX_USER, '/home/<user>')
}

/**
 * The files that go into one report.
 *   description     the tester's words (always included)
 *   logText         recent Signal Out text; included when includeLog
 *   canvasJson      the canvas as JSON text; included when includeCanvas
 *   screenshotPng   a PNG Buffer; included when provided
 *   info            system details written into report.txt
 * Returns [{ name, content }] where content is a string or a Buffer. Every text part is redacted.
 */
export function buildReportFiles({ description = '', includeLog = false, logText = '', includeCanvas = false, canvasJson = '',
                                   screenshotPng = null, info = {}, home = '' }) {
  const red = t => redactPaths(t, { home })
  const included = []
  const files = []
  const reportLines = [
    'videobeaux bug report',
    '=====================',
    '',
    `Time (UTC):   ${info.time || new Date().toISOString()}`,
    `App version:  ${info.appVersion || '?'}${info.packaged === false ? ' (development build)' : ''}`,
    `Platform:     ${info.platform || '?'} ${info.arch || ''} (${info.osRelease || '?'})`,
    `Electron:     ${info.electron || '?'}   Node: ${info.node || '?'}`,
    '',
    'What the tester wrote:',
    red(description).trim() || '(nothing written)',
    ''
  ]
  if (includeLog && logText) { files.push({ name: 'log.txt', content: red(logText) }); included.push('log.txt — recent log') }
  if (includeCanvas && canvasJson) { files.push({ name: 'canvas.vbpreset.json', content: red(canvasJson) }); included.push('canvas.vbpreset.json — the canvas') }
  if (screenshotPng && screenshotPng.length) { files.push({ name: 'screenshot.png', content: screenshotPng }); included.push('screenshot.png — the canvas as it looked') }
  reportLines.push('Included:', ...(included.length ? included.map(i => `  • ${i}`) : ['  • (this report, no other parts)']))
  return [{ name: 'report.txt', content: reportLines.join('\n') + '\n' }, ...files]
}

/**
 * Write the files into a new folder under rootDir, then zip it. macOS uses ditto and Windows uses Compress-Archive (both ship with
 * the OS). If zipping fails, the folder is kept and returned so nothing is lost. Returns { zip, folder }: zip is null on failure.
 */
export function createReportZip({ files, rootDir, stamp }) {
  const folder = join(rootDir, `videobeaux-report-${stamp}`)
  mkdirSync(folder, { recursive: true })
  for (const f of files) writeFileSync(join(folder, f.name), f.content)
  const zip = `${folder}.zip`
  let ok = false
  if (process.platform === 'darwin') {
    // --norsrc/--noextattr/--noacl: no macOS metadata files (._*) in the zip, so it's clean for Windows users too
    ok = spawnSync('/usr/bin/ditto', ['-c', '-k', '--norsrc', '--noextattr', '--noacl', '--keepParent', folder, zip]).status === 0
  } else if (process.platform === 'win32') {
    const q = p => `'${p.replace(/'/g, "''")}'`
    ok = spawnSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command',
      `Compress-Archive -LiteralPath ${q(folder)} -DestinationPath ${q(zip)} -Force`]).status === 0
  }
  if (ok && existsSync(zip) && statSync(zip).size > 0) {
    rmSync(folder, { recursive: true, force: true })
    return { zip, folder: null }
  }
  return { zip: null, folder }
}
