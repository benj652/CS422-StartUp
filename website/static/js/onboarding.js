const MESSAGES = [
  "Analyzing your profile…",
  "Mapping career paths…",
  "Curating courses & milestones…",
  "Almost ready…",
];

const form = document.querySelector("form");
const overlay = document.getElementById("obLoading");
const msgEl = document.getElementById("obLoadingMsg");
const barEl = document.getElementById("obLoadingBar");

let loading = false;

/**
 * Sends a POST request to the Flask backend to log an action
 */
function trackAction(actionType) {
  // Using fetch with keepalive ensures the request finishes even if the page begins unloading
  fetch("/track-action", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ atype: actionType }),
    keepalive: true 
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

  trackAction('roadmap_submit');

  overlay.classList.add("ob-loading--visible");
  overlay.setAttribute("aria-hidden", "false");

  const TOTAL = 2800;
  const step = TOTAL / MESSAGES.length;

  MESSAGES.forEach((msg, i) => {
    setTimeout(() => {
      msgEl.textContent = msg;
      barEl.style.width = ((i + 1) / MESSAGES.length) * 100 + "%";
    }, i * step);
  });

  // Final form submission after animation
  setTimeout(() => form.submit(), TOTAL + 200);
});