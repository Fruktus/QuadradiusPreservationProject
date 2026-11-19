"use client"

import { useEffect, useState } from "react"

import { formatDate } from "@/lib/format"
import { fetchAchievement, type Achievement, type PlayerAchievement } from "@/lib/player"
import { sectionTitle, well } from "@/components/player/styles"

// Only achievements the player earned are listed, we don't want to show locked ones atm.
// Each row loads its own details, so a slow or failed one doesn't hold up the others.
export default function AchievementShelf({ entries }: { entries: PlayerAchievement[] }) {
  return (
    <section aria-labelledby="achievements-title">
      <h2 id="achievements-title" className={sectionTitle}>
        Achievements
      </h2>
      {entries.length === 0 ? (
        <div className={`${well} px-3 py-6 text-center font-dotmatrix text-lg text-[#b97070]`}>
          no achievements yet
        </div>
      ) : (
        <ul className="flex flex-col gap-2">
          {entries.map((entry) => (
            <AchievementRow key={entry.key} entry={entry} />
          ))}
        </ul>
      )}
    </section>
  )
}

type RowState = { status: "loading" } | { status: "ok"; achievement: Achievement } | { status: "error" }

function AchievementRow({ entry }: { entry: PlayerAchievement }) {
  const [state, setState] = useState<RowState>({ status: "loading" })

  useEffect(() => {
    let cancelled = false
    void fetchAchievement(entry.key).then((result) => {
      if (cancelled) return
      setState(result.status === "ok" ? { status: "ok", achievement: result.achievement } : { status: "error" })
    })
    return () => {
      cancelled = true
    }
  }, [entry.key])

  const earned = formatDate(entry.awarded_at)
  const achievement = state.status === "ok" ? state.achievement : null

  return (
    <li className={`${well} flex items-start gap-3 px-3 py-2.5`}>
      <AchievementIcon key={achievement?.image ?? "none"} src={achievement?.image ?? null} />
      <div className="min-w-0 flex-1">
        <div className="break-words font-rajdhani text-[13px] font-bold uppercase leading-tight tracking-[1px] text-input-text">
          {state.status === "loading" && "Loading..."}
          {state.status === "error" && "Could not load"}
          {achievement?.name}
        </div>
        {achievement && (
          <p className="m-0 mt-0.5 break-words font-rajdhani text-[13px] font-bold leading-snug tracking-wide text-[#b97070]">
            {achievement.description}
          </p>
        )}
        {earned && (
          <div className="mt-1 font-rajdhani text-[11px] font-bold uppercase tracking-[1px] text-[#8a5555]">
            Earned {earned}
          </div>
        )}
      </div>
    </li>
  )
}

// Placeholder shown while image is not available (loading, not uploaded, failed to load)
function AchievementIcon({ src }: { src: string | null }) {
  const [failed, setFailed] = useState(false)

  if (!src || failed) {
    return (
      <div
        aria-hidden="true"
        className="flex h-12 w-12 shrink-0 items-center justify-center rounded border border-input-border bg-[#2a0707] font-dotmatrix text-2xl leading-none text-[#661010]"
      >
        ?
      </div>
    )
  }

  // The SVG is admin-supplied, so it is only ever rendered through <img>, where scripts can't run.
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={src} alt="" onError={() => setFailed(true)} className="h-12 w-12 shrink-0 object-contain" />
}
