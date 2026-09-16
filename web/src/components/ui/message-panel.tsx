import MetalPanelScrewed from "@/components/ui/metal-panel-screwed"
import { cn } from "@/lib/utils"
import { Doto } from "next/font/google"

const doto = Doto({ weight: "600", variable: "--font-doto", subsets: ["latin"] })


export type MessageVariant = "idle" | "busy" | "ok" | "error"

interface MessagePanelProps {
  message: string
  variant?: MessageVariant
  className?: string
}

const variantClasses: Record<MessageVariant, string> = {
  idle:  "text-input-text",
  busy:  "text-status-busy",
  ok:    "text-status-ok",
  error: "text-status-error",
}

export default function MessagePanel({
  message,
  variant = "idle",
  className,
}: MessagePanelProps) {
  return (
    <MetalPanelScrewed className={cn("w-[280px]", className)}>
      <div
        role="alert"
        className={cn(
          doto.variable,
          "font-doto text-2xl",
          "w-full rounded bg-input-bg border border-input-border",
          "px-3 py-2.5 min-h-[100px]",
          "shadow-input",
          "flex items-center justify-center text-center",
          variantClasses[variant],
        )}
      >
        {message}
      </div>
    </MetalPanelScrewed>
  )
}
