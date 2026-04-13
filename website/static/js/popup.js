document.addEventListener("DOMContentLoaded", function () {
  var overlay = document.createElement("div");
  overlay.id = "popup-overlay";

  overlay.innerHTML =
    '<div id="popup-modal">' +
    '<span id="popup-close">&times;</span>' +
    '<div id="popup-content"></div>' +
    '</div>';

  document.body.appendChild(overlay);

  var content = overlay.querySelector("#popup-content");
  var closeBtn = overlay.querySelector("#popup-close");

  document.addEventListener("click", function (e) {
    var el = e.target.closest("[data-popup]");
    if (el && el.dataset.popup) {
      content.innerHTML = el.dataset.popup;
      overlay.style.display = "flex";
    }
  });

  closeBtn.addEventListener("click", function () {
    overlay.style.display = "none";
  });

  overlay.addEventListener("click", function (e) {
    if (e.target === overlay) {
      overlay.style.display = "none";
    }
  });
});