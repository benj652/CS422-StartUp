document.addEventListener("DOMContentLoaded", () => {

  const overlay = document.createElement("div");
  overlay.id = "popup-overlay";

  overlay.innerHTML = `
    <div id="popup-modal">
      <span id="popup-close">&times;</span>
      <div id="popup-content"></div>
    </div>
  `;

  document.body.appendChild(overlay);

  const content = overlay.querySelector("#popup-content");
  const closeBtn = overlay.querySelector("#popup-close");

  document.querySelectorAll("[data-popup]").forEach(el => {

    el.addEventListener("click", () => {
      content.textContent = el.dataset.popup;
      overlay.style.display = "flex";
    });

  });

  closeBtn.addEventListener("click", () => {
    overlay.style.display = "none";
  });

  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) {
      overlay.style.display = "none";
    }
  });

});

document.querySelectorAll('.program-checker').forEach(checkbox => {
  const check_box = checkbox.parentElement.querySelector('.item-text').innerHTML;
  if (localStorage.getItem(check_box) === 'true') {
    checkbox.checked = true;
  }

  checkbox.addEventListener('change', function() {
        if (this.checked) {
          localStorage.setItem(check_box, 'true');
          console.log('Done!');
        } else {
          localStorage.setItem(check_box, 'false');
          console.log('Not done!');
        }
    });
});