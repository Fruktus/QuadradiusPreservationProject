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
      `}}/>

      <body dangerouslySetInnerHTML={{__html: `
        <div class="directions">
          <a href="/directions.html" target="_blank">How to play &amp; Powerup Cheatsheet</a>
        </div>
        <div class="fullscreen">
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
        <div class="container">
            <object class="game">
                <embed src="./quadradius_lobby.swf" class="embed" />
            </object>

            <div class="footer">
                Made possible by the
                <a href="https://github.com/Fruktus/QuadradiusPreservationProject" target="_blank">Quadradius Preservation Project</a>.
            </div>
        </div>

        <script src="fullscreen.js"></script>
      `}}/>
    </html>
  )
}
