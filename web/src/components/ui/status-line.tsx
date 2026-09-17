import { cn } from "@/lib/utils"

interface StatusLineProps {
  message?: string
  variant?: StatusVariant
  className?: string
}

const variantClasses: Record<StatusVariant, string> = {
  idle:  "text-input-text",
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
    <input
      type="text"
      readOnly
      tabIndex={message ? 0 : -1}
      value={message}
      aria-label="status"
      aria-live="polite"
      className={cn(
        "mt-4 font-dotmatrix text-lg tracking-wide text-center",
        "w-full rounded bg-input-bg border border-input-border",
        "px-3 py-2.5",
        "shadow-input outline-none caret-transparent cursor-default",
        "transition-colors duration-200",
        variantClasses[variant],
        className,
      )}
    />
  )
}
