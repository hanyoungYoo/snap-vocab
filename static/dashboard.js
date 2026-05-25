const tbody = document.querySelector('#cards tbody');

function escape(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

async function load() {
  const res = await fetch('/api/cards?limit=200', {
    headers: { 'X-API-Key': window.API_KEY },
  });
  const { items } = await res.json();
  tbody.innerHTML = items.map(c => `
    <tr data-id="${c.id}">
      <td>${escape(c.expression)}</td>
      <td>${escape(c.type)}</td>
      <td>${escape((c.meaning && c.meaning.core) || '')}</td>
      <td>${escape(c.level)}</td>
      <td>${escape(c.next_review)}</td>
      <td><button class="del">삭제</button></td>
    </tr>`).join('');
}

tbody.addEventListener('click', async (e) => {
  if (!e.target.classList.contains('del')) return;
  const tr = e.target.closest('tr');
  if (!confirm(`삭제: ${tr.querySelector('td').textContent}?`)) return;
  const res = await fetch(`/api/cards/${tr.dataset.id}`, {
    method: 'DELETE',
    headers: { 'X-API-Key': window.API_KEY },
  });
  if (res.ok) tr.remove();
});

load();
