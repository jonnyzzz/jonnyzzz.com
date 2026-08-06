// Click-to-zoom for Mermaid diagrams: opens a full-screen overlay at natural size.
// Standalone enhancer - referenced from posts that carry large diagrams. It waits for
// _includes/mermaid.html to render the SVGs, then activates only on diagrams that were
// scaled down to fit the column. Styles live in _sass/_mermaid.scss (built into main.css).
(function() {
  if (!document.querySelector('pre code.language-mermaid, pre code.mermaid, .mermaid')) return;

  function openOverlay(svg) {
    var overlay = document.createElement('div');
    overlay.className = 'mermaid-overlay';
    var clone = svg.cloneNode(true);
    var vb = svg.viewBox && svg.viewBox.baseVal;
    if (vb && vb.width) {
      clone.style.width = vb.width + 'px';
    }
    overlay.appendChild(clone);
    function close() {
      overlay.remove();
      document.removeEventListener('keydown', onKey);
    }
    function onKey(e) { if (e.key === 'Escape') close(); }
    overlay.addEventListener('click', close);
    document.addEventListener('keydown', onKey);
    document.body.appendChild(overlay);
    overlay.scrollLeft = (overlay.scrollWidth - overlay.clientWidth) / 2;
  }

  function enhance(svg) {
    var vb = svg.viewBox && svg.viewBox.baseVal;
    if (!vb || !vb.width || svg.getBoundingClientRect().width >= vb.width - 1) return;
    svg.classList.add('mermaid-zoomable');
    svg.setAttribute('role', 'button');
    svg.setAttribute('aria-label', 'Open diagram full-screen');
    svg.addEventListener('click', function() { openOverlay(svg); });
  }

  // mermaid renders asynchronously after its CDN script loads - poll until every
  // diagram container got its SVG, then enhance the scaled-down ones
  var attempts = 0;
  var timer = setInterval(function() {
    attempts++;
    var containers = document.querySelectorAll('.mermaid');
    var pending = 0;
    Array.prototype.forEach.call(containers, function(c) {
      if (!c.querySelector('svg')) pending++;
    });
    if (containers.length > 0 && pending === 0) {
      Array.prototype.forEach.call(document.querySelectorAll('.mermaid svg'), enhance);
      clearInterval(timer);
    } else if (attempts > 100) {
      clearInterval(timer);
    }
  }, 200);
})();
