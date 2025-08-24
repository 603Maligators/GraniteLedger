const statuses = [
  "New",
  "Printed",
  "Addressed",
  "Bags Pulled",
  "Ship Method Chosen",
  "Shipped",
  "Completed",
];

let orders = [];
const selected = new Set();
let focusedTile = null;
let lastLogTs = new Date(0).toISOString();
let shippingOrder = null;

function qs(sel) {
  return document.querySelector(sel);
}

function showToast(msg) {
  const t = qs("#toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 3000);
}

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const txt = await res.text();
    showToast(txt || res.statusText);
    throw new Error(res.statusText);
  }
  if (res.status === 204) return {};
  return res.json();
}

async function loadOrders() {
  try {
    orders = await fetchJSON("/gl/orders");
    renderBoard();
  } catch (e) {}
}

function renderBoard() {
  const board = qs("#board");
  board.innerHTML = "";
  statuses.forEach((status) => {
    const col = document.createElement("div");
    col.className = "column";
    col.dataset.status = status;
    col.innerHTML = `<h2>${status}</h2>`;
    orders
      .filter((o) => o.status === status)
      .forEach((o) => col.appendChild(createTile(o)));
    board.appendChild(col);
  });
}

function createTile(order) {
  const tile = document.createElement("div");
  tile.className = "tile";
  tile.dataset.id = order.id;

  const last = order.history.length
    ? order.history[order.history.length - 1].ts
    : "";
  const proposed = order.proposed_shipping_method
    ? `${order.proposed_shipping_method.carrier} ${order.proposed_shipping_method.service}`
    : "";
  const approved = order.approved_shipping_method
    ? `${order.approved_shipping_method.carrier} ${order.approved_shipping_method.service}`
    : "";

  tile.innerHTML = `
    <div class="select"><input type="checkbox"></div>
    <div class="info">
      <div><strong>${order.id}</strong> - ${order.buyer.name}</div>
      <div>${order.computed_weight}lb • ${order.shipping_tier} • ${order.destination.zip}</div>
      <div>Status: ${order.status}</div>
      <div>Proposed: ${proposed}</div>
      <div>Approved: ${approved}</div>
      <div>Tracking: ${order.tracking_number || ""}</div>
      <div>Last: ${last}</div>
    </div>
    <div class="tile-actions">
      <button class="act-invoice">Invoice</button>
      <button class="act-addressed">Addressed</button>
      <button class="act-bags">Bags</button>
      <button class="act-ship">Approve Ship</button>
      <button class="act-label">Label</button>
      <button class="act-complete">Complete</button>
    </div>
  `;

  tile.addEventListener("click", (e) => {
    if (e.target.tagName === "INPUT") return;
    setFocused(tile);
  });

  tile.querySelector("input[type=checkbox]").addEventListener("change", (e) => {
    if (e.target.checked) selected.add(order.id);
    else selected.delete(order.id);
  });

  tile.querySelector(".act-invoice").onclick = (e) => {
    e.stopPropagation();
    post(`/gl/orders/${order.id}/print/invoice`).then(loadOrders);
  };
  tile.querySelector(".act-addressed").onclick = (e) => {
    e.stopPropagation();
    post(`/gl/orders/${order.id}/addressed`).then(loadOrders);
  };
  tile.querySelector(".act-bags").onclick = (e) => {
    e.stopPropagation();
    post(`/gl/orders/${order.id}/status/Bags%20Pulled`).then(loadOrders);
  };
  tile.querySelector(".act-ship").onclick = (e) => {
    e.stopPropagation();
    openShippingModal(order.id);
  };
  tile.querySelector(".act-label").onclick = (e) => {
    e.stopPropagation();
    post(`/gl/orders/${order.id}/print/label`).then(loadOrders);
  };
  tile.querySelector(".act-complete").onclick = (e) => {
    e.stopPropagation();
    post(`/gl/orders/${order.id}/status/Completed`).then(loadOrders);
  };

  return tile;
}

