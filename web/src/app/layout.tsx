import { Metadata } from "next"
import "@/styles/styles.css"

export const metadata: Metadata = {
  title: 'Quadradius',
  description:
    'Quadradius is a two-player turn-based strategy game from 2007 made in Flash. A game of skill, luck, and deception with the gameplay of checkerboards on steroids. Originally created by Jimmi Heiserman and Brad Kayal.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" >
      <body>
        {children}
      </body>
    </html>
  )
}
