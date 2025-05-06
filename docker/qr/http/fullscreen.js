document.addEventListener("DOMContentLoaded", function () {
  document
    .getElementById("fullscreen-toggle")
    .addEventListener("click", function () {
      if (!document.fullscreenElement) {
        // Enter fullscreen
        if (document.documentElement.requestFullscreen) {
          document.documentElement.requestFullscreen();
        } else if (document.documentElement.webkitRequestFullscreen) {
          document.documentElement.webkitRequestFullscreen();
        } else if (document.documentElement.msRequestFullscreen) {
          document.documentElement.msRequestFullscreen();
        }
        document.getElementById("fullscreen-open").style.display = "none";
        document.getElementById("fullscreen-close").style.display = "block";
      } else {
        // Exit fullscreen
        if (document.exitFullscreen) {
          document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
          document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
          document.msExitFullscreen();
        }
        document.getElementById("fullscreen-open").style.display = "block";
        document.getElementById("fullscreen-close").style.display = "none";
      }
    });

  // Initialize the correct icon state
  document.getElementById("fullscreen-close").style.display = "none";

  // Update icon when fullscreen state changes
  document.addEventListener("fullscreenchange", function () {
    if (document.fullscreenElement) {
      document.getElementById("fullscreen-open").style.display = "none";
      document.getElementById("fullscreen-close").style.display = "block";
    } else {
      document.getElementById("fullscreen-open").style.display = "block";
      document.getElementById("fullscreen-close").style.display = "none";
    }
  });
});
