import MetalPanel from "@/components/ui/metal-panel"
import Screw from "@/components/ui/decorations/screw"
import { cn } from "@/lib/utils"

interface MetalPanelScrewedHProps {
  children: React.ReactNode
  className?: string
}

export default function MetalPanelScrewedH({ children, className }: MetalPanelScrewedHProps) {
  return (
    <MetalPanel className={cn("px-10 py-4", className)}>
      <Screw slot="tl" />
      <Screw slot="tr" />
      {children}
    </MetalPanel>
  )
}