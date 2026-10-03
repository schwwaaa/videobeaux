import { createWriteStream, existsSync, mkdirSync, renameSync, statSync, unlinkSync } from 'fs'
import { dirname } from 'path'

/**
 * Download `url` to `dest` (following redirects), reporting progress.
 * Written to `<dest>.part` first and renamed only once complete, so an
 * interrupted download never leaves a truncated file that looks installed.
 * If `expectedSize` is given, a size mismatch is treated as a failed download.
 */
export async function downloadToFile(url, dest, { onProgress, expectedSize } = {}) {
  mkdirSync(dirname(dest), { recursive: true })
  const part = `${dest}.part`
  try {
    const res = await fetch(url)
    if (!res.ok || !res.body) throw new Error(`Download failed: HTTP ${res.status}`)
    const total = Number(res.headers.get('content-length')) || expectedSize || 0
    let received = 0

    const out = createWriteStream(part)
    const reader = res.body.getReader()
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      received += value.length
      await new Promise((resolve, reject) => out.write(value, err => (err ? reject(err) : resolve())))
      onProgress?.({ received, total })
    }
    await new Promise((resolve, reject) => out.end(err => (err ? reject(err) : resolve())))

    const size = statSync(part).size
    if (expectedSize && size !== expectedSize) {
      throw new Error(`Download was incomplete (${size} of ${expectedSize} bytes) — please try again`)
    }
    renameSync(part, dest)
    return { size }
  } catch (err) {
    try { if (existsSync(part)) unlinkSync(part) } catch { /* ignore */ }
    throw err
  }
}
