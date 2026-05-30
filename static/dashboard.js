/* snap-vocab console */

const PAGE_SIZE = 50;
const state = {
  offset: 0,
  q: '',
  type: '',
  level: '',
  due: false,
  sort: 'updated_at',
  order: 'desc',
  total: 0,
  charts: { timeseries: null, levels: null },
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function getCookie(name) {
  const m = document.cookie.split('; ').find((r) => r.startsWith(name + '='));
  return m ? decodeURIComponent(m.split('=')[1]) : '';
}

function escape(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

async function api(path, opts = {}) {
  const headers = { 'X-API-Key': getCookie('api_key'), ...(opts.headers || {}) };
  if (opts.body && !(opts.body instanceof FormData)) headers['Content-Type'] = 'application/json';
  const res = await fetch(path, { ...opts, headers });
  if (res.status === 401) {
    window.location.href = '/';
    throw new Error('unauthorized');
  }
  if (!res.ok) throw new Error(`${res.status}`);
  if (res.status === 204) return null;
  return res.json();
}

function toast(msg, kind = 'info') {
  const el = $('#toast');
  el.textContent = msg;
  el.classList.remove('hidden');
  el.classList.toggle('bg-rose-600', kind === 'error');
  el.classList.toggle('text-white', kind === 'error');
  setTimeout(() => el.classList.add('hidden'), 2500);
}

/* ---------- Theme ---------- */
$('#theme-toggle').addEventListener('click', () => {
  const isDark = document.documentElement.classList.toggle('dark');
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
  // re-render charts so they pick up new theme colors
  drawCharts();
});

/* ---------- Summary + charts ---------- */
function chartColors() {
  const dark = document.documentElement.classList.contains('dark');
  return {
    grid: dark ? 'rgba(148,163,184,0.15)' : 'rgba(100,116,139,0.15)',
    text: dark ? '#cbd5e1' : '#475569',
    primary: '#6366f1',
    accent: '#10b981',
  };
}

let lastSummary = null;
let lastTimeseries = null;

async function loadSummary() {
  const data = await api('/api/stats/summary');
  lastSummary = data;
  $('[data-stat="total"]').textContent = data.total;
  $('[data-stat="due_today"]').textContent = data.due_today;
  $('[data-stat="accuracy_7d"]').textContent = `${data.accuracy_7d}%`;
  $('[data-stat="new_7d"]').textContent = data.new_7d;
  drawLevels(data.levels);
}

async function loadTimeseries() {
  const data = await api('/api/stats/timeseries?days=30');
  lastTimeseries = data.points;
  drawTimeseries(data.points);
}

function drawCharts() {
  if (lastSummary) drawLevels(lastSummary.levels);
  if (lastTimeseries) drawTimeseries(lastTimeseries);
}

function drawTimeseries(points) {
  const c = chartColors();
  const ctx = $('#chart-timeseries');
  if (state.charts.timeseries) state.charts.timeseries.destroy();
  state.charts.timeseries = new Chart(ctx, {
    data: {
      labels: points.map((p) => p.day.slice(5)),
      datasets: [
        {
          type: 'bar',
          label: '리뷰 수',
          data: points.map((p) => p.reviews),
          backgroundColor: c.primary + '99',
          yAxisID: 'y',
          borderRadius: 4,
        },
        {
          type: 'line',
          label: '정답률 (%)',
          data: points.map((p) => p.accuracy),
          borderColor: c.accent,
          backgroundColor: c.accent,
          spanGaps: true,
          tension: 0.3,
          yAxisID: 'y1',
        },
      ],
    },
    options: {
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { labels: { color: c.text } } },
      scales: {
        x: { ticks: { color: c.text }, grid: { color: c.grid } },
        y: { beginAtZero: true, ticks: { color: c.text }, grid: { color: c.grid }, title: { display: false } },
        y1: { position: 'right', min: 0, max: 100, ticks: { color: c.text }, grid: { drawOnChartArea: false } },
      },
    },
  });
}

function drawLevels(levels) {
  const c = chartColors();
  const ctx = $('#chart-levels');
  if (state.charts.levels) state.charts.levels.destroy();
  state.charts.levels = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: levels.map((l) => `L${l.level}`),
      datasets: [{
        data: levels.map((l) => l.n),
        backgroundColor: c.primary + 'CC',
        borderRadius: 4,
      }],
    },
    options: {
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: c.text }, grid: { color: c.grid } },
        y: { beginAtZero: true, ticks: { color: c.text, precision: 0 }, grid: { color: c.grid } },
      },
    },
  });
}

/* ---------- Admin status ---------- */
function dot(ok) {
  return `<span class="inline-block h-2 w-2 rounded-full ${ok ? 'bg-emerald-500' : 'bg-rose-500'}"></span>`;
}

