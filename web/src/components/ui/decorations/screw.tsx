type ScrewSlot = "tl" | "tr" | "bl" | "br"

interface ScrewProps {
  slot: ScrewSlot
}

const positions: Record<ScrewSlot, string> = {
  tl: "top-[10px] left-[10px]",
  tr: "top-[10px] right-[10px]",
  bl: "bottom-[10px] left-[10px]",
  br: "bottom-[10px] right-[10px]",
}
// A couple of things to notice here:
// Record<ScrewSlot, string> is a TypeScript utility type meaning "an object where every key is a ScrewSlot and every value is a string." It's just a typed object — useful here because TypeScript will complain if you forget one of the four positions.
// The bg-[radial-gradient(...)] is one of those Tailwind escape-hatch brackets again. Tailwind can't generate every possible gradient so complex ones still go in brackets. That's fine — the colors inside it still reference CSS variables so the token layer still holds.
// The two <span> elements are the Phillips cross. In the original HTML these were ::before and ::after pseudo-elements. In React we avoid CSS pseudo-elements where we can because they can't be expressed in JSX — real elements are easier to reason about.


export default function Screw({ slot }: ScrewProps) {
  return (
    <div className={`absolute ${positions[slot]} w-[14px] h-[14px] rounded-full
      bg-[radial-gradient(circle_at_35%_35%,var(--screw-shine),var(--screw-bg)_50%,#1a1a1a)]
      border border-[#111]
      shadow-[0_1px_2px_rgba(0,0,0,0.8),inset_0_1px_0_rgba(255,255,255,0.08)]`}
    >
      {/* horizontal bar of the Phillips cross */}
      <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
        w-[8px] h-[1.5px] bg-black/60 rounded-sm rotate-45 block" />
      {/* vertical bar */}
      <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
        w-[8px] h-[1.5px] bg-black/60 rounded-sm -rotate-45 block" />
    </div>
  )
}