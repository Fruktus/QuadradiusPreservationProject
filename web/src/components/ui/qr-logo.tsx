export default function QrLogo() {
  return (
    <div className="flex flex-col items-center gap-0">
      <svg viewBox="0 0 200 200" width="140" height="140" aria-label="Quadradius logo">
        <circle cx="100" cy="95" r="55" fill="none" stroke="#cc2222" strokeWidth="4"/>
        <line x1="100" y1="95" x2="168" y2="163" stroke="#cc2222" strokeWidth="3" strokeLinecap="round"/>
        <circle cx="100" cy="95" r="9" fill="#cc2222"/>
        <circle cx="168" cy="163" r="9" fill="#cc2222"/>
      </svg>
      <div className="font-vt323 text-[18px] text-[#cc2222] tracking-[5px] opacity-85 -mt-1.5">
        QUADRADIUS<sup className="text-[15px] tracking-normal align-super leading-none">+</sup>
      </div>
    </div>
  )
}