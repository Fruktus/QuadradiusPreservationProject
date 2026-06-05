import { cn } from "@/lib/utils"

type StatusVariant = "idle" | "busy" | "ok" | "error"

interface StatusLineProps {
  message?: string
  variant?: StatusVariant
  className?: string
}

const variantClasses: Record<StatusVariant, string> = {
  idle:  "text-[var(--foreground)]",
  busy:  "text-status-busy",
  ok:    "text-status-ok",
  error: "text-status-error",
}
export type StatusVariant = "idle" | "busy" | "ok" | "error"

export default function StatusLine({
  message = "",
  variant = "idle",
  className,
}: StatusLineProps) {
  return (
    <p className={cn(
      "mt-4",
      "min-h-[16px] text-center font-mono text-[11px] tracking-[1.5px] uppercase",
      "transition-colors duration-200",
      variantClasses[variant],
      className,
    )}>
      {message}
    </p>
  )
}