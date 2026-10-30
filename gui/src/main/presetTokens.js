// Example presets (examples/presets/*.vbpreset.json) name paths with tokens instead of real paths:
//   {{sample}}, {{sample2}}, {{sample3}}  the bundled example clips  →  <vbRoot>/examples/<clip>.mp4
//   {{outputs}}                           where examples write their result →  <Documents>/videobeaux/outputs
// Tokens are filled in Input and Output file paths, and in string argument values (a soundtrack's audio, for example).
// Pure function so it can be tested without Electron; main/index.js supplies the folders.
export function resolvePresetTokens(nodes, { tokens = {} } = {}) {
  const fill = v => {
    if (typeof v !== 'string') return v
    let out = v
    for (const [name, value] of Object.entries(tokens)) out = out.replaceAll(`{{${name}}}`, () => value)
    return out
  }
  return (nodes || []).map(n => {
    if (!n?.data) return n
    const data = { ...n.data }
    for (const key of ['filePath', 'folderPath']) if (typeof data[key] === 'string') data[key] = fill(data[key])
    if (data.args && typeof data.args === 'object') {
      data.args = Object.fromEntries(Object.entries(data.args).map(([k, v]) => [k, fill(v)]))
    }
    return { ...n, data }
  })
}
