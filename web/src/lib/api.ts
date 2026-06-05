import { getUserManager } from "./auth"

export async function apiFetch(input: RequestInfo, init?: RequestInit): Promise<Response> {
  const user = await getUserManager().getUser()
  
  return fetch(input, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(user?.access_token
        ? { Authorization: `Bearer ${user.access_token}` }
        : {}),
      ...init?.headers,
    },
  })
}