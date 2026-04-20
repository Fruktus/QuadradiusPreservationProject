const originalTitle = document.title;
window.onbeforeunload = function () {
  return "Are you sure you want to leave?";
};

// Load Ruffle
document.addEventListener("DOMContentLoaded", function () {
  let version = new URLSearchParams(window.location.search).get(
    "ruffle_version"
  );
  if (version) {
    version = "@" + version + "/ruffle.js";
  } else {
    version = "@0.2.0-nightly.2026.4.21/ruffle.js";
  }
  let ruffleScript = document.createElement("script");
  ruffleScript.setAttribute(
    "src",
    `https://unpkg.com/@ruffle-rs/ruffle${version}`
  );
  document.body.appendChild(ruffleScript);
});
