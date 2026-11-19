import type { SVGProps } from "react"

// Six-armed snowflake. Takes the surrounding text colour via currentColor.
export default function SnowflakeIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      {...props}
    >
      {/* the three main lines through the center */}
      <path d="M8 1.5L8 14.5M13.63 4.75L2.37 11.25M13.63 11.25L2.37 4.75" />
      {/* one chevron branch per arm */}
      <path
        strokeWidth="1.1"
        d="M6.3 2.7L8 4.3L9.7 2.7M11.74 3.88L11.2 6.15L13.44 6.82M13.44 9.18L11.2 9.85L11.74 12.12M9.7 13.3L8 11.7L6.3 13.3M4.26 12.12L4.8 9.85L2.56 9.18M2.56 6.82L4.8 6.15L4.26 3.88"
      />
    </svg>
  )
}
