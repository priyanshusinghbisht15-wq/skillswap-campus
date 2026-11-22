// SkillSwap Campus — main.js

// ─── SIDEBAR TOGGLE ────────────────────────────────────────────
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.toggle('open');
}

// Close sidebar when clicking outside (mobile)
document.addEventListener('click', (e) => {
  const sidebar = document.getElementById('sidebar');
  const toggle  = document.querySelector('.sidebar-toggle');
  if (window.innerWidth <= 768 && sidebar && sidebar.classList.contains('open')) {
    if (!sidebar.contains(e.target) && toggle && !toggle.contains(e.target)) {
      sidebar.classList.remove('open');
    }
  }
});

// ─── ACTIVE NAV LINK ───────────────────────────────────────────
function setActiveNavLink() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.remove('active');
    const href = link.getAttribute('href') || '';
    if (href === path || (href !== '/' && path.startsWith(href))) {
      link.classList.add('active');
    }
    if (href === '/' && path === '/') {
      link.classList.add('active');
    }
  });
}

// ─── MODAL HELPERS ─────────────────────────────────────────────
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.remove('open');
    document.body.style.overflow = '';
  }
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
    document.body.style.overflow = '';
  }
});

// Close modal on Escape
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open').forEach(m => {
      m.classList.remove('open');
      document.body.style.overflow = '';
    });
  }
});

// ─── SCORE BREAKDOWN TOGGLE ────────────────────────────────────
function toggleBreakdown(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.toggle('open');
  const btn = el.previousElementSibling;
  if (btn && btn.classList.contains('breakdown-toggle')) {
    btn.textContent = el.classList.contains('open') ? '▲ Hide Details' : '▼ Show Score Details';
  }
}

// ─── STAR RATING ───────────────────────────────────────────────
function initStarRatings() {
  document.querySelectorAll('.star-rating-interactive').forEach(container => {
    const stars = container.querySelectorAll('.star');
    const input = container.querySelector('input[name="stars"]');

    stars.forEach((star, idx) => {
      star.addEventListener('mouseenter', () => {
        stars.forEach((s, i) => s.classList.toggle('filled', i <= idx));
      });
      star.addEventListener('mouseleave', () => {
        const val = parseInt(input?.value || 0);
        stars.forEach((s, i) => s.classList.toggle('filled', i < val));
      });
      star.addEventListener('click', () => {
        if (input) input.value = idx + 1;
        stars.forEach((s, i) => s.classList.toggle('filled', i <= idx));
      });
    });
  });
}

// ─── PARTNER SKILL LOADER ──────────────────────────────────────
function loadPartnerSkills() {
  const partnerSelect = document.getElementById('partner_select');
  const skillSelect   = document.getElementById('skill_select');
  if (!partnerSelect || !skillSelect) return;

  partnerSelect.addEventListener('change', async () => {
    const partnerId = partnerSelect.value;
    if (!partnerId) {
      skillSelect.innerHTML = '<option value="">— select skill —</option>';
      return;
    }
    try {
      const res  = await fetch(`/api/partner-skills/${partnerId}`);
      const data = await res.json();
      skillSelect.innerHTML = '<option value="">— select skill —</option>' +
        data.map(s => `<option value="${s.id}">${s.name} (${s.proficiency})</option>`).join('');
    } catch (err) {
      console.error('Failed to load skills', err);
    }
  });
}

// ─── AVAILABILITY CHECKER ──────────────────────────────────────
async function checkAvailability(studentAId, studentBId, containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '<p class="text-muted text-sm">Loading...</p>';
  try {
    const res  = await fetch(`/api/availability/${studentAId}/${studentBId}`);
    const data = await res.json();
    if (data.slots.length === 0) {
      container.innerHTML = '<p class="text-muted text-sm">No overlapping availability found.</p>';
    } else {
      container.innerHTML = `
        <div class="text-sm" style="color:var(--accent-green);font-weight:600;margin-bottom:6px;">
          ${data.total_hours}h total shared time
        </div>
        ${data.slots.map(s => `
          <div class="skill-match-row">
            <span class="skill-tag tag-offer">${s.day}</span>
            <span class="text-sm">${s.start} – ${s.end}</span>
          </div>
        `).join('')}
      `;
    }
  } catch (err) {
    container.innerHTML = '<p class="text-muted text-sm">Could not load availability.</p>';
  }
}

