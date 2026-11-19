// --- INTRO SEQUENCE & SECTION REVEAL ---
function initIntroAndReveal() {
  const intro = document.getElementById('intro-sequence');
  if (intro) {
    if (sessionStorage.getItem('beacon_intro_seen') === '1') {
      intro.classList.add('is-skipped');
    } else {
      sessionStorage.setItem('beacon_intro_seen', '1');
      intro.addEventListener('animationend', (e) => {
        if (e.animationName === 'intro-exit') {
          intro.classList.add('is-done');
        }
      });
    }
  }

  requestAnimationFrame(() => {
    document.querySelectorAll('[data-reveal]').forEach((el) => {
      el.classList.add('revealed');
    });
  });
}

// --- KITCHEN ACCESS GATE ---
function initKitchenGate() {
  const gate = document.getElementById('kitchen-gate');
  if (gate && sessionStorage.getItem('beacon_chef_verified') === '1') {
    gate.classList.add('hidden');
  }
}

function verifyChef(btn, isHumanChef) {
  const feedback = document.getElementById('gate-feedback');
  if (isHumanChef) {
    sessionStorage.setItem('beacon_chef_verified', '1');
    feedback.style.color = 'var(--risk-sizzling)';
    feedback.textContent = 'Verified. Entering dashboard...';
    setTimeout(() => {
      document.getElementById('kitchen-gate').classList.add('hidden');
    }, 250);
  } else {
    btn.classList.add('wrong');
    feedback.style.color = 'var(--risk-burnt)';
    feedback.textContent = 'Access denied. Automated agents are blocked.';
    setTimeout(() => btn.classList.remove('wrong'), 350);
  }
}

// --- BRAND MEGA-DRAWER & NAVIGATION ---
function toggleBrandMenu(event) {
  event.stopPropagation();
  const header = document.querySelector('.rs-header');
  const wrap = document.getElementById('brand-menu-wrap');
  const backdrop = document.getElementById('rs-backdrop');
  const isOpen = header.classList.toggle('menu-open');

  wrap.classList.toggle('open', isOpen);
  backdrop.classList.toggle('visible', isOpen);
  wrap.querySelector('.rs-brand-btn').setAttribute('aria-expanded', String(isOpen));
}

function closeBrandMenu() {
  const header = document.querySelector('.rs-header');
  const wrap = document.getElementById('brand-menu-wrap');
  const backdrop = document.getElementById('rs-backdrop');
  if (header) header.classList.remove('menu-open');
  if (wrap) wrap.classList.remove('open');
  if (backdrop) backdrop.classList.remove('visible');
}

function switchTab(tabName, btn) {
  document.querySelectorAll('.rs-nav-link').forEach((t) => t.classList.remove('active'));
  if (btn) btn.classList.add('active');
  document.querySelectorAll('.tab-view').forEach((v) => v.classList.remove('active'));
  const target = document.getElementById(`tab-${tabName}`);
  if (target) target.classList.add('active');
  closeBrandMenu();
}

function selectTabFromMenu(tabName) {
  const navBtn = document.querySelector(`.rs-nav-link[data-tab="${tabName}"]`);
  switchTab(tabName, navBtn);
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeBrandMenu();
});

// --- MASCOT INTERACTIVE QUOTES ---
const MASCOT_QUOTES = [
  {
    badge: 'STATUS: WIP',
    title: 'The web dashboard is still warming up - no data yet',
    desc: 'The interface is ready, but live sockets from <code>NetworkMonitor</code> and the history API via WebSocket will be wired in upcoming commits.'
  },
  {
    badge: 'TIP: CLI READY',
    title: 'Do not wait for a release - the terminal is already hot',
    desc: 'Run <code>beacon</code> or <code>beacon --history --suspicious</code> in the console to inspect outbound sockets right now.'
  },
  {
    badge: 'SECURITY: 127.0.0.1',
    title: 'No socket goes out without authorization',
    desc: 'The local server is bound strictly to <code>127.0.0.1</code> and protected by a one-time session token.'
  },
  {
    badge: 'CHEF MODE',
    title: 'Do not poke the bacon - it is still raw (RAW)!',
    desc: 'After WebSocket is connected, every suspicious <code>BURNT</code> process will rise to the top of the table.'
  }
];

let mascotQuoteIdx = 0;

function pokeMascot() {
  const img = document.getElementById('beacon-mascot');
  const bubble = document.getElementById('mascot-bubble');
  if (!img || !bubble) return;

  img.classList.remove('poked');
  void img.offsetWidth;
  img.classList.add('poked');

  bubble.classList.add('is-switching');

  setTimeout(() => {
    mascotQuoteIdx = (mascotQuoteIdx + 1) % MASCOT_QUOTES.length;
    const quote = MASCOT_QUOTES[mascotQuoteIdx];

    document.getElementById('mascot-badge').textContent = quote.badge;
    document.getElementById('mascot-title').textContent = quote.title;
    document.getElementById('mascot-desc').innerHTML = quote.desc;

    bubble.classList.remove('is-switching');
  }, 160);
}

