import test from 'node:test'
import assert from 'node:assert/strict'
import { parseScale, makeScale, valueFromPosition } from '../src/renderer/src/sliderScale.js'

const close = (a, b, eps = 1e-9) => assert.ok(Math.abs(a - b) <= eps, `${a} vs ${b}`)

test('linear is the default and unknown strings fall back to it', () => {
  for (const s of [undefined, null, '', 'linear', 'wobble', 'pow:0', 'pow:x']) assert.equal(parseScale(s).kind, 'linear', String(s))
  const sc = makeScale(undefined, 0, 10)
  close(sc.toT(5), 0.5); close(sc.fromT(0.25), 2.5); assert.equal(sc.curved, false)
})

test('log: the midpoint is the geometric mean and positions round-trip', () => {
  const sc = makeScale('log', 0.1, 10)
  close(sc.fromT(0.5), 1, 1e-9)
  for (const v of [0.1, 0.25, 1, 3, 10]) close(sc.fromT(sc.toT(v)), v, 1e-9)
  close(sc.toT(0.1), 0); close(sc.toT(10), 1)
})

test('log needs a positive range, otherwise it quietly stays linear', () => {
  assert.equal(makeScale('log', 0, 10).kind, 'linear')
  assert.equal(makeScale('log', -1, 1).kind, 'linear')
})

test('pow: γ>1 starts slow, γ<1 starts fast, endpoints fixed, round-trips', () => {
  const slow = makeScale('pow:2', 0, 1), fast = makeScale('pow:0.5', 0, 1)
  close(slow.fromT(0.5), 0.25); close(fast.fromT(0.5), Math.sqrt(0.5))
  for (const sc of [slow, fast]) { close(sc.fromT(0), 0); close(sc.fromT(1), 1); for (const v of [0, 0.2, 0.7, 1]) close(sc.fromT(sc.toT(v)), v, 1e-9) }
  assert.equal(parseScale('ease').g, 0.6)
})

test('slider values are rounded to what a person would type and stay in range', () => {
  const sc = makeScale('log', 0.05, 100)
  const v = valueFromPosition(sc, 0.37, { lo: 0.05, hi: 100 })
  assert.equal(String(v).replace('.', '').replace(/^0+/, '').length <= 3, true, String(v))
  assert.equal(valueFromPosition(sc, 1, { lo: 0.05, hi: 100 }), 100)
  assert.equal(valueFromPosition(sc, 0, { lo: 0.05, hi: 100 }), 0.05)
  assert.equal(Number.isInteger(valueFromPosition(makeScale('pow:2', 0, 10), 0.5, { lo: 0, hi: 10, integer: true })), true)
})

test('the position of the default, as drawn by the tick, matches what the slider produces there', () => {
  const sc = makeScale('log', 0.1, 8)
  const t = sc.toT(1)
  close(valueFromPosition(sc, Math.round(t * 1000) / 1000, { lo: 0.1, hi: 8 }), 1, 0.01)
})
