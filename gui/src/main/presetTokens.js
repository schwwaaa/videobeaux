// Example presets (examples/presets/*.vbpreset.json) name two places with tokens instead of real paths:
//   {{sample}}   the bundled sample clip        →  <vbRoot>/examples/sample.mp4
//   {{outputs}}  where examples write their result →  <Documents>/videobeaux/outputs
// Pure function so it can be tested without Electron; main/index.js supplies the two folders.
export function resolvePresetTokens(nodes, { sampleFile, outputsDir }) {
  const fill = v => (typeof v === 'string'
    ? v.replaceAll('{{sample}}', sampleFile).replaceAll('{{outputs}}', outputsDir)
    : v)
  return (nodes || []).map(n => {
    if (!n?.data) return n
    const data = { ...n.data }
    for (const key of ['filePath', 'folderPath']) if (typeof data[key] === 'string') data[key] = fill(data[key])
    return { ...n, data }
  })
}
