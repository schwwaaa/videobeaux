// Original "signature" glyphs: small thick-outline cartoon icons, one per family plus hand-drawn ones for flagship modules.
// 32×32 viewBox, black outline, flat fills from the app palette — the same vocabulary as the TV mascot.
// Inline SVG markup (trusted, static); inert under the Classic look because the elements that show them are display:none there.

const K = '#080808', Y = '#ffe500', C = '#32b9df', R = '#ff6847', M = '#d52c91', P = '#8654aa', G = '#c5d92d',
      W = '#fffdf6', O = '#ff9f1c', T = '#2ec4b6'

const st = (w = 2.2) => `stroke="${K}" stroke-width="${w}" stroke-linejoin="round" stroke-linecap="round"`
const svg = (inner) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="100%" height="100%" aria-hidden="true">${inner}</svg>`
const rect = (x, y, w, h, fill, r = 2) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${fill}" ${st()}/>`
const circ = (x, y, r, fill) => `<circle cx="${x}" cy="${y}" r="${r}" fill="${fill}" ${st()}/>`
const path = (d, fill = 'none', w) => `<path d="${d}" fill="${fill}" ${st(w)}/>`
const poly = (pts, fill) => `<polygon points="${pts}" fill="${fill}" ${st()}/>`

// ── one default glyph per family ─────────────────────────────────────────────
export const FAMILY_GLYPHS = {
  glitch:  svg(rect(4, 5, 24, 22, M) + rect(1, 12, 14, 5, Y, 1) + rect(18, 18, 13, 5, C, 1)),
  trails:  svg(rect(3, 3, 18, 18, O) + rect(8, 8, 18, 18, W) + rect(13, 13, 16, 16, Y)),
  motion:  svg(path('M3 10h12M3 16h18M3 22h12') + poly('20,8 29,16 20,24', R)),
  texture: svg([8, 16, 24].flatMap(y => [8, 16, 24].map(x => circ(x, y, 2.6, (x + y) % 16 ? P : Y))).join('')),
  color:   svg(circ(16, 16, 6, Y) + [[16, 2, 16, 7], [16, 25, 16, 30], [2, 16, 7, 16], [25, 16, 30, 16], [6, 6, 10, 10], [22, 22, 26, 26], [26, 6, 22, 10], [6, 26, 10, 22]]
    .map(([a, b, c, d]) => path(`M${a} ${b}L${c} ${d}`)).join('')),
  warp:    svg(path('M16 16c2-3 6-1 5 3-1 5-9 5-10-2-1-8 12-10 15-1', 'none', 2.6) + path('M3 8q6-6 13 0t13 0', 'none', 2)),
  vision:  svg(circ(16, 16, 9, W) + path('M16 2v8M16 22v8M2 16h8M22 16h8') + circ(16, 16, 3, T)),
  layout:  svg(rect(3, 5, 17, 14, C) + rect(12, 13, 17, 14, Y)),
  cut:     svg(path('M5 6l22 20M27 6L5 26', 'none', 3) + circ(7, 9, 3.2, W) + circ(7, 23, 3.2, W)),
  speech:  svg(path('M5 6h22a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H14l-7 6v-6H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z', Y) + circ(10, 14, 1.8, K) + circ(16, 14, 1.8, K) + circ(22, 14, 1.8, K)),
  media:   svg(rect(3, 6, 26, 20, G) + rect(6, 9, 6, 4, W, 1) + rect(6, 19, 6, 4, W, 1) + rect(20, 9, 6, 4, W, 1) + rect(20, 19, 6, 4, W, 1) + rect(13, 11, 6, 10, Y, 1)),
  weird:   svg(path('M3 24L9 6l5 14 5-14 5 18', 'none', 3) + poly('24,5 30,13 22,13', Y) + circ(8, 28, 2, M))
}

