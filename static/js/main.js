// Small helpers used on every page
document.addEventListener("DOMContentLoaded", () => {
  // 1) Reveal elements when they scroll into view
  const items = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) { e.target.classList.add("visible"); io.unobserve(e.target); }
      });
    }, { threshold: 0.12 });
    items.forEach((el) => io.observe(el));
  } else {
    items.forEach((el) => el.classList.add("visible"));
  }

  // 2) Count-up numbers:  <span data-count="7">0</span>
  document.querySelectorAll("[data-count]").forEach((el) => {
    const target = parseFloat(el.dataset.count);
    const suffix = el.dataset.suffix || "";
    let n = 0;
    const stepSize = Math.max(target / 40, 1);
    const timer = setInterval(() => {
      n = Math.min(n + stepSize, target);
      el.textContent = Math.round(n) + suffix;
      if (n >= target) clearInterval(timer);
    }, 30);
  });

  // 3) Hero video: if the file is missing, hide the <video> so the poster background shows
  const vid = document.getElementById("hero-video");
  if (vid) {
    vid.addEventListener("error", () => vid.remove(), true);
    const src = vid.querySelector("source");
    if (src) src.addEventListener("error", () => vid.remove());
  }
});
