import React, { createContext, useContext, useEffect, useState } from 'react'
import { setWorkspaceRemembered } from './workspaceStore'

const SettingsContext = createContext(null)

const DEFAULTS = {
  theme: 'light',
  shadowOffset: 5,
  shadowColor: '#080808',
  shadowsEnabled: true,
  setupSeen: false,
  showSelectionBar: true,
  sliderColor: '#8654aa',
  selectionColor: 'auto',       // 'auto' = yellow in light mode, cyan in dark mode
  sidebarCollapsed: false,
  consoleCollapsed: false,
  consoleHeight: 220,
  autoOverwrite: false,
  notifyOnFinish: true,         // system notification when a run ends while the app isn't in front
  rememberWorkspace: true,      // keep the canvas across reloads / restarts (see workspaceStore.js)
  // Appearance: connection lines / node outlines, canvas wallpaper, visual "Look"
  lineMode: 'ink',              // 'ink' (default) | 'category' (each line takes its source module's colour) | 'custom'
  lineColor: '#080808',         // used when lineMode === 'custom' (also recolours node frames)
  lineWidth: 3,
  canvasBg: '',                 // absolute path of a JPEG/PNG/WebP, or '' for none
  canvasBgOpacity: 0.35,
  canvasBgFit: 'cover',         // 'cover' | 'contain' | 'tile'
  look: 'classic'               // see looks/index.js — 'classic' is exactly the original appearance
}

/**
 * Persisted app-wide appearance settings (dark mode, drop-shadow style),
 * unrelated to any one pipeline — backed by settings:get/settings:set IPC
 * (gui/src/main/index.js), which stores a small JSON file under userData.
 *
 * Applies theme + shadow tokens directly onto the document root as a
 * data-theme attribute and CSS custom-property overrides, so every
 * existing var(--shadow)/var(--ink) consumer picks up changes for free.
 */
export function SettingsProvider({ children }) {
  const [settings, setSettingsState] = useState(DEFAULTS)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    window.electronAPI.getSettings()
      .then(s => setSettingsState({ ...DEFAULTS, ...s }))
      .catch(() => {})
      .finally(() => setReady(true))
  }, [])

  useEffect(() => {
    const root = document.documentElement
    root.setAttribute('data-theme', settings.theme === 'dark' ? 'dark' : 'light')
    const offset = settings.shadowsEnabled ? settings.shadowOffset : 0
    root.style.setProperty('--shadow-offset', `${offset}px`)
    root.style.setProperty('--shadow-offset-sm', `${Math.round(offset * 0.6)}px`)
    root.style.setProperty('--shadow-color', settings.shadowColor)
    root.style.setProperty('--slider', settings.sliderColor)
    if (settings.selectionColor && settings.selectionColor !== 'auto') root.style.setProperty('--select', settings.selectionColor)
    else root.style.removeProperty('--select')
  }, [settings.theme, settings.shadowOffset, settings.shadowColor, settings.shadowsEnabled, settings.sliderColor, settings.selectionColor])

  // Lines + Look. Defaults remove every override, so the stock appearance is untouched.
  useEffect(() => {
    const root = document.documentElement
    const w = Number(settings.lineWidth)
    if (w && w !== 3) root.style.setProperty('--edge-width', String(w)); else root.style.removeProperty('--edge-width')
    if (settings.lineMode === 'custom') {
      root.style.setProperty('--edge-color', settings.lineColor)
      root.style.setProperty('--line', settings.lineColor)
    } else {
      root.style.removeProperty('--edge-color')
      root.style.removeProperty('--line')
    }
    if (settings.look && settings.look !== 'classic') root.setAttribute('data-look', settings.look)
    else root.removeAttribute('data-look')
  }, [settings.lineMode, settings.lineColor, settings.lineWidth, settings.look])

  function update(patch) {
    setSettingsState(prev => {
      const next = { ...prev, ...patch }
      window.electronAPI.setSettings(next).catch(() => {})
      return next
    })
  }

  const value = {
    ...settings,
    ready,
    setTheme: (theme) => update({ theme }),
    toggleTheme: () => update({ theme: settings.theme === 'dark' ? 'light' : 'dark' }),
    setShadowOffset: (shadowOffset) => update({ shadowOffset }),
    setShadowColor: (shadowColor) => update({ shadowColor }),
    setShadowsEnabled: (shadowsEnabled) => update({ shadowsEnabled }),
    setSetupSeen: (setupSeen) => update({ setupSeen }),
    setShowSelectionBar: (showSelectionBar) => update({ showSelectionBar }),
    setSliderColor: (sliderColor) => update({ sliderColor }),
    setSelectionColor: (selectionColor) => update({ selectionColor }),
    setSidebarCollapsed: (sidebarCollapsed) => update({ sidebarCollapsed }),
    setConsoleCollapsed: (consoleCollapsed) => update({ consoleCollapsed }),
    setConsoleHeight: (consoleHeight) => update({ consoleHeight }),
    setAutoOverwrite: (autoOverwrite) => update({ autoOverwrite }),
    setLineMode: (lineMode) => update({ lineMode }),
    setLineColor: (lineColor) => update({ lineColor }),
    setLineWidth: (lineWidth) => update({ lineWidth }),
    setCanvasBg: (canvasBg) => update({ canvasBg }),
    setCanvasBgOpacity: (canvasBgOpacity) => update({ canvasBgOpacity }),
    setCanvasBgFit: (canvasBgFit) => update({ canvasBgFit }),
    setLook: (look) => update({ look }),
    setNotifyOnFinish: (notifyOnFinish) => update({ notifyOnFinish }),
    setRememberWorkspace: (rememberWorkspace) => { setWorkspaceRemembered(rememberWorkspace); update({ rememberWorkspace }) }
  }

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  )
}

export function useSettings() {
  const ctx = useContext(SettingsContext)
  if (!ctx) throw new Error('useSettings must be used inside <SettingsProvider>')
  return ctx
}
