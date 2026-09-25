/* RSA-SHIELD Presentation Controller */

(function () {
  const slides = Array.from(document.querySelectorAll(".slide"));
  const total = slides.length;
  let current = 0;
  let mermaidReady = false;

  const counter = document.getElementById("counter");
  const progress = document.getElementById("progress");
  const prevBtn = document.getElementById("prev");
  const nextBtn = document.getElementById("next");

  mermaid.initialize({
    startOnLoad: false,
    theme: "dark",
    securityLevel: "loose",
    fontFamily: "Sora, Segoe UI, sans-serif",
    themeVariables: {
      darkMode: true,
      background: "#11151d",
      primaryColor: "#11151d",
      primaryTextColor: "#e8eef7",
      primaryBorderColor: "#22d3ee",
      secondaryColor: "#151922",
      secondaryTextColor: "#e8eef7",
      secondaryBorderColor: "#a78bfa",
      tertiaryColor: "#0d1118",
      tertiaryTextColor: "#94a3b8",
      tertiaryBorderColor: "#64748b",
      lineColor: "#64748b",
      textColor: "#e8eef7",
      mainBkg: "#11151d",
      nodeBorder: "#22d3ee",
      clusterBkg: "#0d1118",
      titleColor: "#e8eef7",
      edgeLabelBackground: "#0b0e14",
      fontSize: "14px",
    },
    flowchart: {
      curve: "basis",
      padding: 12,
      htmlLabels: true,
      nodeSpacing: 28,
      rankSpacing: 36,
    },
  });

  function pad(n) {
    return String(n).padStart(2, "0");
  }

  function updateChrome() {
    counter.textContent = `${pad(current + 1)} / ${pad(total)}`;
    progress.style.width = `${((current + 1) / total) * 100}%`;
    prevBtn.disabled = current === 0;
    nextBtn.disabled = current === total - 1;
  }

  async function renderMermaidIn(slide) {
    const nodes = slide.querySelectorAll(".mermaid:not([data-processed])");
    if (!nodes.length) return;
    try {
      await mermaid.run({ nodes });
      nodes.forEach((n) => n.setAttribute("data-processed", "true"));
    } catch (err) {
      console.warn("Mermaid render error:", err);
    }
  }

  async function show(index) {
    if (index < 0 || index >= total) return;
    slides.forEach((s, i) => s.classList.toggle("active", i === index));
    current = index;
    updateChrome();
    await renderMermaidIn(slides[current]);
  }

  function next() {
    show(current + 1);
  }

  function prev() {
    show(current - 1);
  }

  prevBtn.addEventListener("click", prev);
  nextBtn.addEventListener("click", next);

  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") {
      e.preventDefault();
      next();
    } else if (e.key === "ArrowLeft" || e.key === "PageUp") {
      e.preventDefault();
      prev();
    } else if (e.key === "Home") {
      e.preventDefault();
      show(0);
    } else if (e.key === "End") {
      e.preventDefault();
      show(total - 1);
    }
  });

  // Touch swipe
  let touchX = null;
  document.addEventListener(
    "touchstart",
    (e) => {
      touchX = e.changedTouches[0].screenX;
    },
    { passive: true }
  );
  document.addEventListener(
    "touchend",
    (e) => {
      if (touchX === null) return;
      const dx = e.changedTouches[0].screenX - touchX;
      if (Math.abs(dx) > 50) {
        if (dx < 0) next();
        else prev();
      }
      touchX = null;
    },
    { passive: true }
  );

  // Pre-render first slide; lazy-render others on visit for speed
  show(0).then(() => {
    mermaidReady = true;
  });
})();
