"use client"

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import MetalPanelScrewed from "@/components/ui/metal-panel-screwed";
import QrLogo from "@/components/ui/qr-logo";
import HudInput from "@/components/ui/hud-input";
import HudButton from "@/components/ui/hud-button";
import StatusLine, { type StatusVariant } from "@/components/ui/status-line";
import { getUserManager, hashCredentials, isSafeInternalPath } from "@/lib/auth";
import Splash from "@/components/ui/splash";


type LoginStatus = {
  message: string
  variant: StatusVariant
}

// Converts error to user-friendly message
function friendlyLoginError(e: unknown): string {
  const code = typeof e === "object" && e !== null && "error" in e
    ? (e as { error?: unknown }).error
    : undefined

  switch (code) {
    case "invalid_grant":
      return "invalid username or password"
    case "unauthorized_client":
    case "access_denied":
      return "account not authorized"
    default:
      return "unable to sign in, please contact admin"
  }
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginContent />
    </Suspense>
  );
}

function LoginContent() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [status, setStatus] = useState<LoginStatus>({ message: "", variant: "idle" })

  const router = useRouter()
  const searchParams = useSearchParams()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (!username || !password) {
      setStatus({ message: "fill in all fields", variant: "error" })
      return
    }

    setStatus({ message: "authenticating...", variant: "busy" })

    try {
      await getUserManager().signinResourceOwnerCredentials({
        username,
        password: hashCredentials(username, password),
      })
      setStatus({ message: "OK", variant: "ok" })

      await new Promise(r => setTimeout(r, 600))

      const raw = searchParams.get("redirect") ?? "/"
      const redirect = isSafeInternalPath(raw) ? raw : "/"

      router.push(redirect)
    } catch (e: unknown) {
      console.error("login failed:", e)
      setStatus({ message: friendlyLoginError(e), variant: "error" })
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-base-500">
      <MetalPanelScrewed className="w-[280px]">

        <Splash />
        <QrLogo />
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          <div className="flex flex-col gap-3">
            <HudInput
              label="Username"
              id="username"
              autoComplete="username"
              value={username}
              onChange={e => setUsername(e.target.value)}
            />
            <HudInput
              label="Password"
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={e => setPassword(e.target.value)}
            />
          </div>

          <HudButton
            type="submit"
            disabled={status.variant === "busy" || !username || !password}
          >
            LOGIN
          </HudButton>
        </form>

        <StatusLine message={status.message} variant={status.variant} />


      </MetalPanelScrewed>

    </main>
  )
}
