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

form.addEventListener("submit", function (e) {
  if (loading) return;
  e.preventDefault();

  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  loading = true;
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

  setTimeout(() => form.submit(), TOTAL + 200);
});
