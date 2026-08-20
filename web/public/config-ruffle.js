let host = window.location.host;
let protocol = window.location.protocol == 'http:' ? 'ws:' : 'wss:';

window.RufflePlayer = window.RufflePlayer || {};
window.RufflePlayer.config = {
    autoplay: "on",
    contextMenu: "off",
    logLevel: "info",
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
    urlRewriteRules: [
        // [/^https?:\/\/(www\.)?quadradius\.com\/stuff\/quadradius\/tutorial\/tutorial\.html$/, ...], // Directions -> 99 sec starter video
        [/^https?:\/\/(www\.)?quadradius\.com\/quadradius\/directions\.html#rankings$/, "/directions.html#rankings"], // (Main) -> Ranking
        [/^https?:\/\/(www\.)?quadradius\.com\/quadradius\/directions\.html#memberships$/, "/directions.html#memberships"], // Members -> Learn More
        [/^https?:\/\/(www\.)?quadradius\.com\/quadradius\/directions\.html$/, "/directions.html"], // Directions -> Advanced training
        [/^https?:\/\/(www\.)?quadradius\.com\/quadradius\/paypal\/PayPalNotice(%20| )1(%20| )month\.html$/, "https://discord.gg/cVkV8pah4d"], // Members -> (Paid Plans)
        [/^https?:\/\/[^/]+\/about_quadradius\.html$/, "https://github.com/Fruktus/QuadradiusPreservationProject"], // About -> Read more about Quadradius
        // [/^https?:\/\/[^/]+\/about_jimmi_heiserman\.html$/, ...], // About -> Read more about Jimmi
        // [/^https?:\/\/[^/]+\/about_brad_kayal\.html$/, ...], // About -> Read more about Brad
        [/^https?:\/\/(www\.)?quadradius\.com\/quadradius\/PressAndReviews.*$/, "https://discord.gg/cVkV8pah4d"], // Press/Reviews
        [/^https?:\/\/(www\.)?quadradius\.com\/quadboard\/viewforum\.php\?f=9$/, "https://discord.gg/cVkV8pah4d"], // Fan Qreations
        [/^https?:\/\/(www\.)?quadradius\.com\/quadboard.*$/, "https://discord.gg/cVkV8pah4d"], // Quadboard
        // [/^aim:goim\?screenname=Quadradius$/, ...], // Contact -> AIM
        // [/^callto:\/\/quadradius\/?$/, ...], // Contact -> Skype
    ],
};
