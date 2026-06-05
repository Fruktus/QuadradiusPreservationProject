import type { Metadata } from "next"
import { Geist, Geist_Mono, Press_Start_2P, VT323, Silkscreen } from "next/font/google"
import '@/styles/globals.css'

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] })
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] })
const pressStart2P = Press_Start_2P({ weight: "400", variable: "--font-press-start", subsets: ["latin"] })
const vt323 = VT323({ weight: "400", variable: "--font-vt323", subsets: ["latin"] })
const silkscreen = Silkscreen({ weight: ["400", "700"], variable: "--font-silkscreen", subsets: ["latin"] })

export const metadata: Metadata = {
  title: 'Quadradius',
  description: 'Quadradius is a two-player turn-based strategy game from 2007 made in Flash. A game of skill, luck, and deception, with the gameplay of checkerboards on steroids. Originally created by Jimmi Heiserman and Brad Kayal.',
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`
        ${geistSans.variable} ${geistMono.variable}
        ${pressStart2P.variable} ${vt323.variable} ${silkscreen.variable}
        antialiased
      `}>
        {children}
      </body>
    </html>
  )
}