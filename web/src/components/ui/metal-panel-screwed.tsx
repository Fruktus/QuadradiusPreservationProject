import MetalPanel from "@/components/ui/metal-panel"
import Screw from "@/components/ui/decorations/screw"
import { cn } from "@/lib/utils"

interface MetalPanelScrewedProps {
  children: React.ReactNode
  className?: string
}

export default function MetalPanelScrewed({ children, className }: MetalPanelScrewedProps) {
  return (
    <MetalPanel className={cn("p-7", className)}>
      <Screw slot="tl" />
      <Screw slot="tr" />
      <Screw slot="bl" />
      <Screw slot="br" />
      {children}
    </MetalPanel>
  )
}