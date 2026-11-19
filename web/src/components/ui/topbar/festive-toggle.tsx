"use client"

import SnowflakeIcon from "@/components/ui/icons/snowflake-icon"
import { topbarToggleBtn } from "@/components/ui/topbar/topbar-button"
import { setFestiveEnabled, useFestiveMode } from "@/lib/festive"

// Lit toggle button that switches the seasonal decorations. Meant to be shown only during holidays
export default function FestiveToggle() {
  const mode = useFestiveMode()
  if (mode === "off-season") return null

  const on = mode === "on"
  const label = on ? "Festive decorations: on" : "Festive decorations: off"
  return (
    <button
      type="button"
      aria-pressed={on}
      aria-label="Festive decorations"
      title={label}
      onClick={() => setFestiveEnabled(!on)}
      className={topbarToggleBtn(on)}
    >
      <SnowflakeIcon className="h-3 w-3" />
    </button>
  )
}
