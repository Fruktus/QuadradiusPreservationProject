'use client';

import { useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import config from '@/configurations/config.json';

export default function RuffleLoader() {
  const searchParams = useSearchParams();

  useEffect(() => {
    const queryVersion = searchParams.get('ruffle_version');
    const version = queryVersion ?? config.ruffleVersion ?? '';
    const ruffleUrl = version
      ? `https://unpkg.com/@ruffle-rs/ruffle@${version}/ruffle.js`
      : 'https://unpkg.com/@ruffle-rs/ruffle';

    // Prevent double-injection of the Ruffle script (not relevant for generated pages)
    const existing = document.querySelector(`script[src="${ruffleUrl}"]`);
    if (existing) return;

    // Create the script manually to ensure that it runs after everything else is ready
    const script = document.createElement('script');
    script.src = ruffleUrl;
    script.async = true;
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, [searchParams]);

  return null;
}
