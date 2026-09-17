export default function QrLogo() {
  return (
    <div className="flex flex-col items-center gap-0 mb-2">
      <div
        className="flex flex-col items-center gap-0 w-full rounded-[6px] px-6 pt-5 pb-3
          border border-[var(--panel-groove)]
          shadow-[inset_0_1px_2px_rgba(0,0,0,0.15),inset_0_-1px_0_rgba(255,255,255,0.25)]"
      >
        <svg viewBox="0 0 200 200" width="140" height="140" aria-label="Quadradius logo">
          <circle cx="100" cy="95" r="55" fill="none" stroke="#cc2222" strokeWidth="4"/>
          <line x1="100" y1="95" x2="168" y2="163" stroke="#cc2222" strokeWidth="3" strokeLinecap="round"/>
          <circle cx="100" cy="95" r="9" fill="#cc2222"/>
          <circle cx="168" cy="163" r="9" fill="#cc2222"/>
        </svg>
        <div className="font-rajdhani font-bold text-[20px] text-[#cc2222] tracking-[5px] opacity-90 -mt-1.5">
          QUADRADIUS<sup
            className="text-[23px] tracking-normal align-super leading-none ml-0.5"
            style={{ textShadow: "0.6px 0 0 currentColor, -0.6px 0 0 currentColor, 0 0.6px 0 currentColor" }}
          >+</sup>
        </div>
      </div>
    </div>
  )
}
