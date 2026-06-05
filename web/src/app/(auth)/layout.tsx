import { VT323, Silkscreen, Press_Start_2P, Geist, Geist_Mono } from "next/font/google"

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] })
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] })
const pressStart2P = Press_Start_2P({ weight: "400", variable: "--font-press-start", subsets: ["latin"] })
const vt323 = VT323({ weight: "400", variable: "--font-vt323", subsets: ["latin"] })
const silkscreen = Silkscreen({ weight: ["400", "700"], variable: "--font-silkscreen", subsets: ["latin"] })
// TODO: remove html/body when merging — root layout handles this

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const fontVars = `${geistSans.variable} ${geistMono.variable} ${pressStart2P.variable} ${vt323.variable} ${silkscreen.variable}`
  return (
    <html lang="en">
      <body className={`${fontVars} antialiased`}>
        <div
          className="pointer-events-none fixed inset-0 z-50"
          style={{
            background: "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.08) 2px, rgba(0,0,0,0.08) 4px)"
          }}
        />
        {children}
      </body>
    </html>
  )
}