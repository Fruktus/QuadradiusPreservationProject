const originalTitle = document.title;
window.onbeforeunload = function () {
  return "Are you sure you want to leave?";
};

document.addEventListener("visibilitychange", function () {
  if (document.hidden) {
    document.title = originalTitle + " (Paused)";
    alert(
      "Quadradius cannot work properly when the tab is in the background and has to be paused. " +
        "You WILL be timed out after some time when Quadradius is paused. " +
        "This is the current limitation of Ruffle.\n\n" +
        "If you want to run Quadradius in the background, " +
        "currently the best solution is to keep it open in a new window."
    );
  } else {
    document.title = originalTitle;
  }
});

// Load Ruffle
document.addEventListener("DOMContentLoaded", function () {
  let version = new URLSearchParams(window.location.search).get(
    "ruffle_version"
  );
  if (version) {
    version = "@" + version + "/ruffle.js";
  } else {
    version = "@0.1.0-nightly.2025.6.21/ruffle.js";
  }
  let ruffleScript = document.createElement("script");
  ruffleScript.setAttribute(
    "src",
    `https://unpkg.com/@ruffle-rs/ruffle${version}`
  );
  document.body.appendChild(ruffleScript);
});
