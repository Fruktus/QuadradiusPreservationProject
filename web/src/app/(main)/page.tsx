'use client';

import styles from './index.module.css';
import Ruffle from '@/components/ruffle/ruffle';
import FullscreenToggle from '@/components/ui/fullscreen-toggle/fullscreen-toggle';
import Footer from "@/components/ui/footer/footer";
import { useUnloadWarning } from '@/hooks/use-unload-warning';


export default function Home() {
  useUnloadWarning();

  return (
    <>
      <div className={styles.directions}>
        <a href="/directions.html" target="_blank">How to play &amp; Powerup Cheatsheet</a>
      </div>
      <FullscreenToggle />

      <Ruffle />

      <div className={styles.container}>
        <object className={styles.game}>
          <embed src="./quadradius_lobby.swf" className={styles.embed} />
        </object>
        <Footer />
      </div>
    </>
  )
}
