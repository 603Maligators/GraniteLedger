async function fetchJSON(url, opts = {}) {
  const res = await fetch(url, opts);
  return res.json();
}

function renderOrders(orders) {
  const columns = document.querySelectorAll('.column');
  columns.forEach(col => col.querySelector('.cards').innerHTML = '');
  orders.forEach(o => {
    const col = document.querySelector(`.column[data-status="${o.status}"] .cards`);
    if (!col) return;
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <input type="checkbox" class="select-order" data-id="${o.id}" />
      <span class="oid">${o.id}</span>
      <button data-act="invoice" data-id="${o.id}">Inv</button>
      <button data-act="addressed" data-id="${o.id}">Addr</button>
      <button data-act="bag" data-id="${o.id}">Bag</button>
      <button data-act="ship" data-id="${o.id}">Ship</button>
      <button data-act="label" data-id="${o.id}">Label</button>
      <button data-act="complete" data-id="${o.id}">Done</button>`;
    col.appendChild(card);
  });
}

async function loadOrders() {
  const orders = await fetchJSON('/gl/orders');
  renderOrders(orders);
}

async function orderAction(act, id) {
  const map = {
    invoice: `/gl/orders/${id}/print/invoice`,
    addressed: `/gl/orders/${id}/addressed`,
    bag: `/gl/orders/${id}/status/Bags%20Pulled`,
    label: `/gl/orders/${id}/print/label`,
    complete: `/gl/orders/${id}/status/Completed`,
  };
  if (act === 'ship') return openShipping(id);
  const url = map[act];
  if (!url) return;
  await fetchJSON(url, { method: 'POST' });
  loadOrders();
}

async function openShipping(id) {
  const opts = await fetchJSON(`/gl/orders/${id}/shipping/options`);
  const container = document.getElementById('shipping-options');
  container.innerHTML = opts
    .map((o, i) => `<label><input type="radio" name="shipopt" value="${i}"> ${o.carrier} ${o.service} $${o.cost.toFixed(2)} (${o.rationale})</label><br/>`)
    .join('');
  container.dataset.id = id;
  document.getElementById('shipping-modal').classList.remove('hidden');
}

async function approveShipping() {
  const container = document.getElementById('shipping-options');
  const id = container.dataset.id;
  const idx = document.querySelector('input[name="shipopt"]:checked');
  if (!id || !idx) return closeShipping();
  const opts = await fetchJSON(`/gl/orders/${id}/shipping/options`);
  const chosen = opts[parseInt(idx.value, 10)];
  await fetchJSON(`/gl/orders/${id}/shipping/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(chosen),
  });
  closeShipping();
  loadOrders();
}

function closeShipping() {
  document.getElementById('shipping-modal').classList.add('hidden');
}

function selectedIds() {
  return Array.from(document.querySelectorAll('.select-order:checked')).map(i => i.dataset.id);
}

async function batch(path) {
  const ids = selectedIds();
  if (!ids.length) return;
  await fetchJSON(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(ids),
  });
  loadOrders();
}

async function batchStatus() {
  const status = document.getElementById('batch-status').value;
  if (!status) return;
  await batch(`/gl/orders/batch/status/${encodeURIComponent(status)}`);
}

let logSince = null;
async function pollLogs() {
  let url = '/gl/logs';
  if (logSince) url += `?since=${encodeURIComponent(logSince)}`;
  const logs = await fetchJSON(url);
  if (logs.length) {
    logSince = logs[0].ts;
    const box = document.getElementById('logs');
    logs.reverse().forEach(l => {
      const div = document.createElement('div');
      div.textContent = `${l.ts} ${l.topic} ${l.detail || ''}`;
      box.prepend(div);
    });
  }
}

document.addEventListener('click', e => {
  const act = e.target.dataset.act;
  const id = e.target.dataset.id;
  if (act && id) {
    orderAction(act, id);
  }
});

document.getElementById('batch-print-invoices').onclick = () => batch('/gl/orders/batch/print/invoices');
document.getElementById('batch-print-labels').onclick = () => batch('/gl/orders/batch/print/labels');
document.getElementById('batch-set-status').onclick = batchStatus;
document.getElementById('shipping-approve').onclick = approveShipping;
document.getElementById('shipping-close').onclick = closeShipping;

loadOrders();
setInterval(loadOrders, 3000);
setInterval(pollLogs, 3000);