// ── hand-drawn glyphs for flagship modules (id → svg) ────────────────────────
export const PROGRAM_GLYPHS = {
  feedback_loop:   svg(rect(2, 2, 28, 28, O) + rect(7, 7, 18, 18, W) + rect(11, 11, 10, 10, Y) + circ(16, 16, 2, K)),
  flow_warp:       svg(path('M2 9q7-8 14 0t14 0', 'none', 2.8) + path('M2 17q7-8 14 0t14 0', 'none', 2.8) + path('M2 25q7-8 14 0t14 0', 'none', 2.8) + poly('26,3 30,9 22,9', M)),
  ordered_dither:  svg([0, 1, 2, 3].flatMap(r => [0, 1, 2, 3].map(c => `<rect x="${4 + c * 6}" y="${4 + r * 6}" width="6" height="6" fill="${(r + c) % 2 ? K : W}"/>`)).join('') + `<rect x="4" y="4" width="24" height="24" fill="none" ${st()}/>`),
  ascii_art:       svg(rect(2, 5, 28, 22, K, 3) + `<text x="16" y="21" text-anchor="middle" font-family="monospace" font-weight="700" font-size="13" fill="${Y}">@#%</text>`),
  neon_edges:      svg(poly('16,3 29,26 3,26', 'none').replace(`stroke="${K}"`, `stroke="${C}"`).replace('stroke-width="2.2"', 'stroke-width="3.4"') + poly('16,3 29,26 3,26', 'none')),
  little_planet:   svg(circ(16, 17, 11, C) + path('M5 17q11-8 22 0', 'none') + circ(16, 6, 3, Y) + path('M10 25q6 4 12 0', 'none', 2)),
  digital_boss:    svg(rect(3, 3, 26, 26, P) + rect(7, 7, 7, 7, Y, 0) + rect(18, 12, 7, 7, M, 0) + rect(10, 20, 9, 5, C, 0)),
  recalled_sensor: svg(poly('16,2 19,12 30,16 19,20 16,30 13,20 2,16 13,12', Y) + circ(16, 16, 3.5, W)),
  steel_wash:      svg(rect(3, 4, 26, 24, '#9fb4c7') + path('M3 11h26M3 18h26M3 25h26', 'none', 1.6)),
  fever:           svg(rect(12, 3, 8, 18, W, 4) + circ(16, 24, 5, R) + path('M16 8v14', 'none', 3)),
  double_cup:      svg(path('M7 6h18l-2 22H9z', P) + path('M8 12h16', 'none') + circ(16, 3, 2, Y)),
  xpiritualism:    svg(poly('16,2 19,13 30,16 19,19 16,30 13,19 2,16 13,13', Y) + circ(25, 7, 2, M) + circ(7, 25, 2, C)),
  crossmosh:       svg(rect(2, 8, 14, 16, C) + rect(16, 8, 14, 16, M) + path('M14 12h6M14 16h8M14 20h5', 'none', 2)),
  pixel_sort:      svg([4, 8, 13, 19, 24].map((h, i) => rect(3 + i * 5.2, 28 - h - 2, 4.2, h + 2, [M, O, Y, G, C][i], 1)).join('')),
  halftone:        svg([[8, 8, 1.5], [16, 8, 2.5], [24, 8, 3.5], [8, 16, 2.5], [16, 16, 3.5], [24, 16, 4], [8, 24, 3.5], [16, 24, 4], [24, 24, 4.2]].map(([x, y, r]) => circ(x, y, r, K)).join('')),
  trim:            svg(rect(2, 11, 28, 10, Y) + path('M10 8v16M22 8v16', 'none', 3.2) + circ(10, 8, 2.4, W) + circ(22, 24, 2.4, W)),
  concat:          svg(rect(2, 9, 13, 14, C) + rect(17, 9, 13, 14, G) + path('M14 16h4', 'none', 3)),
  soundtrack:      svg(circ(10, 24, 4.5, M) + circ(23, 21, 4.5, M) + path('M14 24V6l13-3v18', 'none', 2.6)),
  transcraibe:     svg(path('M5 5h22v15H15l-6 6v-6H5z', W) + path('M9 10h14M9 14h9', 'none', 2.2)),
  convert_mux:     svg(path('M5 11h20', 'none', 3) + poly('22,5 30,11 22,17', C) + path('M27 22H7', 'none', 3) + poly('10,16 2,22 10,28', Y)),
  proc_amp:        svg(path('M8 4v24M16 4v24M24 4v24', 'none', 2) + rect(4, 8, 8, 5, Y, 1) + rect(12, 18, 8, 5, C, 1) + rect(20, 11, 8, 5, M, 1)),
  chroma_key:      svg(rect(3, 3, 26, 26, '#2ee05c') + circ(16, 15, 6, W) + path('M8 29q8-12 16 0', W)),
  remove_background: svg(rect(3, 3, 26, 26, W) + `<circle cx="16" cy="12" r="5" fill="${M}" ${st()}/>` + path('M7 28q9-16 18 0', M) + path('M3 3l26 26', 'none', 1.4)),
  reverse:         svg(path('M26 12a10 10 0 1 0 1 8', 'none', 3) + poly('27,4 27,14 17,13', Y)),
  boomerang:       svg(path('M5 7q22-4 22 18-6-12-22-18z', Y)),
  speed:           svg(path('M4 24a12 12 0 1 1 24 0', 'none', 3) + path('M16 24l7-9', 'none', 3) + circ(16, 24, 2.6, K)),
  stabilize:       svg(rect(4, 6, 24, 20, W) + path('M16 10v12M10 16h12', 'none', 2) + circ(16, 16, 5, 'none')),
  topobeaux:       svg(path('M3 22q6-14 12-6t14-8', 'none', 2.4) + path('M3 28q8-12 14-4t12-8', 'none', 2.4) + path('M3 15q5-10 11-4t15-7', 'none', 2.4)),
  shape_synth:     svg(circ(10, 10, 6, Y) + poly('26,6 30,16 20,16', C) + rect(8, 18, 12, 10, M)),
  rotate:          svg('<g transform="rotate(-18 14 17)">' + rect(5, 8, 18, 18, Y) + '</g>' + path('M20 5a11 11 0 0 1 9 9', 'none', 2.8) + poly('30,8 30,18 22,14', C)),
  stackadelic:     svg(rect(3, 3, 18, 12, C) + rect(8, 10, 18, 12, Y) + rect(12, 17, 17, 12, M)),
  kinetic_captions: svg(path('M5 20h14', 'none', 2.4) + `<text x="16" y="17" text-anchor="middle" font-family="sans-serif" font-weight="900" font-size="15" fill="${Y}" stroke="${K}" stroke-width="1.5" paint-order="stroke">ABC</text>` + path('M3 25h10M20 25h9', 'none', 2.4)),
  vhs_camcorder:   svg(rect(3, 8, 26, 16, '#a8ad23') + circ(10, 16, 4, W) + circ(22, 16, 4, W) + rect(9, 19, 14, 3, K, 1)),
  chromatic_pulse: svg(circ(12, 16, 9, 'rgba(255,0,60,0.8)') + circ(20, 16, 9, 'rgba(0,160,255,0.8)')),
  pixelate:        svg([0, 1, 2, 3].flatMap(r => [0, 1, 2, 3].map(c => `<rect x="${4 + c * 6}" y="${4 + r * 6}" width="6" height="6" fill="${[Y, C, M, G, O, P, W][(r * 3 + c * 2) % 7]}"/>`)).join('') + `<rect x="4" y="4" width="24" height="24" fill="none" ${st()}/>`)
}

export function glyphFor(programId, family) {
  return PROGRAM_GLYPHS[programId] || FAMILY_GLYPHS[family] || FAMILY_GLYPHS.weird
}
