const form = document.querySelector("form");
const overlay = document.getElementById("obLoading");
const msgEl = document.getElementById("obLoadingMsg");

let loading = false;
let suppressCareerGoalHandler = false;

const ALIGNMENT_MAP = {
  cs: new Set(["software_engineer", "data_science", "product_manager", "exploring"]),
  econ: new Set(["finance", "consulting", "data_science", "exploring"]),
};

const MAJOR_LABELS = {
  cs: "Computer Science",
  econ: "Economics",
};

const CAREER_LABELS = {
  software_engineer: "Software Engineer",
  data_science: "Data Scientist / Analyst",
  product_manager: "Product Manager",
  finance: "Finance / Banking",
  consulting: "Consulting",
  exploring: "Still Exploring",
};

function trackAction(actionType) {
  fetch("/track-action", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ atype: actionType }),
    keepalive: true,
  });
}

function getSelectedValue(name) {
  const checked = form.querySelector(`input[name="${name}"]:checked`);
  return checked ? checked.value : "";
}

function isMismatch(major, careerGoal) {
  if (!major || !careerGoal) return false;
  const allowed = ALIGNMENT_MAP[major];
  if (!allowed) return false;
  return !allowed.has(careerGoal);
}

function ensureMismatchModal() {
  let overlayEl = document.getElementById("obMismatchOverlay");
  if (overlayEl) return overlayEl;

  overlayEl = document.createElement("div");
  overlayEl.id = "obMismatchOverlay";
  overlayEl.innerHTML = `
    <div id="obMismatchModal" role="dialog" aria-modal="true" aria-labelledby="obMismatchTitle">
      <button type="button" id="obMismatchClose" aria-label="Close warning">&times;</button>
      <p class="ob-mismatch-eyebrow">Major mismatch</p>
      <h2 id="obMismatchTitle">This path may not align with your selected major.</h2>
      <p id="obMismatchBody">
        You may want to consider switching majors or adjusting your career path selection.
      </p>
      <div class="ob-mismatch-actions">
        <button type="button" id="obMismatchBack" class="ob-mismatch-secondary">Go back</button>
        <button type="button" id="obMismatchKeep" class="ob-mismatch-primary">Keep this path</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlayEl);

  Object.assign(overlayEl.style, {
    position: "fixed",
    inset: "0",
    background: "rgba(15, 23, 42, 0.45)",
    display: "none",
    alignItems: "center",
    justifyContent: "center",
    padding: "24px",
    zIndex: "10000",
  });

  const modal = overlayEl.querySelector("#obMismatchModal");
  Object.assign(modal.style, {
    position: "relative",
    width: "min(560px, 100%)",
    background: "#ffffff",
    border: "1px solid #e2ded6",
    borderRadius: "14px",
    padding: "28px 28px 24px",
    boxShadow: "0 24px 60px rgba(15, 23, 42, 0.18)",
    fontFamily: '"Inter", sans-serif',
    color: "#0f172a",
  });

  const closeBtn = overlayEl.querySelector("#obMismatchClose");
  Object.assign(closeBtn.style, {
    position: "absolute",
    top: "10px",
    right: "14px",
    border: "none",
    background: "transparent",
    fontSize: "28px",
    fontWeight: "700",
    lineHeight: "1",
    cursor: "pointer",
    color: "#64748b",
  });

  const eyebrow = overlayEl.querySelector(".ob-mismatch-eyebrow");
  Object.assign(eyebrow.style, {
    fontSize: "0.75rem",
    fontWeight: "700",
    letterSpacing: "0.1em",
    textTransform: "uppercase",
    color: "#127be4",
    marginBottom: "10px",
  });

  const title = overlayEl.querySelector("#obMismatchTitle");
  Object.assign(title.style, {
    fontFamily: '"Poppins", sans-serif',
    fontWeight: "800",
    fontSize: "1.5rem",
    lineHeight: "1.15",
    letterSpacing: "-0.03em",
    marginBottom: "12px",
  });

  const body = overlayEl.querySelector("#obMismatchBody");
  Object.assign(body.style, {
    fontSize: "0.98rem",
    lineHeight: "1.7",
    color: "#475569",
    marginBottom: "22px",
  });

  const actions = overlayEl.querySelector(".ob-mismatch-actions");
  Object.assign(actions.style, {
    display: "flex",
    gap: "12px",
    justifyContent: "flex-end",
    flexWrap: "wrap",
  });

  const backBtn = overlayEl.querySelector("#obMismatchBack");
  Object.assign(backBtn.style, {
    border: "1.5px solid #e2ded6",
    background: "#fff",
    color: "#475569",
    borderRadius: "8px",
    padding: "11px 18px",
    fontSize: "0.95rem",
    fontWeight: "600",
    cursor: "pointer",
  });

  const keepBtn = overlayEl.querySelector("#obMismatchKeep");
  Object.assign(keepBtn.style, {
    border: "none",
    background: "#127be4",
    color: "#fff",
    borderRadius: "8px",
    padding: "12px 18px",
    fontSize: "0.95rem",
    fontWeight: "600",
    cursor: "pointer",
  });

  return overlayEl;
}

function showMismatchModal(major, careerGoal, onKeep, onBack) {
  const overlayEl = ensureMismatchModal();
  const body = overlayEl.querySelector("#obMismatchBody");
  const closeBtn = overlayEl.querySelector("#obMismatchClose");
  const backBtn = overlayEl.querySelector("#obMismatchBack");
  const keepBtn = overlayEl.querySelector("#obMismatchKeep");

  const majorLabel = MAJOR_LABELS[major] || "this major";
  const careerLabel = CAREER_LABELS[careerGoal] || "this path";

  body.textContent =
    `${careerLabel} does not usually align with a ${majorLabel} roadmap in this app. ` +
    `You may want to consider switching majors if this is the path you want to pursue.`;

  overlayEl.style.display = "flex";

  function cleanup() {
    overlayEl.style.display = "none";
    closeBtn.onclick = null;
    backBtn.onclick = null;
    keepBtn.onclick = null;
    overlayEl.onclick = null;
  }

  closeBtn.onclick = function () {
    cleanup();
    onBack();
  };

  backBtn.onclick = function () {
    cleanup();
    onBack();
  };

  keepBtn.onclick = function () {
    cleanup();
    onKeep();
  };

  overlayEl.onclick = function (e) {
    if (e.target === overlayEl) {
      cleanup();
      onBack();
    }
  };
}

function handleCareerGoalSelection(radio) {
  if (suppressCareerGoalHandler) return;

  const major = getSelectedValue("major");
  const careerGoal = radio.value;

  if (!major || !careerGoal || !isMismatch(major, careerGoal)) {
    return;
  }

  showMismatchModal(
    major,
    careerGoal,
    function () {
      trackAction("major_career_mismatch_keep");
    },
    function () {
      suppressCareerGoalHandler = true;
      radio.checked = false;
      suppressCareerGoalHandler = false;
      trackAction("major_career_mismatch_back");
    }
  );
}

const careerGoalInputs = form.querySelectorAll('input[name="career_goal"]');
careerGoalInputs.forEach(function (radio) {
  radio.addEventListener("change", function () {
    handleCareerGoalSelection(radio);
  });
});

form.addEventListener("submit", function (e) {
  if (loading) return;
  e.preventDefault();

  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  const major = getSelectedValue("major");
  const careerGoal = getSelectedValue("career_goal");

  if (isMismatch(major, careerGoal)) {
    showMismatchModal(
      major,
      careerGoal,
      function () {
        if (loading) return;
        loading = true;
        trackAction("roadmap_submit");
        trackAction("major_career_mismatch_keep");
        if (msgEl) msgEl.textContent = "Building your roadmap…";
        overlay.classList.add("ob-loading--visible");
        overlay.setAttribute("aria-hidden", "false");
        form.submit();
      },
      function () {
        trackAction("major_career_mismatch_back");
      }
    );
    return;
  }

  loading = true;
  trackAction("roadmap_submit");

  if (msgEl) msgEl.textContent = "Building your roadmap…";
  overlay.classList.add("ob-loading--visible");
  overlay.setAttribute("aria-hidden", "false");

  form.submit();
});