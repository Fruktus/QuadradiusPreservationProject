export default function Home() {
  return (
    <>
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
    </>
  )
}
