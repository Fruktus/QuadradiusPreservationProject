import DiscordIcon from "@/components/ui/icons/discord-icon"
import { topbarBtnClass } from "@/components/ui/topbar/topbar-button"
import { cn } from "@/lib/utils"
import config from "@/configurations/config.json"

export default function DiscordButton() {
  return (
    <a
      href={config.discordInvite}
      target="_blank"
      rel="noopener noreferrer"
      title="Join our Discord server"
      className={cn(topbarBtnClass("purple"), "gap-1.5")}
    >
      <DiscordIcon className="h-3 w-auto -translate-y-px" />
      Discord
    </a>
  )
}
