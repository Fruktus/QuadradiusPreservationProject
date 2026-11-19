"use client"

import { useEffect } from "react"
import { useFestiveMode } from "@/lib/festive"

// Mirrors the festive mode setting onto <html data-festive="on">, which the decoration styles in globals.css read.
// Lives in the layout (not the topbar) so the decorations don't depend on the topbar being rendered.
export default function FestiveSync() {
  const mode = useFestiveMode()

  useEffect(() => {
    const root = document.documentElement
    if (mode === "on") root.dataset.festive = "on"
    else delete root.dataset.festive
  }, [mode])

  return null
}
