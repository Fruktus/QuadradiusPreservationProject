import { cn } from "@/lib/utils"

interface HudButtonProps {
  children: React.ReactNode
  onClick?: () => void
  disabled?: boolean
  className?: string
  type?: "button" | "submit"
}

export default function HudButton({
  children,
  onClick,
  disabled = false,
  className,
  type = "button",
}: HudButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        // base
        "w-full py-3.5 rounded-sm font-rajdhani font-bold text-[22px] tracking-[5px] uppercase",
        "transition-[background-color,border-color,box-shadow,transform,color] duration-100",
        "outline-none border-2 border-[#200404]",

        // popped out, unlit — solid fill, bevel comes from box-shadow only
        // (never a background-image, so nothing has to "un-gradient" on hover)
        "bg-[#3a0a0a] text-[#e0aaaa]",
        "shadow-[inset_0_1px_0_rgba(255,150,150,0.25),inset_0_-6px_10px_rgba(0,0,0,0.35),0_4px_0_#1a0303,0_6px_12px_rgba(0,0,0,0.5)]",
        "translate-y-0",

        // hover — lit up: flat bright coral, dark bold label, like the OG button
        "hover:bg-[#e2472f] hover:text-[#7a1f14]",
        "hover:border-[#8a2814]",
        "hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.25),0_4px_0_#8a2814,0_6px_10px_rgba(0,0,0,0.4)]",

        // pressed — same coral family, sits down a touch
        "active:bg-[#c73c22] active:text-[#5c150c]",
        "active:border-[#7a2210]",
        "active:translate-y-[2px]",
        "active:shadow-[inset_0_2px_5px_rgba(0,0,0,0.35),0_2px_0_#7a2210]",

        // disabled
        "disabled:bg-[#1c0505] disabled:text-[#5a3232]",
        "disabled:translate-y-[3px]",
        "disabled:shadow-[0_1px_0_#0a0101]",
        "disabled:cursor-not-allowed",

        className
      )}
    >
      {children}
    </button>
  )
}