async function loadStatus() {
  try {
    const s = await api('/api/admin/status');
    const next = s.scheduler.next_run_at
      ? new Date(s.scheduler.next_run_at).toLocaleString('ko-KR')
      : '—';
    $('#admin-status').innerHTML = `
      <div class="text-sm"><div class="text-xs text-slate-500 mb-0.5">LLM</div>
        ${dot(s.llm.configured)} ${escape(s.llm.provider || '미설정')}
        <div class="text-xs text-slate-500 mt-0.5">${escape(s.llm.extract_model)}</div>
      </div>
      <div class="text-sm"><div class="text-xs text-slate-500 mb-0.5">알림</div>
        ${dot(s.notification.configured)} ${escape(s.notification.provider)}
      </div>
      <div class="text-sm"><div class="text-xs text-slate-500 mb-0.5">다음 복습 (${escape(s.scheduler.review_time)})</div>
        <div class="text-xs">${escape(next)}</div>
      </div>
      <div class="text-sm"><div class="text-xs text-slate-500 mb-0.5">DB</div>
        ${dot(s.db.ok)} ${s.db.ok ? '연결됨' : '오류'}
      </div>`;
  } catch (e) {
    $('#admin-status').innerHTML = `<div class="text-xs text-rose-500">상태 조회 실패</div>`;
  }
}

$('#status-refresh').addEventListener('click', () => {
  loadStatus();
  loadSummary();
  loadTimeseries();
});

$('#trigger-review').addEventListener('click', async (e) => {
  const btn = e.currentTarget;
  btn.disabled = true;
  try {
    const r = await api('/api/admin/trigger-review', { method: 'POST' });
    toast(`알림 ${r.sent}건 전송`);
  } catch (err) {
    toast('전송 실패', 'error');
  } finally {
    btn.disabled = false;
  }
});

/* ---------- Cards list ---------- */
function buildQuery() {
  const p = new URLSearchParams({
    limit: PAGE_SIZE,
    offset: state.offset,
    sort: state.sort,
    order: state.order,
  });
  if (state.q) p.set('q', state.q);
  if (state.type) p.set('type', state.type);
  if (state.level !== '') p.set('level', state.level);
  if (state.due) p.set('due', 'true');
  return p.toString();
}

async function loadCards() {
  const tbody = $('#cards-tbody');
  tbody.innerHTML = `<tr><td colspan="6" class="px-4 py-6 text-center text-xs text-slate-400">불러오는 중…</td></tr>`;
  try {
    const data = await api(`/api/cards?${buildQuery()}`);
    state.total = data.total;
    renderCards(data.items);
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" class="px-4 py-6 text-center text-xs text-rose-500">불러오기 실패</td></tr>`;
  }
}

function renderCards(items) {
  const tbody = $('#cards-tbody');
  const empty = $('#cards-empty');
  if (!items.length) {
    tbody.innerHTML = '';
    empty.classList.remove('hidden');
  } else {
    empty.classList.add('hidden');
    tbody.innerHTML = items.map((c) => `
      <tr data-id="${c.id}" class="hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer">
        <td class="px-4 py-2 font-medium">${escape(c.expression)}</td>
        <td class="px-4 py-2"><span class="inline-block text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800">${escape(c.type)}</span></td>
        <td class="px-4 py-2 text-slate-600 dark:text-slate-300">${escape((c.meaning && c.meaning.core) || '')}</td>
        <td class="px-4 py-2">L${escape(c.level)}</td>
        <td class="px-4 py-2 text-slate-500">${escape(c.next_review)}</td>
        <td class="px-4 py-2 text-right">
          <button class="del text-xs px-2 py-1 rounded text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40">삭제</button>
        </td>
      </tr>`).join('');
  }
  const page = Math.floor(state.offset / PAGE_SIZE) + 1;
  const pages = Math.max(1, Math.ceil(state.total / PAGE_SIZE));
  $('#cards-count').textContent = `${state.total}건`;
  $('#page-info').textContent = `${page} / ${pages}`;
  $('#page-prev').disabled = state.offset === 0;
  $('#page-next').disabled = state.offset + PAGE_SIZE >= state.total;
}

/* events */
let qTimer;
$('#filter-q').addEventListener('input', (e) => {
  clearTimeout(qTimer);
  qTimer = setTimeout(() => {
    state.q = e.target.value.trim();
    state.offset = 0;
    loadCards();
  }, 250);
});
$('#filter-type').addEventListener('change', (e) => { state.type = e.target.value; state.offset = 0; loadCards(); });
$('#filter-level').addEventListener('change', (e) => { state.level = e.target.value; state.offset = 0; loadCards(); });
$('#filter-due').addEventListener('change', (e) => { state.due = e.target.checked; state.offset = 0; loadCards(); });
$('#page-prev').addEventListener('click', () => { state.offset = Math.max(0, state.offset - PAGE_SIZE); loadCards(); });
$('#page-next').addEventListener('click', () => { state.offset += PAGE_SIZE; loadCards(); });

$$('th[data-sort]').forEach((th) => {
  th.addEventListener('click', () => {
    const col = th.dataset.sort;
    if (state.sort === col) state.order = state.order === 'asc' ? 'desc' : 'asc';
    else { state.sort = col; state.order = 'asc'; }
    state.offset = 0;
    loadCards();
  });
});

