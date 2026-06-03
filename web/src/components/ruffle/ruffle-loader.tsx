'use client';

import Script from 'next/script';
import { useSearchParams } from 'next/navigation';
import config from '@/configurations/config.json';

export default function RuffleLoader() {
  const searchParams = useSearchParams();

  const queryVersion = searchParams.get('ruffle_version');

  const version =
    queryVersion ??
    config.ruffleVersion ??
    '';

  const ruffleUrl = version
    ? `https://unpkg.com/@ruffle-rs/ruffle@${version}/ruffle.js`
    : 'https://unpkg.com/@ruffle-rs/ruffle';

  return (
    <Script
      src={ruffleUrl}
      strategy="afterInteractive"
    />
  );
}
