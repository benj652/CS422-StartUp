(function () {
  var grid = document.getElementById("rmGrid");
  if (!grid) return;

  var started = Date.now();
  var hasReportedRoadmapTime = false;

  function postTrack(atype, detail) {
    var body = { atype: atype };

    if (detail != null) {
      body.detail = detail;
    }

    fetch("/track-action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).catch(function () {});
  }

  function reportRoadmapTime() {
    if (hasReportedRoadmapTime) return;

    hasReportedRoadmapTime = true;

    var sec = Math.min(7200, Math.round((Date.now() - started) / 1000));
    var payload = JSON.stringify({
      atype: "roadmap_time_on_page",
      detail: { seconds: sec },
    });

    if (navigator.sendBeacon) {
      navigator.sendBeacon(
        "/track-action",
        new Blob([payload], { type: "application/json" })
      );
    } else {
      fetch("/track-action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
        keepalive: true,
      }).catch(function () {});
    }
  }

  document.addEventListener(
    "change",
    function (e) {
      var t = e.target;

      if (!t || !t.classList) return;

      if (t.classList.contains("program-checker")) {
        var li = t.closest(".roadmap-node");
        if (!li || !grid.contains(li)) return;

        postTrack("roadmap_checkbox", {
          section: li.getAttribute("data-rm-section") || "",
          label: li.getAttribute("data-rm-label") || "",
          item_id: li.getAttribute("data-rm-id") || "",
          checked: !!t.checked,
        });
      }

      if (t.classList.contains("rm-status-select")) {
        var node = t.closest(".roadmap-node");
        if (!node || !grid.contains(node)) return;

        postTrack("roadmap_status_change", {
          section: node.getAttribute("data-rm-section") || "",
          label: node.getAttribute("data-rm-label") || "",
          item_id: node.getAttribute("data-rm-id") || "",
          status: t.value || "",
        });
      }
    },
    false
  );

  document.addEventListener(
    "click",
    function (e) {
      var a = e.target.closest && e.target.closest("a");

      if (!a || !a.href) return;
      if (!grid.contains(a)) return;

      var node = a.closest(".roadmap-node");

      postTrack("roadmap_link_click", {
        href: a.href,
        label: (a.textContent || "").trim(),
        item_label: node ? node.getAttribute("data-rm-label") || "" : "",
        section: node ? node.getAttribute("data-rm-section") || "" : "",
        item_id: node ? node.getAttribute("data-rm-id") || "" : "",
      });
    },
    true
  );

  document.addEventListener("visibilitychange", function () {
    if (document.hidden) reportRoadmapTime();
  });

  window.addEventListener("pagehide", reportRoadmapTime);
})();