// ─── PROGRESS BAR ANIMATION ────────────────────────────────────
function animateProgressBars() {
  document.querySelectorAll('.progress-fill, .score-bar-fill, .xp-bar-fill').forEach(bar => {
    const target = bar.dataset.width || bar.style.width;
    bar.style.width = '0%';
    setTimeout(() => { bar.style.width = target; }, 100);
  });
}

// ─── FLASH MESSAGES AUTO-DISMISS ──────────────────────────────
function initAlertDismiss() {
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s ease';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 500);
    }, 4000);
  });
}

// ─── SEARCH / FILTER ───────────────────────────────────────────
function initSearch() {
  const searchInput = document.getElementById('partner_search');
  if (!searchInput) return;

  searchInput.addEventListener('input', () => {
    const query = searchInput.value.toLowerCase();
    document.querySelectorAll('.partner-card').forEach(card => {
      const name = card.dataset.name?.toLowerCase() || '';
      const skills = card.dataset.skills?.toLowerCase() || '';
      card.closest('.partner-card-wrap').style.display =
        (name.includes(query) || skills.includes(query)) ? '' : 'none';
    });
  });
}

// ─── FADE-IN CARDS ─────────────────────────────────────────────
function initFadeIn() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('fade-in');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08 });

  document.querySelectorAll('.card, .partner-card, .session-card, .chain-card, .stat-card').forEach(el => {
    observer.observe(el);
  });
}

// ─── HEATMAP ───────────────────────────────────────────────────
async function initHeatmap() {
  const canvas = document.getElementById('heatmapChart');
  if (!canvas) return;

  try {
    const res  = await fetch('/api/heatmap-data');
    const data = await res.json();

    const labels  = data.map(d => d.skill);
    const offered = data.map(d => d.offered);
    const wanted  = data.map(d => d.wanted);

    new Chart(canvas, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Students Offering',
            data: offered,
            backgroundColor: 'rgba(16,185,129,0.6)',
            borderColor: 'rgba(16,185,129,0.9)',
            borderWidth: 1,
            borderRadius: 6,
          },
          {
            label: 'Students Wanting',
            data: wanted,
            backgroundColor: 'rgba(239,68,68,0.5)',
            borderColor: 'rgba(239,68,68,0.8)',
            borderWidth: 1,
            borderRadius: 6,
          },
        ],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#94a3b8', font: { size: 12 } } },
          tooltip: { mode: 'index', intersect: false },
        },
        scales: {
          x: {
            ticks: { color: '#64748b' },
            grid:  { color: 'rgba(255,255,255,0.05)' },
          },
          y: {
            ticks: { color: '#94a3b8', font: { size: 11 } },
            grid:  { color: 'rgba(255,255,255,0.05)' },
          },
        },
      },
    });

    // Render gap list
    const gapList = document.getElementById('gapList');
    if (gapList) {
      const sorted = [...data].sort((a, b) => b.gap - a.gap);
      gapList.innerHTML = sorted.map(d => {
        const isShortage = d.gap > 0;
        const color = isShortage ? 'var(--accent-red)' : 'var(--accent-green)';
        const label = isShortage ? `⚠ Shortage (+${d.gap})` : `✓ Surplus (${d.gap})`;
        return `
          <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border);">
            <span style="flex:1;font-size:13px;color:var(--text-primary);">${d.skill}</span>
            <span style="font-size:11px;color:var(--text-muted);">${d.offered} offer / ${d.wanted} want</span>
            <span style="font-size:11px;font-weight:700;color:${color};">${label}</span>
          </div>`;
      }).join('');
    }
  } catch (err) {
    console.error('Heatmap load error', err);
    if (canvas.parentElement) {
      canvas.parentElement.innerHTML = '<p class="text-muted text-sm">Could not load heatmap data.</p>';
    }
  }
}

// ─── INIT ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  setActiveNavLink();
  initStarRatings();
  loadPartnerSkills();
  animateProgressBars();
  initAlertDismiss();
  initSearch();
  initFadeIn();
  initHeatmap();
});