function setFocused(tile) {
  if (focusedTile) focusedTile.classList.remove("focused");
  focusedTile = tile;
  tile.classList.add("focused");
}

async function post(url) {
  return fetchJSON(url, { method: "POST" });
}

function getSelectedIds() {
  return Array.from(selected);
}

qs("#batch-print-invoices").onclick = async () => {
  await fetchJSON("/gl/orders/batch/print/invoices", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids: getSelectedIds() }),
  });
  loadOrders();
};

qs("#batch-print-labels").onclick = async () => {
  await fetchJSON("/gl/orders/batch/print/labels", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids: getSelectedIds() }),
  });
  loadOrders();
};

qs("#batch-advance").onclick = async () => {
  const status = qs("#batch-status").value;
  if (!status) return;
  await fetchJSON(`/gl/orders/batch/status/${encodeURIComponent(status)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids: getSelectedIds() }),
  });
  loadOrders();
};

qs("#refresh").onclick = loadOrders;

function focusById(id) {
  const tile = document.querySelector(`.tile[data-id="${id}"]`);
  if (tile) {
    tile.scrollIntoView({ behavior: "smooth", block: "center" });
    setFocused(tile);
  }
}

qs("#toggle-logs").onclick = () => {
  qs("#log-drawer").classList.add("open");
};
qs("#close-log").onclick = () => {
  qs("#log-drawer").classList.remove("open");
};

function renderLogs(entries) {
  const list = qs("#log-list");
  entries.reverse().forEach((e) => {
    const li = document.createElement("li");
    li.textContent = `[${e.ts}] ${e.topic} ${e.detail || ""}`;
    li.onclick = () => focusById(e.order_id);
    list.prepend(li);
    lastLogTs = e.ts;
  });
}

async function fetchLogs() {
  try {
    const data = await fetchJSON(
      `/gl/logs?since=${encodeURIComponent(lastLogTs)}&topic=&q=`
    );
    if (data.length) renderLogs(data);
  } catch (e) {}
}

document.addEventListener("keydown", (e) => {
  if (!focusedTile) return;
  const id = focusedTile.dataset.id;
  const key = e.key.toLowerCase();
  if (key === "p") post(`/gl/orders/${id}/print/invoice`).then(loadOrders);
  if (key === "a") post(`/gl/orders/${id}/addressed`).then(loadOrders);
  if (key === "b") post(`/gl/orders/${id}/status/Bags%20Pulled`).then(loadOrders);
  if (key === "m") openShippingModal(id);
  if (key === "l") post(`/gl/orders/${id}/print/label`).then(loadOrders);
  if (key === "c") post(`/gl/orders/${id}/status/Completed`).then(loadOrders);
});

async function openShippingModal(id) {
  shippingOrder = id;
  try {
    const opts = await fetchJSON(`/gl/orders/${id}/shipping/options`);
    const container = qs("#shipping-options");
    container.innerHTML = "";
    opts.forEach((o, idx) => {
      const label = document.createElement("label");
      label.innerHTML = `<input type="radio" name="ship" value="${idx}" ${
        o.rationale ? "checked" : ""
      }> ${o.carrier} ${o.service} $${o.cost.toFixed(2)} ETA ${o.eta_days}d ${
        o.rationale ? "(" + o.rationale + ")" : ""
      }`;
      container.appendChild(label);
    });
    qs("#shipping-modal").classList.remove("hidden");
  } catch (e) {}
}

qs("#approve-shipping").onclick = async () => {
  if (!shippingOrder) return;
  await post(`/gl/orders/${shippingOrder}/shipping/approve`);
  qs("#shipping-modal").classList.add("hidden");
  shippingOrder = null;
  loadOrders();
};

qs("#cancel-shipping").onclick = () => {
  qs("#shipping-modal").classList.add("hidden");
  shippingOrder = null;
};

loadOrders();
fetchLogs();
setInterval(loadOrders, 3000);
setInterval(fetchLogs, 3000);
