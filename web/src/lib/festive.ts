import { useSyncExternalStore } from "react"

// Seasonal decorations. They are on by default during the season and the player can switch them off.
// Only the "off" choice is stored, so a missing value means "on".
const STORAGE_KEY = "qr.festive"
const CHANGE_EVENT = "qr:festive-change"

export type FestiveMode = "off-season" | "off" | "on"

// Festivities run during Dec 1 - Jan 6
export function isFestiveSeason(now: Date = new Date()): boolean {
  return now.getMonth() === 11 || (now.getMonth() === 0 && now.getDate() <= 6)
}


function isDisabled(): boolean {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === "off"
  } catch {
    return false
  }
}

export function getFestiveMode(): FestiveMode {
  if (!isFestiveSeason()) return "off-season"
  return isDisabled() ? "off" : "on"
}

export function setFestiveEnabled(enabled: boolean): void {
  try {
    if (enabled) window.localStorage.removeItem(STORAGE_KEY)
    else window.localStorage.setItem(STORAGE_KEY, "off")
  } catch {
    // storage blocked: nothing persists
  }
  window.dispatchEvent(new Event(CHANGE_EVENT))
}

function subscribe(onChange: () => void): () => void {
  window.addEventListener("storage", onChange) // another tab changed it
  window.addEventListener(CHANGE_EVENT, onChange)
  return () => {
    window.removeEventListener("storage", onChange)
    window.removeEventListener(CHANGE_EVENT, onChange)
  }
}

export function useFestiveMode(): FestiveMode {
  return useSyncExternalStore(subscribe, getFestiveMode, () => "off-season")
}
