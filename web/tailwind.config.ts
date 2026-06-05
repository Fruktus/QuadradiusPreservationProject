import type { Config } from "tailwindcss";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        "text-primary": "var(--text-primary)",
        "red-dark":     "var(--red-dark)",
        "red-medium":   "var(--red-medium)",
        "red-light":    "var(--red-light)",
        "panel-bg":     "var(--panel-bg)",
        "panel-edge":   "var(--panel-edge)",
        "panel-groove": "var(--panel-groove)",
        "input-bg":       "var(--input-bg)",
        "input-border":   "var(--input-border)",
        "input-focus":    "var(--input-focus)",
        "input-text":     "var(--input-text)",
        "btn-login-bg":   "var(--btn-login-bg)",
        "btn-login-hover":"var(--btn-login-hover)",
        "btn-login-text": "var(--btn-login-text)",
        "status-error":   "var(--status-error)",
        "status-ok":      "var(--status-ok)",
        "status-busy":    "var(--status-busy)",
        "base-200": "var(--base-200)",
        "base-300": "var(--base-300)",
        "base-400": "var(--base-400)",
        "base-500": "var(--base-500)",
        "base-900": "var(--base-900)",
      },
      fontFamily: {
        vt323:      ["var(--font-vt323)"],
        silkscreen: ["var(--font-silkscreen)"],
        mono:       ["var(--font-geist-mono)"],
      },
      boxShadow: {
        "panel":       "0 0 0 1px var(--panel-shine) inset, 0 4px 8px rgba(0,0,0,0.8), 0 12px 40px rgba(0,0,0,0.7)",
        "input":       "inset 0 2px 6px rgba(0,0,0,0.5)",
        "input-focus": "inset 0 2px 6px rgba(0,0,0,0.5), 0 0 0 2px rgba(153,21,21,0.25)",
        "btn-press":   "inset 0 2px 4px rgba(0,0,0,0.6), 0 0 18px rgba(255,34,34,0.5)",
      },
    },
  },
  plugins: [],
} satisfies Config;