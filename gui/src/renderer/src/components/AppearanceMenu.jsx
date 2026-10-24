import React, { useRef, useState } from 'react'
import { useSettings } from '../SettingsContext'
import { LOOKS, resolveLook } from '../looks'
import { refreshArtOverrides, artInfo, useArtVersion, ART_COUNT } from '../looks/output-art/art'

/**
 * Header control for dark mode + drop-shadow customization. A small button
 * that opens a popover panel, matching the app's flat/bold visual language
 * (same button chrome as the "⚙ Setup" button beside it in App.jsx).
 */
export default function AppearanceMenu() {
  const { theme, toggleTheme, shadowOffset, shadowColor, shadowsEnabled,
    setShadowOffset, setShadowColor, setShadowsEnabled, showSelectionBar, setShowSelectionBar, sliderColor, setSliderColor, selectionColor, setSelectionColor,
    rememberWorkspace, setRememberWorkspace, notifyOnFinish, setNotifyOnFinish,
    look, setLook, lineMode, setLineMode, lineColor, setLineColor, lineWidth, setLineWidth,
    canvasBg, setCanvasBg, canvasBgOpacity, setCanvasBgOpacity, canvasBgFit, setCanvasBgFit } = useSettings()
  const [open, setOpen] = useState(false)
  const wrapRef = useRef(null)
  useArtVersion()
  const [art, setArt] = useState({ busy: false, line: '', done: 0, total: 0, error: '' })
  const artListener = useRef(null)

  const chooseClip = async () => {
    const p = await window.electronAPI.openFile([{ name: 'Video', extensions: ['mp4', 'mov', 'm4v', 'mkv', 'webm', 'avi'] }])
    if (!p) return
    setArt({ busy: true, line: 'Starting…', done: 0, total: 0, error: '' })
    artListener.current = window.electronAPI.onArtProgress(d => {
      setArt(a => ({ ...a, line: d.line.replace(/^\s*\[\s*\d+\/\d+\]\s*/, '').slice(0, 60), done: d.done ?? a.done, total: d.total ?? a.total }))
    })
    const r = await window.electronAPI.artGenerate({ source: p, start: 0.5, duration: 4 })
    artListener.current?.()
    if (r?.ok) await refreshArtOverrides()
    setArt({ busy: false, line: '', done: 0, total: 0, error: r?.ok ? '' : (r?.error || 'Could not make previews.') })
  }
  const resetClip = async () => { await window.electronAPI.artReset(); await refreshArtOverrides() }

  return (
    <div ref={wrapRef} style={{ position: 'relative', WebkitAppRegion: 'no-drag' }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          background: 'var(--paper)', color: 'var(--ink)',
          padding: '5px 10px', borderRadius: 'var(--radius-sm)',
          fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 11,
          border: '2px solid var(--ink)', cursor: 'pointer'
        }}
      >
        🎨 Appearance
      </button>

      {open && (
        <>
          {/* Click-outside catcher */}
          <div
            onClick={() => setOpen(false)}
            style={{ position: 'fixed', inset: 0, zIndex: 40 }}
          />
          <div
            style={{
              position: 'absolute', top: 'calc(100% + 8px)', right: 0, zIndex: 41,
              width: 260, background: 'var(--paper)', border: 'var(--border)',
              borderRadius: 'var(--radius)', boxShadow: 'var(--shadow)',
              padding: 12, display: 'flex', flexDirection: 'column', gap: 12,
              maxHeight: 'calc(100vh - 90px)', overflowY: 'auto'
            }}
          >
            {LOOKS.length > 1 && (
              <>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 11 }}>Look</span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                    {LOOKS.map(l => {
                      const on = resolveLook(look) === l.id
                      return (
                        <button key={l.id} title={l.blurb} onClick={() => setLook(l.id)}
                                style={{ padding: '2px 9px', fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 700, borderRadius: 999,
                                         background: on ? 'var(--select)' : 'var(--paper)', color: on ? '#080808' : 'var(--ink)',
                                         border: '2px solid var(--ink)', cursor: 'pointer' }}>
                          {l.label}
                        </button>
                      )
                    })}
                  </div>
                  <span style={{ fontSize: 10, color: 'var(--muted-dim)' }}>Classic is always one click away.</span>
                </div>
                <div style={{ height: 1, background: 'var(--gray)' }} />
              </>
            )}

            {resolveLook(look) !== 'classic' && (
              <>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 11 }}>Module previews</span>
                  <span style={{ fontSize: 10, color: 'var(--muted-dim)' }}>
                    {artInfo().count
                      ? `From your clip: ${(artInfo().source || '').replace(/^user clip: /, '') || 'custom'} (${artInfo().count} modules)`
                      : `Built-in clip (${ART_COUNT} modules)`}
                  </span>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                    <button disabled={art.busy} onClick={chooseClip}
                            title="Pick a video; every module is run on it to make the preview pictures (takes a few minutes)"
                            style={{ padding: '3px 10px', fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 700, borderRadius: 6,
                                     background: 'var(--yellow)', color: '#080808', border: '2px solid var(--ink)', cursor: art.busy ? 'default' : 'pointer', opacity: art.busy ? 0.6 : 1 }}>
                      Choose clip…
                    </button>
                    {art.busy && (
                      <button onClick={() => window.electronAPI.artCancel()}
                              style={{ padding: '3px 8px', fontSize: 10, fontFamily: 'var(--font-mono)', borderRadius: 6, background: 'var(--paper)',
                                       color: 'var(--ink)', border: '2px solid var(--ink)', cursor: 'pointer' }}>Cancel</button>
                    )}
                    {!art.busy && artInfo().count > 0 && (
                      <button onClick={resetClip}
                              style={{ padding: '3px 8px', fontSize: 10, fontFamily: 'var(--font-mono)', borderRadius: 6, background: 'var(--paper)',
                                       color: 'var(--ink)', border: '2px solid var(--ink)', cursor: 'pointer' }}>Use built-in</button>
                    )}
                  </div>
                  {art.busy && (
                    <>
                      <div style={{ height: 8, border: '2px solid var(--ink)', borderRadius: 5, overflow: 'hidden', background: 'var(--paper-dim)' }}>
                        <div style={{ height: '100%', width: `${art.total ? Math.round(100 * art.done / art.total) : 8}%`, background: 'var(--slider)' }} />
                      </div>
                      <span style={{ fontSize: 10, color: 'var(--muted-dim)', fontFamily: 'var(--font-mono)' }}>
                        {art.total ? `${art.done}/${art.total} · ` : ''}{art.line}
                      </span>
                    </>
                  )}
                  {art.error && <span style={{ fontSize: 10, color: 'var(--coral)' }}>❌ {art.error}</span>}
                </div>
                <div style={{ height: 1, background: 'var(--gray)' }} />
              </>
            )}

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 11 }}>
                Dark mode
              </span>
              <button
                onClick={toggleTheme}
                style={{
                  background: theme === 'dark' ? 'var(--purple)' : 'var(--paper-dim)',
                  color: theme === 'dark' ? 'var(--paper)' : 'var(--ink)',
                  border: '2px solid var(--ink)', borderRadius: 999,
                  padding: '3px 10px', fontFamily: 'var(--font-mono)',
                  fontWeight: 700, fontSize: 10, cursor: 'pointer'
                }}
              >
                {theme === 'dark' ? 'ON' : 'OFF'}
              </button>
            </div>

            <div style={{ height: 1, background: 'var(--gray)' }} />

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 11 }}>
                Notify when done
              </span>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}
                     title="A system notification when a run finishes or fails while Videobeaux isn't the front window.">
                <input type="checkbox" checked={notifyOnFinish !== false} onChange={e => setNotifyOnFinish(e.target.checked)}
                       style={{ accentColor: 'var(--slider)', cursor: 'pointer' }} />
                <span style={{ fontSize: 10, color: 'var(--muted-dim)' }}>On</span>
              </label>
            </div>

            <div style={{ height: 1, background: 'var(--gray)' }} />

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 11 }}>
                Remember workspace
              </span>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}
                     title="Keeps your canvas and view, and brings it back if the app reloads, restarts or the computer wakes from sleep. Undo history is not kept.">
                <input type="checkbox" checked={rememberWorkspace !== false} onChange={e => setRememberWorkspace(e.target.checked)}
                       style={{ accentColor: 'var(--slider)', cursor: 'pointer' }} />
                <span style={{ fontSize: 10, color: 'var(--muted-dim)' }}>On</span>
              </label>
            </div>

            <div style={{ height: 1, background: 'var(--gray)' }} />

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 11 }}>
                Selection bar
              </span>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}
                     title="The small bar with Copy / Delete buttons that appears when programs are selected. Shortcuts keep working when it's off.">
                <input
                  type="checkbox"
                  checked={showSelectionBar}
                  onChange={e => setShowSelectionBar(e.target.checked)}
                  style={{ accentColor: 'var(--slider)', cursor: 'pointer' }}
                />
                <span style={{ fontSize: 10, color: 'var(--muted-dim)' }}>Show</span>
              </label>
            </div>

            <div style={{ height: 1, background: 'var(--gray)' }} />

            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 11 }}>Slider color</span>
              <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
                <input
                  type="color"
                  value={/^#[0-9a-fA-F]{6}$/.test(sliderColor) ? sliderColor : '#8654aa'}
                  onChange={e => setSliderColor(e.target.value)}
                  title="Slider color"
                  style={{ width: 32, height: 28, padding: 0, border: '2px solid var(--ink)', borderRadius: 6, background: 'none', flexShrink: 0 }}
                />
                <input
                  type="text"
                  value={sliderColor}
                  onChange={e => setSliderColor(e.target.value)}
                  style={{ flex: 1, minWidth: 0, fontFamily: 'var(--font-mono)', fontSize: 11, border: '2px solid var(--ink)',
                           borderRadius: 6, padding: '4px 8px', background: 'var(--paper)', color: 'var(--ink)' }}
                />
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                {[['#8654aa', 'purple'], ['#ff6847', 'coral'], ['#32b9df', 'cyan'], ['#a8ad23', 'lime'], ['#ffe500', 'yellow'], ['#d52c91', 'magenta']].map(([c, n]) => (
                  <button key={c} title={n} onClick={() => setSliderColor(c)}
                          style={{ width: 22, height: 22, padding: 0, borderRadius: '50%', background: c,
                                   border: sliderColor.toLowerCase() === c ? '3px solid var(--ink)' : '2px solid var(--ink)' }} />
                ))}
              </div>
            </div>

            <div style={{ height: 1, background: 'var(--gray)' }} />

            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 11 }}>Selection color</span>
              <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                <button onClick={() => setSelectionColor('auto')} title="Yellow in light mode, cyan in dark mode"
                        style={{ padding: '1px 8px', fontSize: 10, fontFamily: 'var(--font-mono)', borderRadius: 999,
                                 background: selectionColor === 'auto' ? 'var(--select)' : 'var(--paper)', color: selectionColor === 'auto' ? '#080808' : 'var(--ink)' }}>
                  auto
                </button>
                {[['#ffe500', 'yellow'], ['#6ff3ff', 'cyan'], ['#ff5ccf', 'pink'], ['#9dff4d', 'lime'], ['#ffffff', 'white'], ['#ff9f1c', 'orange']].map(([c, n]) => (
                  <button key={c} title={n} onClick={() => setSelectionColor(c)}
                          style={{ width: 22, height: 22, padding: 0, borderRadius: '50%', background: c,
                                   border: selectionColor.toLowerCase() === c ? '3px solid var(--ink)' : '2px solid var(--ink)' }} />
                ))}
                <input type="color" value={/^#[0-9a-fA-F]{6}$/.test(selectionColor) ? selectionColor : '#6ff3ff'} onChange={e => setSelectionColor(e.target.value)}
                       title="Custom selection color" style={{ width: 26, height: 24, padding: 0, border: '2px solid var(--ink)', borderRadius: 6, background: 'none' }} />
              </div>
            </div>

            <div style={{ height: 1, background: 'var(--gray)' }} />

            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 11 }}>Lines</span>
              <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                {[['ink', 'Ink', 'Black lines (white in dark mode) — the original look'],
                  ['category', 'By module', "Each connection takes the colour of the module it leaves"],
                  ['custom', 'Custom', 'One colour for every connection and node outline']].map(([id, label, tip]) => (
                  <button key={id} title={tip} onClick={() => setLineMode(id)}
                          style={{ padding: '2px 9px', fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 700, borderRadius: 999,
                                   background: lineMode === id ? 'var(--select)' : 'var(--paper)', color: lineMode === id ? '#080808' : 'var(--ink)',
                                   border: '2px solid var(--ink)', cursor: 'pointer' }}>
                    {label}
                  </button>
                ))}
              </div>
              {lineMode === 'custom' && (
                <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
                  <input type="color" value={/^#[0-9a-fA-F]{6}$/.test(lineColor) ? lineColor : '#080808'}
                         onChange={e => setLineColor(e.target.value)} title="Line colour"
                         style={{ width: 32, height: 28, padding: 0, border: '2px solid var(--ink)', borderRadius: 6, background: 'none', flexShrink: 0 }} />
                  <input type="text" value={lineColor} onChange={e => setLineColor(e.target.value)}
                         style={{ flex: 1, minWidth: 0, fontFamily: 'var(--font-mono)', fontSize: 11, border: '2px solid var(--ink)',
                                  borderRadius: 6, padding: '4px 8px', background: 'var(--paper)', color: 'var(--ink)' }} />
                </div>
              )}
              <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--muted-dim)' }}>Connection thickness: {lineWidth}px</span>
                <input type="range" min={1} max={8} step={1} value={lineWidth}
                       onChange={e => setLineWidth(Number(e.target.value))} style={{ accentColor: 'var(--slider)', cursor: 'pointer' }} />
              </label>
            </div>

            <div style={{ height: 1, background: 'var(--gray)' }} />

            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 11 }}>Canvas background</span>
              <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                <button
                  onClick={async () => {
                    const p = await window.electronAPI.openFile([{ name: 'Images', extensions: ['jpg', 'jpeg', 'png', 'webp'] }])
                    if (p) setCanvasBg(p)
                  }}
                  style={{ padding: '3px 10px', fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 700, borderRadius: 6,
                           background: 'var(--yellow)', color: '#080808', border: '2px solid var(--ink)', cursor: 'pointer' }}>
                  {canvasBg ? 'Change image…' : 'Choose image…'}
                </button>
                {canvasBg && (
                  <button onClick={() => setCanvasBg('')}
                          style={{ padding: '3px 8px', fontSize: 10, fontFamily: 'var(--font-mono)', borderRadius: 6,
                                   background: 'var(--paper)', color: 'var(--ink)', border: '2px solid var(--ink)', cursor: 'pointer' }}>
                    Remove
                  </button>
                )}
              </div>
              {canvasBg && (
                <>
                  <span title={canvasBg} style={{ fontSize: 10, color: 'var(--muted-dim)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {canvasBg.split(/[\\/]/).pop()}
                  </span>
                  <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--muted-dim)' }}>
                      Opacity: {Math.round(canvasBgOpacity * 100)}%
                    </span>
                    <input type="range" min={0} max={100} step={5} value={Math.round(canvasBgOpacity * 100)}
                           onChange={e => setCanvasBgOpacity(Number(e.target.value) / 100)}
                           style={{ accentColor: 'var(--slider)', cursor: 'pointer' }} />
                  </label>
                  <div style={{ display: 'flex', gap: 5 }}>
                    {[['cover', 'Fill'], ['contain', 'Fit'], ['tile', 'Tile']].map(([id, label]) => (
                      <button key={id} onClick={() => setCanvasBgFit(id)}
                              style={{ padding: '1px 8px', fontSize: 10, fontFamily: 'var(--font-mono)', borderRadius: 999,
                                       background: canvasBgFit === id ? 'var(--select)' : 'var(--paper)', color: canvasBgFit === id ? '#080808' : 'var(--ink)',
                                       border: '2px solid var(--ink)', cursor: 'pointer' }}>
                        {label}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>

            <div style={{ height: 1, background: 'var(--gray)' }} />

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 11 }}>
                Drop shadow
              </span>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={shadowsEnabled}
                  onChange={e => setShadowsEnabled(e.target.checked)}
                  style={{ accentColor: 'var(--slider)', cursor: 'pointer' }}
                />
                <span style={{ fontSize: 10, color: 'var(--muted-dim)' }}>Enabled</span>
              </label>
            </div>

            <label style={{ display: 'flex', flexDirection: 'column', gap: 4, opacity: shadowsEnabled ? 1 : 0.4 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--muted-dim)' }}>
                Offset: {shadowOffset}px
              </span>
              <input
                type="range"
                min={0}
                max={10}
                step={1}
                value={shadowOffset}
                disabled={!shadowsEnabled}
                onChange={e => setShadowOffset(Number(e.target.value))}
                style={{ accentColor: 'var(--slider)', cursor: shadowsEnabled ? 'pointer' : 'default' }}
              />
            </label>

            <div style={{ display: 'flex', gap: 5, alignItems: 'center', opacity: shadowsEnabled ? 1 : 0.4 }}>
              <input
                type="color"
                value={/^#[0-9a-fA-F]{6}$/.test(shadowColor) ? shadowColor : '#080808'}
                disabled={!shadowsEnabled}
                onChange={e => setShadowColor(e.target.value)}
                title="Shadow color"
                style={{
                  width: 32, height: 28, padding: 0, border: '2px solid var(--ink)',
                  borderRadius: 6, cursor: shadowsEnabled ? 'pointer' : 'default',
                  background: 'none', flexShrink: 0
                }}
              />
              <input
                type="text"
                value={shadowColor}
                disabled={!shadowsEnabled}
                onChange={e => setShadowColor(e.target.value)}
                style={{
                  flex: 1, minWidth: 0, fontFamily: 'var(--font-mono)', fontSize: 11,
                  border: '2px solid var(--ink)', borderRadius: 6, padding: '4px 8px',
                  background: 'var(--paper)', color: 'var(--ink)'
                }}
              />
            </div>
          </div>
        </>
      )}
    </div>
  )
}
