import { apiFetch } from "./api"

export type Trophy = {
  id: string
  name: string
  awarded_at: string | null
  // data: URI of an SVG. Only ever use it as <img src>, never inline it into the DOM.
  image: string
}

// Achievements earned by player, newest first. The details come from fetchAchievement.
export type PlayerAchievement = {
  key: string
  awarded_at: string
}

export type Achievement = {
  key: string
  name: string
  description: string
  // data: URI of an SVG, or null if no image was uploaded yet. Only ever use it as <img src>, never inline it.
  image: string | null
}

export type PlayerProfile = {
  player: {
    username: string
    member_since: string | null
  }
  stats: {
    total_matches: number
    wins: number
    losses: number
    win_rate: number | null
    longest_match_seconds: number | null
    most_moves: number | null
    biggest_win_margin: number | null
    nemesis: { username: string; losses: number } | null
  }
  trophies: Trophy[]
  achievements: PlayerAchievement[]
}

export type PlayerProfileResult =
  | { status: "ok"; profile: PlayerProfile }
  | { status: "not_found" }
  | { status: "error" }

// The site is a static export, so there are no dynamic routes: the name goes in the query string.
export function playerProfileHref(username: string): string {
  return `/player?name=${encodeURIComponent(username)}`
}

export async function fetchPlayerProfile(username: string): Promise<PlayerProfileResult> {
  try {
    const res = await apiFetch(`/api/v1/players/${encodeURIComponent(username)}`)
    if (res.status === 404) return { status: "not_found" }
    if (!res.ok) return { status: "error" }
    return { status: "ok", profile: (await res.json()) as PlayerProfile }
  } catch (e) {
    console.error("failed to load player profile:", e)
    return { status: "error" }
  }
}

export type AchievementResult = { status: "ok"; achievement: Achievement } | { status: "error" }

export async function fetchAchievement(key: string): Promise<AchievementResult> {
  try {
    const res = await apiFetch(`/api/v1/achievements/${encodeURIComponent(key)}`)
    if (!res.ok) return { status: "error" }
    const body = (await res.json()) as { achievement: Achievement }
    return { status: "ok", achievement: body.achievement }
  } catch (e) {
    console.error("failed to load achievement:", e)
    return { status: "error" }
  }
}
