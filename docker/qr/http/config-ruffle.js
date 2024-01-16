window.RufflePlayer = window.RufflePlayer || {};
window.RufflePlayer.config = {
    autoplay: "on",
    contextMenu: "off",
    socketProxy: [
        {
            host: "127.0.0.1",
            port: 3000,
            proxyUrl: window.Quadradius.lobbyProxyUrl,
        },
        {
            host: "127.0.0.1",
            port: 3001,
            proxyUrl: window.Quadradius.gameProxyUrl,
        },
    ],
};
