import { cn } from "@/lib/utils"

interface HudButtonProps {
  children: React.ReactNode
  onClick?: () => void
  disabled?: boolean
  className?: string
}

export default function HudButton({
  children,
  onClick,
  disabled = false,
  className,
}: HudButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        // base
        "w-full py-3.5 rounded font-vt323 text-[26px] tracking-[6px] uppercase",
        "transition-[background,box-shadow,transform,color] duration-100",
        "outline-none border border-[#2a0505]",

        // popped out, unlit
        "bg-[#3a0a0a] text-[#7a3333]",
        "shadow-[0_4px_0_#1a0303,0_6px_12px_rgba(0,0,0,0.5)]",
        "translate-y-0",

        // hover — glows from within
        "hover:bg-[#5c0f0f] hover:text-btn-login-text",
        "hover:shadow-[0_4px_0_#1a0303,0_6px_12px_rgba(0,0,0,0.5),inset_0_0_18px_rgba(255,50,50,0.2),0_0_12px_rgba(255,50,50,0.15)]",

        // pressed
        "active:bg-[#4a0c0c] active:text-[#ff4444]",
        "active:translate-y-[3px]",
        "active:shadow-[0_1px_0_#1a0303,inset_0_0_18px_rgba(255,50,50,0.3),0_0_8px_rgba(255,50,50,0.2)]",

        // disabled — pressed down, dim, unlit
        "disabled:bg-[#1a0505] disabled:text-[#3a1a1a]",
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