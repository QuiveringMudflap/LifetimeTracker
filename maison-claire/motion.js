/* Maison Claire - subtle scroll-reveal. Gated by body.motion (MOTION flag in
   build.py) and disabled for prefers-reduced-motion. Progressive enhancement:
   if anything here fails, all content stays fully visible. */
(function () {
  if (!document.body.classList.contains('motion')) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (!('IntersectionObserver' in window)) return;

  var SELECTORS = [
    '.intro-lede > *',
    '.section-head',
    '.prompt',
    '.feature-card',
    '.split-approach > div',
    '.split-about > div',
    '.journey-row',
    '.modality',
    '.gallery3 img',
    '.contact-card',
    '.band-line',
    '.testimonial',
    '.form-section',
    '.about-photo'
  ];

  var seen = [];
  SELECTORS.forEach(function (sel) {
    var list = document.querySelectorAll(sel);
    for (var i = 0; i < list.length; i++) if (seen.indexOf(list[i]) === -1) seen.push(list[i]);
  });

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('revealed'); observer.unobserve(e.target); }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });

  var vh = window.innerHeight || document.documentElement.clientHeight;
  seen.forEach(function (el) {
    // Leave anything already in view untouched (no flash); only animate what's below.
    var top = el.getBoundingClientRect().top;
    if (top < vh * 0.9) return;
    var parent = el.parentNode;
    var idx = parent ? Array.prototype.indexOf.call(parent.children, el) : 0;
    el.style.transitionDelay = (Math.min(idx, 6) * 0.07).toFixed(2) + 's';
    el.classList.add('will-reveal');
    observer.observe(el);
  });
})();
