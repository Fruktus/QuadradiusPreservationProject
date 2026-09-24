import { UserManager, WebStorageStateStore } from "oidc-client-ts"
import  { md5 } from "js-md5"

let _userManager: UserManager | null = null

export function loginUrlWithRedirect(): string {
  const here = `${window.location.pathname}${window.location.search}`
  if (here === "/" || here === "/login" || here.startsWith("/login?")) return "/login"
  if (!isSafeInternalPath(here)) return "/login"
  return `/login?redirect=${encodeURIComponent(here)}`
}

export function getUserManager(): UserManager {
  if (!_userManager) {
    _userManager = new UserManager({
      authority: window.location.origin,
      client_id: "frontend",
      redirect_uri: window.location.origin,
      userStore: new WebStorageStateStore({ store: window.localStorage }),
      loadUserInfo: true,
      automaticSilentRenew: true,
      accessTokenExpiringNotificationTimeInSeconds: 60,
    })

    _userManager.events.addSilentRenewError((err) => {
      console.error("token refresh failed:", err)
    })

    // Expiration redirect is omitted deliberately so it doesn't try to redirect to login
    // when the refresh token expires - this could cause a redirect during an active game.
    // For now only 401 from API will cause redirect.
  }
  return _userManager
}

export function hashCredentials(username: string, password: string): string {
  return md5(`++${username.toUpperCase()}++${password}`)
}

// Guard against malicious redirects:
//   - "//attacker.com" - protocol-relative, browsers may treat this as an absolute URL to a different host
//   - "/\attacker.com" - some URL parsers (and older browsers) normalize a leading backslash to a slash
export function isSafeInternalPath(path: string): boolean {
  return path.startsWith("/") && !path.startsWith("//") && !path.includes("\\")
}

// Username of the logged-in user, or null, reads from the stored session.
export async function getLoggedInUsername(): Promise<string | null> {
  try {
    const user = await getUserManager().getUser()
    // An expired access token is fine as long as it can still be refreshed.
    if (!user || (user.expired && !user.refresh_token)) return null
    const username = user.profile.username
    return typeof username === "string" && username ? username : null
  } catch {
    return null // storage blocked (private mode, etc.)
  }
}
