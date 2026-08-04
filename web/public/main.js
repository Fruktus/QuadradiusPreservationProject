const originalTitle = document.title;
window.onbeforeunload = function () {
  return "Are you sure you want to leave?";
};

// Load Ruffle
let version = new URLSearchParams(window.location.search).get(
  "ruffle_version"
);
if (version) {
  version = "@" + version + "/ruffle.js";
} else {
  version = "@0.5.0/ruffle.js";
}
let ruffleScript = document.createElement("script");
ruffleScript.setAttribute(
  "src",
  `https://unpkg.com/@ruffle-rs/ruffle${version}`
);
document.body.appendChild(ruffleScript);
