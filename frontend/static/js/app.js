(function () {
  "use strict";

  var data = JSON.parse(document.getElementById("page-data").textContent);
  var strings = data.strings;
  var REVIEWS_KEY = "fdp.reviews.v1";
  var BUBBLE_KEY = "fdp.ptBubbleClosed";

  function all(selector, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(selector));
  }

  function toast(message) {
    var host = document.getElementById("toasts");
    var el = document.createElement("div");
    el.className = "toast";
    el.textContent = message;
    host.appendChild(el);
    setTimeout(function () { el.remove(); }, 4000);
  }

  /* Intro screen: shown on a new visit or a reload, pulled up to reveal the system */
  var intro = document.getElementById("intro");
  if (document.documentElement.classList.contains("intro-open")) {
    var hiddenWhileIntro = all(".skip, .header, .shell, .toasts");
    var introReveal = document.getElementById("intro-reveal");
    var dragStart = null;
    var dragOffset = 0;
    var dragTime = 0;
    var revealing = false;

    var finishIntro = function () {
      document.documentElement.classList.remove("intro-open");
      hiddenWhileIntro.forEach(function (el) { el.inert = false; });
      document.removeEventListener("keydown", onIntroKey);
      document.getElementById("main").focus({ preventScroll: true });
    };

    var revealSystem = function () {
      if (revealing) { return; }
      revealing = true;
      try { sessionStorage.setItem("fdp.introSeen", "1"); } catch (e) { /* the intro simply returns next load */ }
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { finishIntro(); return; }
      intro.classList.remove("dragging");
      intro.style.transform = "translateY(-100%)";
      var finished = false;
      var finishOnce = function () { if (!finished) { finished = true; finishIntro(); } };
      intro.addEventListener("transitionend", finishOnce, { once: true });
      setTimeout(finishOnce, 900);
    };

    function onIntroKey(event) {
      if (["ArrowUp", "ArrowDown", "PageDown", "Escape", "Enter", " "].indexOf(event.key) !== -1) {
        event.preventDefault();
        revealSystem();
      }
    }

    hiddenWhileIntro.forEach(function (el) { el.inert = true; });
    intro.focus({ preventScroll: true });
    introReveal.addEventListener("click", revealSystem);
    document.addEventListener("keydown", onIntroKey);
    intro.addEventListener("wheel", function (event) {
      if (event.deltaY > 0) { revealSystem(); }
    }, { passive: true });

    intro.addEventListener("pointerdown", function (event) {
      if (revealing) { return; }
      dragStart = event.clientY;
      dragOffset = 0;
      dragTime = event.timeStamp;
      intro.setPointerCapture(event.pointerId);
      intro.classList.add("dragging");
    });
    intro.addEventListener("pointermove", function (event) {
      if (dragStart === null) { return; }
      dragOffset = Math.min(0, event.clientY - dragStart);
      intro.style.transform = "translateY(" + dragOffset + "px)";
    });
    var endDrag = function (event) {
      if (dragStart === null) { return; }
      var speed = -dragOffset / Math.max(1, event.timeStamp - dragTime);
      dragStart = null;
      intro.classList.remove("dragging");
      if (-dragOffset > window.innerHeight * 0.2 || (dragOffset < -24 && speed > 0.6)) {
        revealSystem();
      } else {
        intro.style.transform = "";
      }
    };
    intro.addEventListener("pointerup", endDrag);
    intro.addEventListener("pointercancel", endDrag);
  }

  /* Mobile navigation */
  var navToggle = document.getElementById("nav-toggle");
  var sidenav = document.getElementById("sidenav");
  navToggle.addEventListener("click", function () {
    var open = sidenav.classList.toggle("open");
    navToggle.setAttribute("aria-expanded", String(open));
  });
  function closeNav() {
    sidenav.classList.remove("open");
    navToggle.setAttribute("aria-expanded", "false");
  }
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && sidenav.classList.contains("open")) {
      closeNav();
      navToggle.focus();
    }
  });
  document.addEventListener("click", function (event) {
    if (sidenav.classList.contains("open") && !sidenav.contains(event.target) && !navToggle.contains(event.target)) {
      closeNav();
    }
  });

  /* Portuguese bubble: closing holds until a reload or a new visit */
  var bubble = document.getElementById("pt-bubble");
  if (bubble) {
    var closed = false;
    try {
      var nav = performance.getEntriesByType("navigation")[0];
      if (nav && nav.type === "reload") { sessionStorage.removeItem(BUBBLE_KEY); }
      closed = sessionStorage.getItem(BUBBLE_KEY) === "1";
    } catch (e) { closed = false; }
    bubble.hidden = closed;
    document.getElementById("pt-bubble-close").addEventListener("click", function () {
      bubble.hidden = true;
      try { sessionStorage.setItem(BUBBLE_KEY, "1"); } catch (e) { /* stays closed for this page only */ }
    });
  }

  /* Alert reviews live only in this browser */
  var memoryReviews = {};

  function loadReviews() {
    try {
      return JSON.parse(localStorage.getItem(REVIEWS_KEY)) || memoryReviews;
    } catch (e) {
      return memoryReviews;
    }
  }

  function saveReview(id, outcome) {
    var reviews = loadReviews();
    reviews[id] = outcome;
    memoryReviews = reviews;
    try {
      localStorage.setItem(REVIEWS_KEY, JSON.stringify(reviews));
      return true;
    } catch (e) {
      return false;
    }
  }

  function renderPendingCounts() {
    var reviews = loadReviews();
    var remaining = data.pendingIds.filter(function (id) { return !reviews[id]; }).length;
    all("[data-pending-count]").forEach(function (el) { el.textContent = remaining; });
    all(".sidenav .count").forEach(function (el) { el.hidden = remaining === 0; });
  }

  function renderLargestAlerts() {
    var list = document.getElementById("largest-alerts");
    if (!list) { return; }
    var reviews = loadReviews();
    var shown = 0;
    all("[data-alert-row]", list).forEach(function (row) {
      var visible = !reviews[row.dataset.id] && shown < 4;
      row.hidden = !visible;
      if (visible) { shown += 1; }
    });
    document.getElementById("largest-alerts-empty").hidden = shown > 0;
  }

  /* Alerts page */
  var alertRows = all("[data-alert]");
  var alertFilter = "all";

  function alertState(row, reviews) {
    return reviews[row.dataset.id] || (row.dataset.serverStatus === "reviewed" ? "reviewed" : "pending");
  }

  function renderAlerts() {
    if (!alertRows.length) { return; }
    var reviews = loadReviews();
    var counts = { all: alertRows.length, pending: 0, reviewed: 0 };
    var visible = 0;

    alertRows.forEach(function (row) {
      var state = alertState(row, reviews);
      var group = state === "pending" ? "pending" : "reviewed";
      counts[group] += 1;
      all("[data-state]", row).forEach(function (el) { el.hidden = el.dataset.state !== state; });
      row.querySelector("[data-review-actions]").hidden = state !== "pending";
      var show = alertFilter === "all" || alertFilter === group;
      row.hidden = !show;
      if (show) { visible += 1; }
    });

    all("[data-tab-count]").forEach(function (el) { el.textContent = "(" + counts[el.dataset.tabCount] + ")"; });
    document.getElementById("alerts-empty").hidden = visible > 0;
  }

  document.addEventListener("click", function (event) {
    var reviewBtn = event.target.closest("[data-review]");
    if (reviewBtn) {
      var row = reviewBtn.closest("[data-alert]");
      var saved = saveReview(row.dataset.id, reviewBtn.dataset.review);
      toast(saved ? strings.js_reviewed : strings.js_not_saved);
      renderAlerts();
      renderPendingCounts();
      return;
    }

    var copyBtn = event.target.closest("[data-copy]");
    if (copyBtn) {
      if (!navigator.clipboard) { toast(strings.js_copy_failed); return; }
      navigator.clipboard.writeText(copyBtn.dataset.copy).then(
        function () { toast(strings.js_copied); },
        function () { toast(strings.js_copy_failed); }
      );
      return;
    }

    var tab = event.target.closest("[data-filter]");
    if (tab) {
      alertFilter = tab.dataset.filter;
      all("[data-filter]").forEach(function (b) { b.setAttribute("aria-pressed", String(b === tab)); });
      renderAlerts();
      return;
    }

    var exportBtn = event.target.closest("[data-export]");
    if (exportBtn) { exportTable(exportBtn.dataset.export, exportBtn.dataset.filename); }
  });

  var resetBtn = document.getElementById("reset-demo");
  if (resetBtn) {
    resetBtn.addEventListener("click", function () {
      memoryReviews = {};
      try { localStorage.removeItem(REVIEWS_KEY); } catch (e) { /* memory state is already cleared */ }
      toast(strings.js_reset);
      renderAlerts();
      renderPendingCounts();
    });
  }

  /* Equipment filters */
  var eqTable = document.getElementById("equipment-table");
  if (eqTable) {
    var eqRows = all("tbody tr", eqTable);
    var eqCount = document.getElementById("equipment-count");
    var inputs = {
      q: document.getElementById("filter-q"),
      type: document.getElementById("filter-type"),
      line: document.getElementById("filter-line"),
      status: document.getElementById("filter-status"),
    };

    var filterEquipment = function () {
      var q = inputs.q.value.trim().toLowerCase();
      var shown = 0;
      eqRows.forEach(function (row) {
        var show = (!q || row.dataset.machine.indexOf(q) !== -1) &&
          (!inputs.type.value || row.dataset.type === inputs.type.value) &&
          (!inputs.line.value || row.dataset.line === inputs.line.value) &&
          (!inputs.status.value || row.dataset.status === inputs.status.value);
        row.hidden = !show;
        if (show) { shown += 1; }
      });
      eqCount.textContent = strings.showing.replace("{shown}", shown).replace("{total}", eqRows.length);
      document.getElementById("equipment-empty").hidden = shown > 0;
    };

    Object.keys(inputs).forEach(function (key) { inputs[key].addEventListener("input", filterEquipment); });
  }

  /* CSV export of the table the visitor sees */
  function csvCell(text, separator) {
    var value = text.replace(/\s+/g, " ").trim();
    if (/^[=+@\t\r]/.test(value) && !/^[+-]?\d/.test(value)) { value = "'" + value; }
    if (/^-/.test(value) && !/^-\d/.test(value)) { value = "'" + value; }
    if (value.indexOf('"') !== -1 || value.indexOf(separator) !== -1) {
      value = '"' + value.replace(/"/g, '""') + '"';
    }
    return value;
  }

  function exportTable(tableId, filename) {
    var table = document.getElementById(tableId);
    var separator = data.lang === "pt" ? ";" : ",";
    var lines = all("tr", table).filter(function (row) { return !row.hidden; }).map(function (row) {
      return all("th, td", row).map(function (cell) { return csvCell(cell.dataset.csv || cell.textContent, separator); }).join(separator);
    });
    var blob = new Blob(["﻿" + lines.join("\r\n")], { type: "text/csv;charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    toast(strings.js_exported);
  }

  renderPendingCounts();
  renderLargestAlerts();
  renderAlerts();
})();
