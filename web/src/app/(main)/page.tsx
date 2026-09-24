'use client';

import Ruffle from "@/components/ruffle/ruffle";
import { useUnloadWarning } from '@/hooks/use-unload-warning';

export default function Home() {
  useUnloadWarning();

  return (
    <>
      <Ruffle />
      <div className="game-container">
        <object className="game">
          <embed src="./quadradius_lobby.swf" className="embed" />
        </object>
      </div>
    </>
  )
}
