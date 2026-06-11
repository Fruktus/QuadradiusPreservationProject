import '@/styles/globals.css'

export const metadata = {
  title: 'Quadradius',
  description: 'Quadradius is a two-player turn-based strategy game from 2007 made in Flash. A game of skill, luck, and deception, with the gameplay of checkerboards on steroids. Originally created by Jimmi Heiserman and Brad Kayal.',
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function MainLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <main>{children}</main>
      </body>
    </html>
  )
}
