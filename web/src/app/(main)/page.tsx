'use client';

import Footer from "@/components/ui/footer/footer";
import Ruffle from "@/components/ruffle/ruffle";
import Script from "next/script";
import { useUnloadWarning } from '@/hooks/use-unload-warning';

export default function Home() {
  useUnloadWarning();

  return (
    <>
      <Script src="/fullscreen.js" />
      <Ruffle />
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
      <div className="game-container">
        <object className="game">
          <embed src="./quadradius_lobby.swf" className="embed" />
        </object>

        <Footer />
      </div>
    </>
  )
}
