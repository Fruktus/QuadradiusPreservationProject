import { VT323, Rajdhani, Press_Start_2P, Geist, Geist_Mono, DotGothic16 } from "next/font/google"
import '@/styles/globals.css'

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] })
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] })
const pressStart2P = Press_Start_2P({ weight: "400", variable: "--font-press-start", subsets: ["latin"] })
const vt323 = VT323({ weight: "400", variable: "--font-vt323", subsets: ["latin"] })
const rajdhani = Rajdhani({ weight: ["600", "700"], variable: "--font-rajdhani", subsets: ["latin"] })
const dotGothic16 = DotGothic16({ weight: "400", variable: "--font-dotgothic16", subsets: ["latin"] })

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const fontVars = `${geistSans.variable} ${geistMono.variable} ${pressStart2P.variable} ${vt323.variable} ${rajdhani.variable} ${dotGothic16.variable}`
  return (
      <div className={`${fontVars} antialiased`}>
        {children}
      </div>
  )
}
