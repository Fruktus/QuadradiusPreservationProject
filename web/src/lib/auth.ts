import { UserManager, WebStorageStateStore } from "oidc-client-ts"

let _userManager: UserManager | null = null

export function getUserManager(): UserManager {
  if (!_userManager) {
    _userManager = new UserManager({
      authority: window.location.origin,
      client_id: "frontend",
      redirect_uri: window.location.origin,
      userStore: new WebStorageStateStore({ store: window.localStorage }),
      loadUserInfo: false,
    })
  }
  return _userManager
}