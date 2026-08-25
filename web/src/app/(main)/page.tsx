'use client';

import Footer from "@/components/ui/footer/footer";
import Ruffle from "@/components/ruffle/ruffle";
import { useUnloadWarning } from '@/hooks/use-unload-warning';
import FullscreenToggle from '@/components/ui/fullscreen-toggle/fullscreen-toggle';

export default function Home() {
  useUnloadWarning();

  return (
    <>
      <Ruffle />
      <div className="directions">
        <a href="/directions.html" target="_blank">How to play &amp; Powerup Cheatsheet</a>
      </div>
      <FullscreenToggle />
      <div className="game-container">
        <object className="game">
          <embed src="./quadradius_lobby.swf" className="embed" />
        </object>

        <Footer />
      </div>
    </>
  )
}