$('#cards-tbody').addEventListener('click', async (e) => {
  const tr = e.target.closest('tr');
  if (!tr) return;
  const id = tr.dataset.id;
  if (e.target.classList.contains('del')) {
    e.stopPropagation();
    if (!confirm(`삭제: ${tr.querySelector('td').textContent}?`)) return;
    try {
      await api(`/api/cards/${id}`, { method: 'DELETE' });
      toast('삭제됨');
      loadCards();
      loadSummary();
    } catch {
      toast('삭제 실패', 'error');
    }
    return;
  }
  openDrawer(id);
});

/* ---------- Drawer ---------- */
const drawer = $('#drawer');
const backdrop = $('#drawer-backdrop');

function closeDrawer() {
  drawer.classList.add('translate-x-full');
  backdrop.classList.add('hidden');
}
backdrop.addEventListener('click', closeDrawer);
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeDrawer(); });

async function openDrawer(id) {
  backdrop.classList.remove('hidden');
  drawer.classList.remove('translate-x-full');
  $('#drawer-body').innerHTML = `<div class="text-sm text-slate-500">불러오는 중…</div>`;
  try {
    const { card, review_logs } = await api(`/api/cards/${id}`);
    renderDrawer(card, review_logs);
  } catch {
    $('#drawer-body').innerHTML = `<div class="text-sm text-rose-500">불러오기 실패</div>`;
  }
}

function renderDrawer(card, logs) {
  const examples = (card.examples || []).map((e) => `
    <li class="text-sm py-1">
      <span>${escape(e.sentence || '')}</span>
      ${e.source ? `<span class="ml-2 text-xs text-slate-400">${escape(e.source)}</span>` : ''}
    </li>`).join('');
  const logRows = logs.map((l) => `
    <li class="text-xs flex items-center gap-2 py-0.5">
      ${l.correct ? '<span class="text-emerald-500">✓</span>' : '<span class="text-rose-500">✗</span>'}
      <span class="text-slate-400">${escape(new Date(l.reviewed_at).toLocaleString('ko-KR'))}</span>
      <span>${escape(l.question_type)}</span>
      ${l.user_answer ? `<span class="text-slate-500">— ${escape(l.user_answer)}</span>` : ''}
    </li>`).join('') || `<li class="text-xs text-slate-400">이력 없음</li>`;

  $('#drawer-body').innerHTML = `
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold">${escape(card.expression)}</h3>
      <button id="drawer-close" class="text-slate-400 hover:text-slate-600 text-xl leading-none">×</button>
    </div>
    <div class="flex flex-wrap gap-2 text-xs">
      <span class="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800">${escape(card.type)}</span>
      <span class="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800">L${card.level}</span>
      <span class="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800">다음 ${escape(card.next_review)}</span>
    </div>

    <div>
      <div class="text-xs text-slate-500 mb-1">핵심 뜻</div>
      <div class="text-sm">${escape((card.meaning && card.meaning.core) || '')}</div>
      ${card.meaning && card.meaning.nuance ? `<div class="text-xs text-slate-500 mt-1">${escape(card.meaning.nuance)}</div>` : ''}
    </div>

    <div>
      <div class="text-xs text-slate-500 mb-1">인라인 편집</div>
      <form id="edit-form" class="space-y-2">
        <label class="block text-xs">핵심 뜻
          <input name="core" value="${escape((card.meaning && card.meaning.core) || '')}" class="mt-1 w-full px-2 py-1.5 text-sm rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950" />
        </label>
        <div class="flex gap-2">
          <label class="flex-1 text-xs">레벨
            <input name="level" type="number" min="0" max="10" value="${card.level}" class="mt-1 w-full px-2 py-1.5 text-sm rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950" />
          </label>
          <label class="flex-1 text-xs">다음 복습
            <input name="next_review" type="date" value="${escape(card.next_review)}" class="mt-1 w-full px-2 py-1.5 text-sm rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950" />
          </label>
        </div>
        <button class="mt-1 text-sm px-3 py-1.5 rounded bg-indigo-600 text-white hover:bg-indigo-500">저장</button>
      </form>
    </div>

    <div>
      <div class="text-xs text-slate-500 mb-1">예문 (${(card.examples || []).length})</div>
      <ul class="divide-y divide-slate-100 dark:divide-slate-800">${examples || '<li class="text-xs text-slate-400 py-1">없음</li>'}</ul>
    </div>

    <div>
      <div class="text-xs text-slate-500 mb-1">최근 복습 이력</div>
      <ul>${logRows}</ul>
    </div>`;

  $('#drawer-close').addEventListener('click', closeDrawer);
  $('#edit-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const patch = {
      meaning: { ...(card.meaning || {}), core: fd.get('core') },
      level: Number(fd.get('level')),
      next_review: fd.get('next_review'),
    };
    try {
      await api(`/api/cards/${card.id}`, { method: 'PATCH', body: JSON.stringify(patch) });
      toast('저장됨');
      closeDrawer();
      loadCards();
      loadSummary();
    } catch {
      toast('저장 실패', 'error');
    }
  });
}

/* ---------- Boot ---------- */
loadStatus();
loadSummary();
loadTimeseries();
loadCards();
