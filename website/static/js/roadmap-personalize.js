(function () {
  const overlay = document.getElementById("rmLoading");
  const msgEl = document.getElementById("rmLoadingMsg");
  const grid = document.getElementById("rmGrid");

  if (!grid) return;

  const params = new URLSearchParams(window.location.search);

  const profile = {
    major: window.__RM_MAJOR || "cs",
    year: params.get("year") || "",
    career_goal: params.get("career_goal") || "",
    career_stage: params.get("career_stage") || "",
    priority: params.get("priority") || "",
  };

  const MESSAGES = [
    "Building your personalized roadmap…",
    "Reading your onboarding answers…",
    "Choosing the strongest next steps…",
    "Organizing your path…",
    "Almost ready…",
  ];

  const SECTION_LABELS = {
    classes: "class",
    programs: "program",
    internships: "internship",
    full_time_roles: "role",
    projects: "project",
    networking: "networking step",
    resources: "resource",
  };

  const STATUS_OPTIONS = {
    classes: ["Planning", "Taking Now", "Completed"],
    programs: ["Interested", "Applied", "Interviewing", "Accepted"],
    internships: ["Interested", "Applied", "Interviewing", "Accepted"],
    full_time_roles: ["Interested", "Applied", "Interviewing", "Accepted"],
    projects: ["Not Started", "In Progress", "Completed"],
    networking: ["Not Started", "In Progress", "Completed"],
    resources: ["Not Started", "In Progress", "Completed"],
    default: ["Not Started", "In Progress", "Completed"],
  };

  let msgIdx = 0;
  const msgTimer = setInterval(function () {
    msgIdx = (msgIdx + 1) % MESSAGES.length;
    if (msgEl) msgEl.textContent = MESSAGES[msgIdx];
  }, 1600);

  fetch("/roadmap/personalize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  })
    .then(function (res) {
      if (!res.ok) throw new Error("Roadmap request failed");
      return res.json();
    })
    .then(function (data) {
      render(data.sections || {});
    })
    .catch(function () {
      render({});
    })
    .finally(function () {
      clearInterval(msgTimer);
      hideOverlay();
    });

  function render(sections) {
    const cards = grid.querySelectorAll(".rm-card[data-section]");

    cards.forEach(function (card) {
      const key = card.getAttribute("data-section");
      const items = sections[key] || [];
      const ul = card.querySelector("ul");

      if (!ul) return;

      ul.innerHTML = "";

      if (!items.length) {
        card.classList.add("rm-card--empty");
        return;
      }

      card.classList.remove("rm-card--empty");

      items.forEach(function (item) {
        ul.appendChild(createRoadmapNode(item, key));
      });
    });

    renumberCards();
  }

  function createRoadmapNode(item, sectionKey) {
    const li = document.createElement("li");
    li.className = "roadmap-node";

    const itemId = getItemId(item, sectionKey);
    const label = item.text || "Recommendation";

    li.setAttribute("data-rm-section", sectionKey);
    li.setAttribute("data-rm-label", label);
    li.setAttribute("data-rm-id", itemId);

    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.className = "program-checker";
    cb.setAttribute("aria-label", "Mark complete: " + label);

    const checkboxKey = storageKey("complete", itemId);
    cb.checked = localStorage.getItem(checkboxKey) === "true";

    cb.addEventListener("change", function () {
      localStorage.setItem(checkboxKey, cb.checked ? "true" : "false");
    });

    li.appendChild(cb);

    const main = document.createElement("div");
    main.className = "roadmap-node-main";

    const titleRow = document.createElement("div");
    titleRow.className = "item-title-row";

    const titleWrap = document.createElement("div");

    if (item.href) {
      const titleLink = document.createElement("a");
      titleLink.href = item.href;
      titleLink.target = "_blank";
      titleLink.rel = "noopener noreferrer";
      titleLink.textContent = label;
      titleLink.className = "item-title-link";
      titleWrap.appendChild(titleLink);
    } else {
      const title = document.createElement("span");
      title.textContent = label;
      title.className = "item-title";
      titleWrap.appendChild(title);
    }

    titleRow.appendChild(titleWrap);

    if (item.href) {
      const external = document.createElement("a");
      external.href = item.href;
      external.target = "_blank";
      external.rel = "noopener noreferrer";
      external.className = "external-pill";
      external.textContent = openLabel(sectionKey);
      external.setAttribute("aria-label", "Open " + label);
      titleRow.appendChild(external);
    }

    main.appendChild(titleRow);

    if (item.summary) {
      const meta = document.createElement("span");
      meta.className = "item-meta";
      meta.textContent = item.summary;
      main.appendChild(meta);
    } else if (item.popupText) {
      const meta = document.createElement("span");
      meta.className = "item-meta";
      meta.textContent = truncate(item.popupText, 116);
      main.appendChild(meta);
    }

    const actions = document.createElement("div");
    actions.className = "item-actions";

    const statusLabel = document.createElement("span");
    statusLabel.className = "status-label";
    statusLabel.textContent = "Status";
    actions.appendChild(statusLabel);

    const select = document.createElement("select");
    select.className = "rm-status-select";
    select.setAttribute("aria-label", "Status for " + label);

    const options = STATUS_OPTIONS[sectionKey] || STATUS_OPTIONS.default;
    options.forEach(function (optionLabel) {
      const opt = document.createElement("option");
      opt.value = optionLabel;
      opt.textContent = optionLabel;
      select.appendChild(opt);
    });

    const statusKey = storageKey("status", itemId);
    const savedStatus = localStorage.getItem(statusKey);

    if (savedStatus && options.indexOf(savedStatus) !== -1) {
      select.value = savedStatus;
    }

    select.addEventListener("change", function () {
      localStorage.setItem(statusKey, select.value);
    });

    actions.appendChild(select);
    main.appendChild(actions);

    const speech = createSpeechBubble(item, sectionKey);
    if (speech) main.appendChild(speech);

    li.appendChild(main);

    return li;
  }

  function createSpeechBubble(item, sectionKey) {
    if (!item.popupText && !item.whyRecommended) return null;

    const bubble = document.createElement("div");
    bubble.className = "rm-speech";

    if (item.popupText) {
      const about = document.createElement("div");
      about.className = "rm-speech-section";

      const strong = document.createElement("strong");
      strong.textContent = "What this is";

      const p = document.createElement("p");
      p.textContent = item.popupText;

      about.appendChild(strong);
      about.appendChild(p);
      bubble.appendChild(about);
    }

    if (item.whyRecommended) {
      const why = document.createElement("div");
      why.className = "rm-speech-section";

      const strong = document.createElement("strong");
      strong.textContent = "Why it matters";

      const p = document.createElement("p");
      p.textContent = item.whyRecommended;

      why.appendChild(strong);
      why.appendChild(p);
      bubble.appendChild(why);
    } else {
      const fallback = document.createElement("div");
      fallback.className = "rm-speech-section";

      const strong = document.createElement("strong");
      strong.textContent = "Why it matters";

      const p = document.createElement("p");
      p.textContent =
        "This " +
        (SECTION_LABELS[sectionKey] || "step") +
        " was included because it fits your current roadmap stage.";

      fallback.appendChild(strong);
      fallback.appendChild(p);
      bubble.appendChild(fallback);
    }

    return bubble;
  }

  function renumberCards() {
    const visible = grid.querySelectorAll(
      ".rm-card[data-section]:not(.rm-card--empty)"
    );

    let n = 1;

    visible.forEach(function (card) {
      const num = card.querySelector(".rm-stage-number");
      if (num) {
        num.textContent = n < 10 ? "0" + n : String(n);
        n += 1;
      }
    });
  }

  function hideOverlay() {
    if (!overlay) return;

    overlay.classList.add("rm-loading--hidden");

    setTimeout(function () {
      overlay.style.display = "none";
    }, 400);
  }

  function getItemId(item, sectionKey) {
    if (item.id) return item.id;

    const raw = [
      profile.major,
      profile.year,
      profile.career_goal,
      profile.career_stage,
      profile.priority,
      sectionKey,
      item.text || "item",
    ].join("|");

    return slugify(raw);
  }

  function storageKey(type, itemId) {
    return "blueprint:" + type + ":" + itemId;
  }

  function slugify(value) {
    return String(value)
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  }

  function truncate(value, maxLen) {
    const text = String(value || "");
    if (text.length <= maxLen) return text;

    const trimmed = text.slice(0, maxLen);
    const lastSpace = trimmed.lastIndexOf(" ");

    if (lastSpace > 60) {
      return trimmed.slice(0, lastSpace).replace(/[.,;:!?-]+$/, "") + "…";
    }

    return trimmed.replace(/[.,;:!?-]+$/, "") + "…";
  }

  function openLabel(sectionKey) {
    if (sectionKey === "classes") return "View course";
    if (sectionKey === "internships") return "Open role";
    if (sectionKey === "full_time_roles") return "Open role";
    if (sectionKey === "programs") return "Open";
    if (sectionKey === "projects") return "View project";
    if (sectionKey === "resources") return "Open resource";
    return "Open";
  }
})();