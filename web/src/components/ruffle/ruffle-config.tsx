'use client';

import { useEffect } from 'react';

export default function RuffleConfig() {
  useEffect(() => {
    const host = window.location.host;
    const protocol = window.location.protocol == 'http:' ? 'ws:' : 'wss:';

    window.RufflePlayer = window.RufflePlayer || {};
    window.RufflePlayer.config = {
        autoplay: "on",
        contextMenu: "off",
        logLevel: "debug",
        socketProxy: [
            {
                host: "127.0.0.1",
                port: 3000,
                proxyUrl: `${protocol}//${host}/websocket/lobby`,
            },
            {
                host: "127.0.0.1",
                port: 3001,
                proxyUrl: `${protocol}//${host}/websocket/game`,
            },
        ],
    };
  }, []);

  return null;
}