// --- UI LANGUAGE STRINGS ---
const I18N_STRINGS = {
  en: {
    strip_text: 'BEACON v2.0.0 WEB DASHBOARD — LOCAL TELEMETRY INTERFACE (BOUND TO 127.0.0.1)',
    status_awaiting: 'Awaiting Stream',
    btn_pause: 'Pause',
    hero_kicker: 'UNTRUSTED OUTBOUND ALERTS (BURNT)',
    hero_caption: 'No untrusted processes detected while stream is offline',
    hero_status_title: 'UI Scaffold Ready (WIP)',
    hero_status_desc: 'Live socket streaming via WebSocket and SQLite history endpoints will be wired in upcoming commits.',
    kpi_active: 'Active Sockets',
    kpi_active_sub: 'No live stream connected yet',
    kpi_sizzling_sub: 'Trusted ports 80, 443, 53',
    kpi_crispy_sub: 'Trusted non-standard ports',
    kpi_burnt_sub: 'New targets this session: 0',
    chart_title: 'Active Sockets Over Time (count)',
    donut_title: 'Roast Distribution & Top Processes'
  }
};

function setUiLang(lang) {
  const dict = I18N_STRINGS[lang] || I18N_STRINGS.en;
  document.documentElement.lang = lang;
  document.querySelectorAll('[data-i18n]').forEach((el) => {
    const key = el.getAttribute('data-i18n');
    if (dict[key]) {
      el.textContent = dict[key];
    }
  });
}

// --- EMPTY TELEMETRY CHARTS (WIP STATE) ---
function drawEmptyTrafficChart() {
  const canvas = document.getElementById('trafficChart');
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;

  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  const w = rect.width;
  const h = rect.height;

  const padLeft = 38;
  const padRight = 12;
  const padTop = 12;
  const padBottom = 28;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  ctx.clearRect(0, 0, w, h);

  const maxVal = 40;
  ctx.font = '12px "JetBrains Mono", monospace';
  ctx.fillStyle = '#d0d7de';
  ctx.textAlign = 'right';
  ctx.textBaseline = 'middle';

  [0, 20, 40].forEach((val) => {
    const y = padTop + plotH - (val / maxVal) * plotH;
    ctx.fillText(String(val), padLeft - 8, y);

    ctx.strokeStyle = '#21262d';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(padLeft + plotW, y);
    ctx.stroke();
  });

  ctx.textBaseline = 'top';
  ctx.textAlign = 'left';
  ctx.fillText('-30s', padLeft, padTop + plotH + 8);
  ctx.textAlign = 'center';
  ctx.fillText('-15s', padLeft + plotW / 2, padTop + plotH + 8);
  ctx.textAlign = 'right';
  ctx.fillText('now', padLeft + plotW, padTop + plotH + 8);

  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillStyle = '#b1bac4';
  ctx.font = '14px "JetBrains Mono", monospace';
  ctx.fillText('No telemetry stream connected yet (WIP)', padLeft + plotW / 2, padTop + plotH / 2);
}

function drawEmptyDonutChart() {
  const canvas = document.getElementById('roastDonut');
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const size = canvas.parentElement.clientWidth || 168;
  const center = size / 2;
  const radius = center - 16;

  canvas.width = size * dpr;
  canvas.height = size * dpr;
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  ctx.clearRect(0, 0, size, size);
  ctx.beginPath();
  ctx.arc(center, center, radius, 0, Math.PI * 2);
  ctx.strokeStyle = '#30363d';
  ctx.lineWidth = 13;
  ctx.stroke();
}

// --- INERTIAL AMBIENT PARALLAX ---
(() => {
  let targetX = 0;
  let targetY = 0;
  let currentX = 0;
  let currentY = 0;

  window.addEventListener('pointermove', (e) => {
    targetX = ((e.clientX / window.innerWidth) - 0.5) * 90;
    targetY = ((e.clientY / window.innerHeight) - 0.5) * 60;
  }, { passive: true });

  function animateAmbient() {
    currentX += (targetX - currentX) * 0.06;
    currentY += (targetY - currentY) * 0.06;
    document.body.style.setProperty('--pointer-x', `${currentX.toFixed(1)}px`);
    document.body.style.setProperty('--pointer-y', `${currentY.toFixed(1)}px`);
    requestAnimationFrame(animateAmbient);
  }
  requestAnimationFrame(animateAmbient);
})();

window.addEventListener('resize', drawEmptyTrafficChart);

document.addEventListener('DOMContentLoaded', () => {
  initIntroAndReveal();
  initKitchenGate();
  setUiLang('en');
  drawEmptyTrafficChart();
  drawEmptyDonutChart();
});