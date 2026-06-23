import { Metadata } from "next"
import "@/styles/styles.css"

export const metadata: Metadata = {
  title: 'Quadradius',
  description:
    'Quadradius is a two-player turn-based strategy game from 2007 made in Flash. A game of skill, luck, and deception with the gameplay of checkerboards on steroids. Originally created by Jimmi Heiserman and Brad Kayal.',
}

export default function MainLayout() {
  return (
    <html lang="en" >
      <head dangerouslySetInnerHTML={{__html: `
        <script src="config-ruffle.js"></script>
        <script src="main.js"></script>
        <script src="fullscreen.js"></script>
      `}}/>

      <body>
        <div className="directions">
          <a href="/directions.html" target="_blank">How to play &amp; Powerup Cheatsheet</a>
        </div>
        <div className="fullscreen">
          <button id="fullscreen-toggle" title="Toggle fullscreen">
            <img
              src="fullscreen-open.svg"
              id="fullscreen-open"
              alt="Fullscreen open icon"
            />
            <img
              src="fullscreen-close.svg"
              id="fullscreen-close"
              alt="Fullscreen close icon"
            />
          </button>
        </div>
        <div className="container">
            <object className="game">
                <embed src="./quadradius_lobby.swf" className="embed" />
            </object>

            <div className="footer">
                Made possible by the <a href="https://github.com/Fruktus/QuadradiusPreservationProject" target="_blank">Quadradius Preservation Project</a>.
            </div>
        </div>
      </body>
    </html>
  )
}
