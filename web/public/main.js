const originalTitle = document.title;
window.onbeforeunload = function () {
  return "Are you sure you want to leave?";
};
