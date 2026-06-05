import { cn } from "@/lib/utils"

interface MetalPanelProps {
  children: React.ReactNode
  className?: string
}

export default function MetalPanel({ children, className }: MetalPanelProps) {
  return (
    <div className={cn(
      "relative rounded-[14px] border-2 border-panel-edge bg-panel-bg",
      "shadow-panel",
      "before:content-[''] before:absolute before:inset-[2px] before:rounded-[12px]",
      "before:bg-[linear-gradient(160deg,rgba(255,255,220,0.22)_0%,transparent_40%,rgba(0,0,0,0.12)_100%)]",
      "before:pointer-events-none",
      className
    )}>
      {children}
    </div>
  )
}