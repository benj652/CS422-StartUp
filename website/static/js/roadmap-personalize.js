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
    "Analyzing your profile…",
    "Selecting recommendations…",
    "Almost ready…",
  ];

  let msgIdx = 0;
  const msgTimer = setInterval(function () {
    msgIdx = (msgIdx + 1) % MESSAGES.length;
    if (msgEl) msgEl.textContent = MESSAGES[msgIdx];
  }, 1800);

  fetch("/roadmap/personalize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  })
    .then(function (res) {
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
    var cards = grid.querySelectorAll(".rm-card[data-section]");
    cards.forEach(function (card) {
      var key = card.getAttribute("data-section");
      var items = sections[key] || [];
      var ul = card.querySelector("ul");
      if (!ul) return;

      ul.innerHTML = "";

      if (items.length === 0) {
        card.classList.add("rm-card--empty");
        return;
      }
      card.classList.remove("rm-card--empty");

      items.forEach(function (item) {
        var li = document.createElement("li");
        var isSpecialSection = (key === "internships" || key === "programs");

        var cb = document.createElement("input");
        cb.type = "checkbox";
        cb.className = "program-checker";
        li.appendChild(cb);

        var contentWrap = document.createElement("div");
        contentWrap.className = isSpecialSection ? "item-spreadsheet-wrapper" : "item-text";

        if (isSpecialSection) {
          contentWrap.innerHTML = `
            <div class="ss-header" onclick="this.parentElement.classList.toggle('is-open')">
              <span class="ss-title">${item.text}</span>
              
              <select class="ss-status-select" onclick="event.stopPropagation()" data-item="${item.text}">
                <option value="not-applied">Not Applied</option>
                <option value="applied">Interviewing</option>
                <option value="interviewing"> Applied</option>
              </select>

              <span class="ss-arrow">▼</span>
            </div>
            <div class="ss-details">
              <div class="ss-details-inner">
                <p><strong>About:</strong> ${item.popupText || 'No details provided.'}</p>
                <p><strong>Why Recommended:</strong> ${item.whyRecommended || 'Fits your profile.'}</p>
                ${item.href ? `<a href="${item.href}" target="_blank" class="ss-link">View Opportunity</a>` : ''}
              </div>
            </div>
          `;
        } else {
          var mainEl = item.href ? document.createElement("a") : document.createElement("span");
          if (item.href) { mainEl.href = item.href; mainEl.target = "_blank"; }
          mainEl.textContent = item.text;
          mainEl.className = "item-title";
          contentWrap.appendChild(mainEl);

          if (item.summary) {
            var meta = document.createElement("span");
            meta.className = "item-meta";
            meta.textContent = item.summary;
            contentWrap.appendChild(meta);
          }
        }

        li.appendChild(contentWrap);

        if (!isSpecialSection && (item.popupText || item.whyRecommended)) {
            var info = document.createElement("button");
            info.className = "info-btn";
            li.appendChild(info);
        }

        li.setAttribute("data-rm-section", key);
        ul.appendChild(li);

        var storageKey = item.text;
        if (localStorage.getItem(storageKey) === "true") cb.checked = true;
        cb.addEventListener("change", function () {
          localStorage.setItem(storageKey, cb.checked ? "true" : "false");
        });
      });
    });

    renumberCards();
  }

  function renumberCards() {
    var visible = grid.querySelectorAll(
      ".rm-card[data-section]:not(.rm-card--empty)"
    );
    var n = 1;
    visible.forEach(function (card) {
      var eyebrow = card.querySelector(".rm-card-eyebrow");
      if (eyebrow) {
        eyebrow.textContent = n < 10 ? "0" + n : "" + n;
        n++;
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
})();