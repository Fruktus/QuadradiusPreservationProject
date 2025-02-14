let host = window.location.host;
let protocol = window.location.protocol == 'http:' ? 'ws:' : 'wss:';

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
    urlRewriteRules: [
        // // Rewrites to a relative URL
        // [/^https?:\/\/example.com\/(.*)\.swf$/, "$1.swf"],
        // // Rewrites to an absolute URL
        // [/^(.*)\.test\.swf$/, "$1.swf"],
        // // Rewrites using a string (exact match, not a regex)
        // ["http://old.example.com/site.html", "http://new.example.com/other_site.html"],

        // ["https://www.quadradius.com/stuff/quadradius/tutorial/tutorial.html", ...], // Directions -> 99 sec starter video
        ["https://www.quadradius.com/quadradius/directions.html", "/directions.html"], // Directions -> Advanced training
        // ["https://quadradius.com/quadradius/directions.html#rankings", ...], // (Main) -> Ranking
        // ["https://www.quadradius.com/quadradius/directions.html#memberships", ...], // Members -> Learn More
        // ["https://www.quadradius.com/quadradius/paypal/PayPalNotice%201%20month.html", ...] // Members -> (Paid Plans)
        // ["https://quadradius.ddns.net/about_quadradius.html", ...] // About -> Read more about Quadradius
        // ["https://quadradius.ddns.net/about_jimmi_heiserman.html", ...] // About -> Read more about Jimmi
        // ["https://quadradius.ddns.net/about_brad_kayal.html", ...] // About -> Read more about Brad
        // ["https://www.quadradius.com/quadradius/PressAndReviews", ...] // Press/Reviews
        // ["https://www.quadradius.com/quadboard/viewforum.php?f=9", ...] // Fan Qreations
        // ["https://www.quadradius.com/quadboard", ...] // Quadboard
        // ["aim:goim?screenname=Quadradius", ...] // Contact -> AIM
        // ["callto://quadradius/", ...] // Contact -> Skype
    ],
};
