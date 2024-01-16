let hostname = window.location.hostname;
let protocol = window.location.protocol == 'http:' ? 'ws:' : 'wss:';

window.Quadradius = window.Quadradius || {};
window.Quadradius.lobbyProxyUrl = `${protocol}//${hostname}:8100`;
window.Quadradius.gameProxyUrl = `${protocol}//${hostname}:8101`;
