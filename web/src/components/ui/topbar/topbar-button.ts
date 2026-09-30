import { cn } from "@/lib/utils"

// Shared by every item that sits in the topbar (buttons and the username chip),
// so the bar's row height is defined in exactly one place.
export const topbarItemSize = "h-[18px] [@media(pointer:coarse)]:h-[22px] rounded-[2px]"

export type TopbarBtnColor = "red" | "purple"

const topbarBtnBase = cn(
  "inline-flex shrink-0 select-none items-center justify-center",
  topbarItemSize,
  "px-2 pt-[2px]",
  "font-rajdhani font-bold text-[12px] leading-none tracking-[2px] uppercase whitespace-nowrap",
  "border cursor-pointer outline-none",
  "transition-[background-color,border-color,box-shadow,transform,color] duration-100",
  "focus-visible:ring-1",
)

// Colour variants. Tailwind needs complete class strings, so each variant is spelled out in full.
// `!text-*` is needed because the global `a:link/a:visited/a:hover` colours would otherwise win on anchors.
const topbarBtnColors: Record<TopbarBtnColor, string> = {
  red: cn(
    "border-[#200404] bg-[#3a0a0a] !text-[#e0aaaa]",
    "shadow-[inset_0_1px_0_rgba(255,150,150,0.25),inset_0_-2px_0_#1a0303]",
    "hover:bg-[#e2472f] hover:!text-[#7a1f14] hover:border-[#8a2814]",
    "hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.25),inset_0_-2px_0_#8a2814]",
    "active:bg-[#c73c22] active:!text-[#5c150c] active:border-[#7a2210]",
    "active:shadow-[inset_0_1px_3px_rgba(0,0,0,0.35),inset_0_-1px_0_#7a2210]",
    "focus-visible:ring-[#e2472f]",
  ),
  purple: cn(
    "border-[#0e0620] bg-[#2a1650] !text-[#b9a6e8]",
    "shadow-[inset_0_1px_0_rgba(170,150,255,0.25),inset_0_-2px_0_#120a2a]",
    "hover:bg-[#5865f2] hover:!text-[#141a5c] hover:border-[#343fb0]",
    "hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.25),inset_0_-2px_0_#343fb0]",
    "active:bg-[#4752c4] active:!text-[#0e1240] active:border-[#2c3590]",
    "active:shadow-[inset_0_1px_3px_rgba(0,0,0,0.35),inset_0_-1px_0_#2c3590]",
    "focus-visible:ring-[#5865f2]",
  ),
}

// Mini version of HudButton for the topbar: same bevel, ~18px tall, colour picked by `color`.
export const topbarBtnClass = (color: TopbarBtnColor = "red") => cn(topbarBtnBase, topbarBtnColors[color])

// Default (red) button, kept so existing imports keep working
export const topbarBtn = topbarBtnClass()

// Square variant for icon-only buttons
export const topbarIconBtn = cn(topbarBtn, "w-[18px] [@media(pointer:coarse)]:w-[22px] px-0 pt-0")
// (icon button reuses topbarBtn's topbarItemSize for height; only width/padding differ)
