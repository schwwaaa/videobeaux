import React, { useRef, useState } from 'react'
import { useSettings } from '../SettingsContext'

/**
 * Header control for dark mode + drop-shadow customization. A small button
 * that opens a popover panel, matching the app's flat/bold visual language
 * (same button chrome as the "⚙ Setup" button beside it in App.jsx).
 */
export default function AppearanceMenu() {
  const { theme, toggleTheme, shadowOffset, shadowColor, shadowsEnabled,
    setShadowOffset, setShadowColor, setShadowsEnabled } = useSettings()
  const [open, setOpen] = useState(false)
  const wrapRef = useRef(null)

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
              width: 240, background: 'var(--paper)', border: 'var(--border)',
              borderRadius: 'var(--radius)', boxShadow: 'var(--shadow)',
              padding: 12, display: 'flex', flexDirection: 'column', gap: 12
            }}
          >
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
                Drop shadow
              </span>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={shadowsEnabled}
                  onChange={e => setShadowsEnabled(e.target.checked)}
                  style={{ accentColor: 'var(--purple)', cursor: 'pointer' }}
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
                style={{ accentColor: 'var(--purple)', cursor: shadowsEnabled ? 'pointer' : 'default' }}
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
