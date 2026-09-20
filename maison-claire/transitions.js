/* Maison Claire - page-transition fallback for browsers without cross-document
   View Transitions. Chromium handles it entirely in CSS, so this exits early
   there. The <head> primer sets html.pt-enter before first paint (no flicker);
   here we release it into a fade, and fade out again on internal navigation. */
(function () {
  var root = document.documentElement;
  if (!document.body.classList.contains('motion')) { root.classList.remove('pt-enter'); return; }
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    root.classList.remove('pt-enter');
    return;
  }
  if ('CSSViewTransitionRule' in window) { root.classList.remove('pt-enter'); return; }

  // Release the primed fade-in. pt-enter-active is left in place: it only
  // pins opacity to 1, and removing it can leave the transition mid-flight.
  root.classList.remove('pt-enter');
  root.classList.add('pt-enter-active');

  // Dissolve out before following an internal link.
  document.addEventListener('click', function (e) {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (!a || a.target === '_blank' || a.hasAttribute('download')) return;
    var href = a.getAttribute('href') || '';
    if (/^(mailto:|tel:|#)/i.test(href)) return;
    var url;
    try { url = new URL(a.href, location.href); } catch (err) { return; }
    if (url.origin !== location.origin) return;
    if (url.pathname === location.pathname) return;   // same page or in-page anchor
    e.preventDefault();
    root.classList.add('pt-leave');
    setTimeout(function () { window.location.href = a.href; }, 240);
  });
})();
