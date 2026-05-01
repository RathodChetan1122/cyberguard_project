/* ═══════════════════════════════════════════════════════════════════════════
   CyberGuard — Main JavaScript
═══════════════════════════════════════════════════════════════════════════ */

'use strict';

// ── Loading Overlay ───────────────────────────────────────────────────────
function showLoading(text) {
  const overlay = document.getElementById('loadingOverlay');
  const label   = document.getElementById('loadingText');
  if (!overlay) return;
  if (label && text) label.textContent = text;
  overlay.classList.remove('d-none');
}

function hideLoading() {
  const overlay = document.getElementById('loadingOverlay');
  if (overlay) overlay.classList.add('d-none');
}

// Hide loading on back navigation
window.addEventListener('pageshow', hideLoading);

// ── CSRF helper ───────────────────────────────────────────────────────────
function getCsrfToken() {
  const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
  return cookie ? cookie.split('=')[1].trim() : '';
}

// ── Animate confidence bars on page load ─────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

  // Confidence bars
  setTimeout(() => {
    document.querySelectorAll('.confidence-bar[data-width]').forEach(bar => {
      bar.style.transition = 'width 1s cubic-bezier(0.4,0,0.2,1)';
      bar.style.width = bar.dataset.width;
    });
    document.querySelectorAll('.risk-gauge-fill[data-width]').forEach(bar => {
      bar.style.transition = 'width 1.2s cubic-bezier(0.4,0,0.2,1)';
      bar.style.width = bar.dataset.width;
    });
  }, 250);

  // Mini conf bars — set width from inline style if present
  document.querySelectorAll('.mini-conf-bar').forEach(bar => {
    // width already set inline via template
  });

  // Input validation feedback
  document.querySelectorAll('form').forEach(form => {
    form.querySelectorAll('input, textarea').forEach(input => {
      input.addEventListener('blur', () => {
        if (!input.value.trim()) {
          input.classList.add('is-invalid-soft');
        } else {
          input.classList.remove('is-invalid-soft');
        }
      });
      input.addEventListener('input', () => {
        input.classList.remove('is--invalid-soft');
      });
    });
  });

  // Auto-scroll to result if present
  const resultPanel = document.getElementById('resultPanel');
  if (resultPanel && resultPanel.querySelector('.verdict-banner')) {
    setTimeout(() => {
      const isMobile = window.innerWidth < 992;
      if (isMobile) {
        resultPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 400);
  }

  // Tooltips on long inputs in history table
  document.querySelectorAll('.input-cell span[title]').forEach(el => {
    el.style.cursor = 'help';
  });

  // Stat number counter animation on home page
  document.querySelectorAll('.stat-number').forEach(el => {
    const target = parseInt(el.textContent.replace(/[^0-9]/g, ''), 10);
    if (!isNaN(target) && target > 0) {
      animateCounter(el, target);
    }
  });

});

// ── Counter Animation ─────────────────────────────────────────────────────
function animateCounter(el, target) {
  const duration  = 800;
  const start     = performance.now();
  const startVal  = 0;

  function update(now) {
    const elapsed  = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased    = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    el.textContent = Math.round(startVal + eased * (target - startVal));
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

// ── Dismiss alerts ────────────────────────────────────────────────────────
document.addEventListener('click', e => {
  if (e.target.matches('[data-dismiss-alert]')) {
    e.target.closest('.alert')?.remove();
  }
});

// ── Expose globally ───────────────────────────────────────────────────────
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.getCsrfToken = getCsrfToken;
