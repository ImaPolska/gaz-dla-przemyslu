/* Presentation only: sticky shrink for the existing free Blocksy header. */
(() => {
  const update = () => document.documentElement.classList.toggle('gdp-scrolled', window.scrollY > 48);
  window.addEventListener('scroll', update, { passive: true });
  update();
})();
