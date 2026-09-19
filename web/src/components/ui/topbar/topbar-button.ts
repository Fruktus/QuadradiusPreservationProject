import { cn } from "@/lib/utils"

// Shared by every item that sits in the topbar (buttons and the username chip),
// so the bar's row height is defined in exactly one place.
export const topbarItemSize = "h-[18px] [@media(pointer:coarse)]:h-[22px] rounded-[2px]"

// Mini version of HudButton for the topbar: same palette and bevel, ~18px tall.
// `!text-*` is needed because the global `a:link/a:visited/a:hover` colours would otherwise win on anchors.
export const topbarBtn = cn(
  "inline-flex shrink-0 select-none items-center justify-center",
  topbarItemSize,
  "px-2 pt-[2px]",
  "font-rajdhani font-bold text-[12px] leading-none tracking-[2px] uppercase whitespace-nowrap",
  "border border-[#200404] bg-[#3a0a0a] !text-[#e0aaaa] cursor-pointer outline-none",
  "shadow-[inset_0_1px_0_rgba(255,150,150,0.25),inset_0_-2px_0_#1a0303]",
  "transition-[background-color,border-color,box-shadow,transform,color] duration-100",
  "hover:bg-[#e2472f] hover:!text-[#7a1f14] hover:border-[#8a2814]",
  "hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.25),inset_0_-2px_0_#8a2814]",
  "active:bg-[#c73c22] active:!text-[#5c150c] active:border-[#7a2210]",
  "active:shadow-[inset_0_1px_3px_rgba(0,0,0,0.35),inset_0_-1px_0_#7a2210]",
  "focus-visible:ring-1 focus-visible:ring-[#e2472f]",
)

// Square variant for icon-only buttons
export const topbarIconBtn = cn(topbarBtn, "w-[18px] [@media(pointer:coarse)]:w-[22px] px-0 pt-0")
// (icon button reuses topbarBtn's topbarItemSize for height; only width/padding differ)
