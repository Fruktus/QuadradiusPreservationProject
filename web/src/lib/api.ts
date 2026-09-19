import { getUserManager, loginUrlWithRedirect } from "./auth"

export async function apiFetch(input: RequestInfo, init?: RequestInit): Promise<Response> {
  const manager = getUserManager()
  let user = await manager.getUser()

  const doFetch = (accessToken?: string) =>
    fetch(input, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...init?.headers,
      },
    })

  let res = await doFetch(user?.access_token)

  if (res.status === 401) {
    try {
      user = await manager.signinSilent()
      res = await doFetch(user?.access_token)
    } catch (e) {
      console.error("silent token refresh failed, redirecting to login:", e)
      await manager.removeUser()
      window.location.href = loginUrlWithRedirect()
      // The redirect above is async so we don't want to resolve here, throwing 401, which is already handled above.
      // Instead we never resolve as we're leaving this page anyway.
      return new Promise<Response>(() => {})
    }
  }

  return res
}
