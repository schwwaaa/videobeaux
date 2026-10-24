// Slider response curves: how the slider *position* maps to the *value*.
//   linear    (default) equal distance = equal change
//   log       equal distance = equal ratio      — for ranges spanning decades (0.05…100, 0.01…1)
//   pow:γ     value = lo + (hi-lo)·t^γ          — γ > 1: slow start, fast finish · γ < 1: fast start (front-loaded)
//   ease      shorthand for pow:0.6
// Only the slider moves along the curve; the number box, saved presets and the CLI always carry real values.

export function parseScale(scale) {
  if (!scale || scale === 'linear') return { kind: 'linear' }
  if (scale === 'log') return { kind: 'log' }
  if (scale === 'ease') return { kind: 'pow', g: 0.6 }
  const m = /^pow:([0-9]*\.?[0-9]+)$/.exec(String(scale))
  if (m && Number(m[1]) > 0 && Number(m[1]) !== 1) return { kind: 'pow', g: Number(m[1]) }
  return { kind: 'linear' }
}

export function makeScale(scale, lo, hi) {
  let s = parseScale(scale)
  if (s.kind === 'log' && !(lo > 0 && hi > lo)) s = { kind: 'linear' }       // log needs a positive range
  const span = hi - lo
  const clamp01 = t => (t < 0 ? 0 : t > 1 ? 1 : t)
  if (s.kind === 'log') {
    const k = Math.log(hi / lo)
    return { kind: 'log', curved: true, toT: v => clamp01(Math.log(Math.max(v, lo) / lo) / k), fromT: t => lo * Math.exp(k * clamp01(t)) }
  }
  if (s.kind === 'pow') {
    return { kind: 'pow', curved: true, toT: v => clamp01(Math.pow(clamp01((v - lo) / span), 1 / s.g)), fromT: t => lo + span * Math.pow(clamp01(t), s.g) }
  }
  return { kind: 'linear', curved: false, toT: v => clamp01((v - lo) / span), fromT: t => lo + span * clamp01(t) }
}

/** A slider value from a position, rounded to something a person would type (3 significant digits), kept in range. */
export function valueFromPosition(sc, t, { lo, hi, integer = false }) {
  let v = sc.fromT(t)
  v = integer ? Math.round(v) : Number(v.toPrecision(3))
  return Math.min(hi, Math.max(lo, v))
}

export function describeScale(sc) {
  return sc.kind === 'log' ? 'logarithmic slider' : sc.kind === 'pow' ? (sc.curved ? 'curved slider' : '') : ''
}
