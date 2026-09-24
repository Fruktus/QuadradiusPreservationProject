'use client';

import { useEffect, useState } from 'react';
import { topbarIconBtn } from '@/components/ui/topbar/topbar-button';

// The icon files are used as a mask, so the icon takes the button's text colour (an <img> can't do that).
function iconStyle(isFullscreen: boolean): React.CSSProperties {
  const image = isFullscreen ? "url('/fullscreen-close.svg')" : "url('/fullscreen-open.svg')";
  return {
    maskImage: image,
    WebkitMaskImage: image,
    maskRepeat: 'no-repeat',
    WebkitMaskRepeat: 'no-repeat',
    maskPosition: 'center',
    WebkitMaskPosition: 'center',
    maskSize: 'contain',
    WebkitMaskSize: 'contain',
  };
}

export default function FullscreenToggle({ isFullscreen }: { isFullscreen: boolean }) {
  // iPhone Safari has no Fullscreen API for arbitrary elements; hide the button there instead of showing a dead one.
  const [supported, setSupported] = useState(true);
  useEffect(() => setSupported(!!document.fullscreenEnabled), []);

  if (!supported) return null;

  const handleClick = () => {
    if (!document.fullscreenElement) {
      void document.documentElement.requestFullscreen();
    } else {
      void document.exitFullscreen();
    }
  };

  return (
    <button
      type="button"
      className={topbarIconBtn}
      title={isFullscreen ? 'Exit fullscreen' : 'Toggle fullscreen'}
      aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
      onClick={handleClick}
    >
      <span aria-hidden="true" className="block h-2.5 w-2.5 bg-current" style={iconStyle(isFullscreen)} />
    </button>
  );
}
