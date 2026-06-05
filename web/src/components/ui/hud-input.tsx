import { cn } from "@/lib/utils"

interface HudInputProps {
  label: string
  id: string
  type?: "text" | "password"
  placeholder?: string
  autoComplete?: string
  className?: string
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
}

export default function HudInput({
  label,
  id,
  type = "text",
  placeholder,
  autoComplete,
  className,
  value,
  onChange,
}: HudInputProps) {
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <label
        htmlFor={id}
        className="font-mono text-[11px] tracking-[2px] uppercase text-[var(--panel-groove)]"
      >
        {label}
      </label>
      <input
        id={id}
        name={id}
        type={type}
        placeholder={placeholder}
        autoComplete={autoComplete}
        value={value}
        onChange={onChange}
        spellCheck={false}
        className={cn(
          "font-vt323 text-2xl",
          "w-full rounded bg-input-bg border border-input-border",
          "px-3 py-2.5 text-input-text",
          "shadow-input caret-[var(--input-text)]",
          "placeholder:text-[var(--input-placeholder)]",
          "outline-none transition-[border-color,box-shadow] duration-150",
          "focus:border-input-focus focus:shadow-input-focus",
        )}
      />
    </div>
  )
}