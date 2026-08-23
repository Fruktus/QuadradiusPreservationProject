import { UserManager, WebStorageStateStore } from "oidc-client-ts"
import  { md5 } from "js-md5"

let _userManager: UserManager | null = null

export function loginUrlWithRedirect(): string {
  const here = `${window.location.pathname}${window.location.search}`
  if (here === "/login" || here.startsWith("/login?")) return "/login"
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
      loadUserInfo: false,
      automaticSilentRenew: true,
      accessTokenExpiringNotificationTimeInSeconds: 60,
    })

    _userManager.events.addSilentRenewError((err) => {
      console.error("token refresh failed:", err)
    })

    _userManager.events.addAccessTokenExpired(() => {
      _userManager?.removeUser()
      window.location.href = loginUrlWithRedirect()
    })
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
