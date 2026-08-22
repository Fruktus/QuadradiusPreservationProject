"use client"

import { useState, useEffect } from "react"

const DEFAULT_SPLASH = "Now with 100% more squares"

export default function Splash() {
  const [splash, setSplash] = useState("")

  useEffect(() => {
    async function loadSplash() {
      try {
        const res = await fetch("/splashes.txt")
        if (!res.ok) return
        const text = await res.text()
        const lines = text.split("\n").map((s: string) => s.trim()).filter(Boolean)
        if (lines.length > 0)
          setSplash(lines[Math.floor(Math.random() * lines.length)])
      } catch {
        setSplash(DEFAULT_SPLASH)
      }
    }
    loadSplash()
  }, [])

  return (
    <p
      className="splash-pulse absolute font-vt323 text-[15px] text-[#ffdd33] text-center leading-[1.2] pointer-events-none z-10"
      style={{
        top: "18px",
        right: "-18px",
        maxWidth: "110px",
        textShadow: "1px 1px 0 #885500, 2px 2px 0 rgba(0,0,0,0.4)",
      }}
    >
      {splash}
    </p>
  )
}
