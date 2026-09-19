import { Metadata } from "next"
import { VT323, Rajdhani, Press_Start_2P, Geist, Geist_Mono, DotGothic16 } from "next/font/google"
import "@/styles/globals.css"
import Topbar from "@/components/ui/topbar/topbar"
import Footer from "@/components/ui/footer/footer"

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] })
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] })
const pressStart2P = Press_Start_2P({ weight: "400", variable: "--font-press-start", subsets: ["latin"] })
const vt323 = VT323({ weight: "400", variable: "--font-vt323", subsets: ["latin"] })
const rajdhani = Rajdhani({ weight: ["600", "700"], variable: "--font-rajdhani", subsets: ["latin"] })
const dotGothic16 = DotGothic16({ weight: "400", variable: "--font-dotgothic16", subsets: ["latin"] })

const fontVars = [geistSans, geistMono, pressStart2P, vt323, rajdhani, dotGothic16].map(f => f.variable).join(" ")

export const metadata: Metadata = {
  title: 'Quadradius',
  description:
    'Quadradius is a two-player turn-based strategy game from 2007 made in Flash. A game of skill, luck, and deception with the gameplay of checkerboards on steroids. Originally created by Jimmi Heiserman and Brad Kayal.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-ruffle-optout>
      <body className={`${fontVars} antialiased`}>
        <div className="game-page-layout">
          <Topbar />
          <div className="game-page-layout-content">{children}</div>
          <Footer />
        </div>
      </body>
    </html>
  )
}
