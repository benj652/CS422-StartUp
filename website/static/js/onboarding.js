const form = document.querySelector("form");
const overlay = document.getElementById("obLoading");
const msgEl = document.getElementById("obLoadingMsg");

let loading = false;

function trackAction(actionType) {
  fetch("/track-action", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ atype: actionType }),
    keepalive: true,
  });
}

form.addEventListener("submit", function (e) {
  if (loading) return;
  e.preventDefault();

  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  loading = true;
  trackAction("roadmap_submit");

  if (msgEl) msgEl.textContent = "Building your roadmap…";
  overlay.classList.add("ob-loading--visible");
  overlay.setAttribute("aria-hidden", "false");

  form.submit();
});