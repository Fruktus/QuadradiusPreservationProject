import type { SVGProps } from "react"

// Simple "player" glyph: round head over a rounded, cylinder-like body.
// Takes the surrounding text colour via currentColor.
export default function PersonIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 16 16"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      {...props}
    >
      <circle cx="8" cy="4.4" r="2.9" />
      <path d="M3.6 15.5v-3.1a3.8 3.8 0 0 1 3.8-3.8h1.2a3.8 3.8 0 0 1 3.8 3.8v3.1z" />
    </svg>
  )
}
