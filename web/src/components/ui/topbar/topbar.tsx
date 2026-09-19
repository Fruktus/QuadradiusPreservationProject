'use client';

import { useEffect, useState } from 'react';
import FullscreenToggle from '@/components/ui/fullscreen-toggle';
import UserStatus from '@/components/ui/topbar/user-status';
import { topbarBtn } from '@/components/ui/topbar/topbar-button';
import { cn } from '@/lib/utils';

export default function Topbar() {
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const sync = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener('fullscreenchange', sync);
    return () => document.removeEventListener('fullscreenchange', sync);
  }, []);

  // In fullscreen mode hide the topbar, leave only exit button
  if (isFullscreen) {
    return (
      <div className="fixed left-1.5 top-1.5 z-30 opacity-60 transition-opacity hover:opacity-100 focus-within:opacity-100">
        <FullscreenToggle isFullscreen={isFullscreen} />
      </div>
    );
  }

  return (
    <header
      className={cn(
        "relative z-20 flex w-full flex-none items-center justify-between gap-2 px-1.5",
        "h-6 [@media(pointer:coarse)]:h-7",
        "bg-panel-bg",
        "bg-[url('/assets/scuff-texture.svg'),repeating-linear-gradient(100deg,rgba(255,255,255,0.04)_0px,rgba(255,255,255,0.04)_1px,transparent_1px,transparent_3px)]",
        "shadow-[inset_0_1px_0_var(--panel-shine),inset_0_-1px_0_var(--panel-edge),0_2px_4px_rgba(0,0,0,0.6)]",
        "before:pointer-events-none before:absolute before:inset-0",
        "before:bg-[linear-gradient(180deg,rgba(255,255,255,0.16)_0%,transparent_50%,rgba(0,0,0,0.16)_100%)]",
      )}
    >
      <div className="relative flex shrink-0 items-center gap-1.5">
        <FullscreenToggle isFullscreen={isFullscreen} />
        <a
          href="/directions.html"
          target="_blank"
          rel="noopener noreferrer"
          title="How to play & Powerup Cheatsheet"
          className={topbarBtn}
        >
          Manual
        </a>
      </div>
      <div className="relative flex min-w-0 items-center">
        <UserStatus />
      </div>
    </header>
  );
}
