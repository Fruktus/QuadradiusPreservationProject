"use client"

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import MetalPanelScrewed from "@/components/ui/metal-panel-screwed";
import QrLogo from "@/components/ui/qr-logo";
import HudInput from "@/components/ui/hud-input";
import HudButton from "@/components/ui/hud-button";
import StatusLine, { type StatusVariant } from "@/components/ui/status-line";
import { getUserManager } from "@/lib/auth";
import { hashCredentials } from "@/lib/utils";


type LoginStatus = {
  message: string
  variant: StatusVariant
}

export default function LoginPage() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [status, setStatus] = useState<LoginStatus>({ message: "", variant: "idle" })

  const router = useRouter()
  const searchParams = useSearchParams()

  async function handleLogin() {
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
      const redirect = raw.startsWith("/") ? raw : "/"

      router.push(redirect)
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "connection error"
      setStatus({ message, variant: "error" })
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-base-500">
      <MetalPanelScrewed className="w-[280px]">

        <QrLogo />
        <div className="flex flex-col gap-3">
          <HudInput
            label="Username"
            id="username"
            value={username}
            onChange={e => setUsername(e.target.value)}
          />
          <HudInput
            label="Password"
            id="password"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
          />
        </div>

        <HudButton
          className="mt-6"
          onClick={handleLogin}
          disabled={status.variant === "busy" || !username || !password}
        >
          LOGIN
        </HudButton>

        <StatusLine message={status.message} variant={status.variant} />


      </MetalPanelScrewed>

    </main>
  )
}