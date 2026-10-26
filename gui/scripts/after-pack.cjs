// electron-builder hook (package.json → build.afterPack), macOS only.
//
// The installer copies Python, ffmpeg and the videobeaux package into the app AFTER Electron has signed it. That changes the
// bundle's contents, so its signature no longer matches, and macOS then reports the app as "damaged" (quarantined downloads fail
// the check outright). This hook gives every native binary inside Resources, and then the app bundle, a valid ad-hoc signature,
// so the bundle is sealed. It is NOT a developer identity: people still get the "unidentified developer" prompt, and the app is
// not notarized. It does nothing once a real identity is configured (mac.identity), because electron-builder then signs properly.
//
// The build fails if the sealed bundle doesn't verify, rather than shipping something macOS will call damaged.
const { execFileSync } = require('child_process')
const fs = require('fs')
const path = require('path')

// first four bytes of a Mach-O file: thin 64/32-bit (little-endian) and fat/universal (big-endian)
const MACHO_MAGIC = new Set(['cffaedfe', 'cefaedfe', 'cafebabe', 'cafebabf', 'bebafeca', 'bfbafeca'])

/** Every regular, non-symlinked Mach-O file under `dir` (python's .so/.dylib files, ffmpeg, python3, …). */
function machoFiles(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name)
    if (e.isSymbolicLink()) continue
    if (e.isDirectory()) { machoFiles(p, out); continue }
    if (!e.isFile()) continue
    const fd = fs.openSync(p, 'r')
    const head = Buffer.alloc(4)
    try { fs.readSync(fd, head, 0, 4, 0) } finally { fs.closeSync(fd) }
    if (MACHO_MAGIC.has(head.toString('hex'))) out.push(p)
  }
  return out
}

async function afterPack(context) {
  if (context.electronPlatformName !== 'darwin') return
  const identity = context.packager.platformSpecificBuildOptions && context.packager.platformSpecificBuildOptions.identity
  if (identity) return                                              // a real identity is configured: electron-builder signs

  if (process.platform !== 'darwin') {
    console.warn('after-pack: not running on macOS, so the unsigned app will not be sealed (build the mac app on a Mac)')
    return
  }
  const app = path.join(context.appOutDir, `${context.packager.appInfo.productFilename}.app`)
  const binaries = machoFiles(path.join(app, 'Contents', 'Resources'))
  console.log(`after-pack: ad-hoc signing ${binaries.length} binaries in Resources, then the app bundle`)
  for (let i = 0; i < binaries.length; i += 200) {
    execFileSync('codesign', ['--force', '--sign', '-', '--timestamp=none', ...binaries.slice(i, i + 200)], { stdio: 'inherit' })
  }
  // Electron's own framework and helper apps ship with a bare linker signature and no sealed resources, so the app can't
  // verify until they are re-signed too. For an ad-hoc build the recursive form is the simplest way to sign them all.
  // (Phase 2, with a Developer ID, signs inside-out instead and doesn't use --deep.)
  execFileSync('codesign', ['--force', '--deep', '--sign', '-', '--timestamp=none', app], { stdio: 'inherit' })
  execFileSync('codesign', ['--verify', '--deep', '--strict', '--verbose=2', app], { stdio: 'inherit' })   // throws (fails the build) if broken
  console.log('after-pack: app bundle sealed (ad-hoc)')
}

module.exports = afterPack
module.exports.machoFiles = machoFiles
module.exports.MACHO_MAGIC = MACHO_MAGIC
