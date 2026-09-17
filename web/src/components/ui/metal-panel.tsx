import { cn } from "@/lib/utils"

interface MetalPanelProps {
  children: React.ReactNode
  className?: string
}

export default function MetalPanel({ children, className }: MetalPanelProps) {
  return (
    <div className={cn(
      "relative rounded-[14px] border-2 border-panel-edge bg-panel-bg",
      "bg-[url('/assets/scuff-texture.svg'),repeating-linear-gradient(100deg,rgba(255,255,255,0.04)_0px,rgba(255,255,255,0.04)_1px,transparent_1px,transparent_3px)]",
      "shadow-panel",
      "before:content-[''] before:absolute before:inset-[2px] before:rounded-[12px]",
      "before:bg-[linear-gradient(160deg,rgba(255,255,255,0.16)_0%,transparent_40%,rgba(0,0,0,0.16)_100%)]",
      "before:pointer-events-none",
      className
    )}>
      {children}
    </div>
  )
}
