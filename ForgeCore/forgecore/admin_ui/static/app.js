// basic state
let orders = [];
let focusedId = null;

function loadOrders() {
  fetch('/gl/orders').then(r => r.json()).then(data => {
    orders = data;
    const cont = document.getElementById('orders');
    cont.innerHTML = '';
    data.forEach(o => {
      const div = document.createElement('div');
      div.className = 'order';
      div.dataset.id = o.id;
      div.textContent = `${o.id} - ${o.status}`;
      div.addEventListener('click', () => focusOrder(o.id));
      cont.appendChild(div);
    });
    if (focusedId) focusOrder(focusedId);
  });
}

function focusOrder(id) {
  focusedId = id;
  document.querySelectorAll('.order').forEach(el => el.classList.remove('focused'));
  const el = document.querySelector(`.order[data-id="${id}"]`);
  if (el) {
    el.classList.add('focused');
    el.scrollIntoView({ block: 'center' });
  }
}

function toolbarInit() {
  const tb = document.getElementById('toolbar');
  const btnOrder = document.createElement('button');
  btnOrder.textContent = 'Test: New Order';
  btnOrder.onclick = () => fetch('/gl/test/order', { method: 'POST' }).then(loadAll);
  tb.appendChild(btnOrder);
  const btnPrint = document.createElement('button');
  btnPrint.textContent = 'Test: Print';
  btnPrint.onclick = () => fetch('/gl/test/print', { method: 'POST' }).then(loadAll);
  tb.appendChild(btnPrint);
  const btnShip = document.createElement('button');
  btnShip.textContent = 'Test: Ship';
  btnShip.onclick = () => fetch('/gl/test/ship', { method: 'POST' }).then(loadAll);
  tb.appendChild(btnShip);
}

function loadLogs(filter = '') {
  let url = '/gl/logs';
  if (filter) url += `?topic=${encodeURIComponent(filter)}`;
  fetch(url).then(r => r.json()).then(data => {
    const cont = document.getElementById('log-entries');
    cont.innerHTML = '';
    data.forEach(ev => {
      const row = document.createElement('div');
      row.textContent = `${ev.ts} ${ev.topic} ${ev.order_id || ''}`;
      row.dataset.oid = ev.order_id;
      row.addEventListener('click', () => {
        if (ev.order_id) focusOrder(ev.order_id);
      });
      cont.appendChild(row);
    });
  });
}

document.getElementById('log-filter').addEventListener('input', e => {
  loadLogs(e.target.value);
});

function showShippingModal(oid) {
  const modal = document.getElementById('modal');
  fetch(`/gl/orders/${oid}/shipping/options`).then(r => r.json()).then(opts => {
    modal.innerHTML = '';
    const box = document.createElement('div');
    box.className = 'box';
    box.innerHTML = '<h3>Select Shipping</h3>';
    opts.forEach(opt => {
      const btn = document.createElement('button');
      btn.textContent = `${opt.carrier} ${opt.service} $${opt.cost} - ${opt.rationale}`;
      btn.addEventListener('click', () => {
        fetch(`/gl/orders/${oid}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ proposed_shipping_method: opt })
        }).then(() => fetch(`/gl/orders/${oid}/shipping/approve`, { method: 'POST' }))
        .then(() => { modal.classList.add('hidden'); loadOrders(); });
      });
      box.appendChild(btn);
    });
    const cancel = document.createElement('button');
    cancel.textContent = 'Cancel';
    cancel.onclick = () => modal.classList.add('hidden');
    box.appendChild(cancel);
    modal.appendChild(box);
    modal.classList.remove('hidden');
  });
}

function printInvoice(id) {
  fetch(`/gl/orders/${id}/print/invoice`, { method: 'POST' }).then(() => { loadOrders(); loadLogs(); });
}
function markAddressed(id) {
  fetch(`/gl/orders/${id}/status/Addressed`, { method: 'POST' }).then(loadOrders);
}
function markBags(id) {
  fetch(`/gl/orders/${id}/status/Bags%20Pulled`, { method: 'POST' }).then(loadOrders);
}
function printLabel(id) {
  fetch(`/gl/orders/${id}`).then(r => r.json()).then(o => {
    if (!o.approved_shipping_method) return;
    fetch(`/gl/orders/${id}/print/label`, { method: 'POST' }).then(() => { loadOrders(); loadLogs(); });
  });
}
function markComplete(id) {
  fetch(`/gl/orders/${id}/status/Completed`, { method: 'POST' }).then(loadOrders);
}

function batchPrintLabels(ids) {
  Promise.all(ids.map(i => fetch(`/gl/orders/${i}`).then(r => r.json()))).then(data => {
    const ok = data.filter(o => o.approved_shipping_method).map(o => o.id);
    ok.forEach(i => fetch(`/gl/orders/${i}/print/label`, { method: 'POST' }));
  });
}

document.addEventListener('keydown', e => {
  if (!focusedId) return;
  const k = e.key.toUpperCase();
  if (k === 'P') printInvoice(focusedId);
  if (k === 'A') markAddressed(focusedId);
  if (k === 'B') markBags(focusedId);
  if (k === 'M') showShippingModal(focusedId);
  if (k === 'L') printLabel(focusedId);
  if (k === 'C') markComplete(focusedId);
});

function loadAll() {
  loadOrders();
  loadLogs(document.getElementById('log-filter').value);
}

toolbarInit();
loadAll();
