// Small enhancements. Every page works without this file; it only adds
// the mobile menu, live "Upcoming" badges and the presentation filters.
(() => {
  // Mobile menu
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
  }

  // "Upcoming" is decided in the browser, so a meeting stops being upcoming the
  // day after it ends even if the site hasn't been rebuilt since.
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const parseDate = (s) => {
    const [y, m, d] = s.split("-").map(Number);
    return new Date(y, m - 1, d);
  };
  document.querySelectorAll("[data-end]").forEach((el) => {
    el.classList.toggle("is-upcoming", parseDate(el.dataset.end) >= today);
  });

  // Presentation filters (?show=poster etc. can be shared as a link)
  const bar = document.querySelector("[data-filter-bar]");
  if (!bar) return;
  const talks = [...document.querySelectorAll("[data-talk]")];
  const events = [...document.querySelectorAll("[data-event]")];
  const years = [...document.querySelectorAll("[data-year]")];
  const empty = document.querySelector("[data-filter-empty]");
  const tests = {
    all: () => true,
    "has-poster": (t) => t.dataset.hasPoster === "true",
    coauthor: (t) => t.dataset.coauthor === "true",
  };
  const matches = (key, talk) => (tests[key] ? tests[key](talk) : talk.dataset.type === key);

  function apply(key) {
    let shown = 0;
    talks.forEach((t) => {
      t.hidden = !matches(key, t);
      if (!t.hidden) shown++;
    });
    events.forEach((e) => (e.hidden = !e.querySelector("[data-talk]:not([hidden])")));
    years.forEach((y) => (y.hidden = !y.querySelector("[data-event]:not([hidden])")));
    if (empty) empty.hidden = shown > 0;
    bar.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.filter === key)));
    const url = new URL(location.href);
    if (key === "all") url.searchParams.delete("show");
    else url.searchParams.set("show", key);
    history.replaceState(null, "", url);
  }

  bar.hidden = false;
  bar.addEventListener("click", (e) => {
    const button = e.target.closest("button[data-filter]");
    if (button) apply(button.dataset.filter);
  });
  const initial = new URLSearchParams(location.search).get("show");
  if (initial && bar.querySelector(`[data-filter="${CSS.escape(initial)}"]`)) apply(initial);
})();
