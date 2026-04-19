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

        var cb = document.createElement("input");
        cb.type = "checkbox";
        cb.className = "program-checker";
        li.appendChild(cb);

        var textWrap = document.createElement("div");
        textWrap.className = "item-text";

        var mainEl;
        if (item.href) {
          mainEl = document.createElement("a");
          mainEl.href = item.href;
          mainEl.target = "_blank";
          mainEl.rel = "noopener noreferrer";
          mainEl.textContent = item.text;
        } else {
          mainEl = document.createElement("span");
          mainEl.textContent = item.text;
        }

        mainEl.className = "item-title";
        textWrap.appendChild(mainEl);

        if (item.summary) {
          var meta = document.createElement("span");
          meta.className = "item-meta";
          meta.textContent = item.summary;
          textWrap.appendChild(meta);
        }

        li.appendChild(textWrap);

        if (item.popupText || item.whyRecommended) {
          var info = document.createElement("button");
          info.type = "button";
          info.className = "info-btn";

          var popupParts = [];

          if (item.popupText) {
            popupParts.push(
              "<div class='popup-section'><strong>About this recommendation</strong><p>" +
                item.popupText +
                "</p></div>"
            );
          }

          if (item.whyRecommended) {
            popupParts.push(
              "<div class='popup-section'><strong>Why it fits your roadmap</strong><p>" +
                item.whyRecommended +
                "</p></div>"
            );
          }

          info.setAttribute("data-popup", popupParts.join(""));
          info.setAttribute("aria-label", "More info about " + item.text);
          info.innerHTML =
            '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/><path d="M8 7v4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><circle cx="8" cy="5" r="0.75" fill="currentColor"/></svg>';
          li.appendChild(info);
        } else {
          var spacer = document.createElement("span");
          li.appendChild(spacer);
        }

        li.setAttribute("data-rm-section", key);
        li.setAttribute("data-rm-label", item.text || "");

        ul.appendChild(li);

        var storageKey = item.text;
        if (localStorage.getItem(storageKey) === "true") {
          cb.checked = true;
        }
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