import PersonIcon from "@/components/ui/icons/person-icon"
import { topbarIconBtn } from "@/components/ui/topbar/topbar-button"
import { playerProfileHref } from "@/lib/player"

// Opens the player's profile in a new tab: the game page may have a match running, and a plain
// in-app navigation would silently end it (the unload warning doesn't fire for Next's client-side routing).
export default function ProfileButton({ username }: { username: string }) {
  return (
    <a
      href={playerProfileHref(username)}
      target="_blank"
      rel="noopener noreferrer"
      title="My profile"
      aria-label="My profile"
      className={topbarIconBtn}
    >
      <PersonIcon className="h-3 w-3" />
    </a>
  )
}
