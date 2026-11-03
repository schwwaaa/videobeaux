#!/usr/bin/env node
// Builds the macOS installer (npm run dist), then creates a DRAFT GitHub
// release with the DMG attached, using the gh CLI. Needs gh installed and
// logged in (`gh auth status`). Publishes nothing: check the draft on GitHub
// and press Publish yourself.
//
// Usage: npm run release
// The tag is v<version> from package.json. Commit and push first, because
// gh creates a new tag on the remote's default branch.

import { readFileSync, readdirSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const guiDir = join(dirname(fileURLToPath(import.meta.url)), '..')
const { version } = JSON.parse(readFileSync(join(guiDir, 'package.json'), 'utf8'))
const tag = `v${version}`

function run(cmd, args) {
  const result = spawnSync(cmd, args, { cwd: guiDir, stdio: 'inherit' })
  if (result.error) throw result.error
  if (result.status !== 0) throw new Error(`${cmd} ${args.join(' ')} exited with ${result.status}`)
}

// Check gh before the long build, so a missing login fails in seconds.
const auth = spawnSync('gh', ['auth', 'status'], { stdio: 'ignore' })
if (auth.error) throw new Error('gh is not installed. Install it with: brew install gh')
if (auth.status !== 0) throw new Error('gh is not logged in. Run: gh auth login')

run('npm', ['run', 'dist'])

// Only this version's DMG, so older builds left in dist/ are not uploaded.
const distDir = join(guiDir, 'dist')
const dmgs = readdirSync(distDir)
  .filter((f) => f.endsWith('.dmg') && f.includes(version))
  .map((f) => join(distDir, f))
if (dmgs.length === 0) throw new Error(`no ${version} .dmg found in ${distDir}`)

run('gh', ['release', 'create', tag, ...dmgs, '--draft', '--title', `Videobeaux ${tag}`, '--generate-notes'])
console.log(`Draft ${tag} created. Check it on GitHub, then press Publish.`)
