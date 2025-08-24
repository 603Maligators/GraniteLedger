const columns = ["New","Printed","Addressed","Bags Pulled","Ship Method Chosen","Shipped","Completed"];
let orders = [];
let focusedId = null;
let logSince = null;

async function loadOrders(){
  const res = await fetch('/gl/orders');
  orders = await res.json();
  renderBoard();
}

function tileTemplate(o){
  const last = o.history[o.history.length-1];
  const div = document.createElement('div');
  div.className='tile';
  div.id = `tile-${o.id}`;
  div.innerHTML = `
    <input type="checkbox" class="sel" data-id="${o.id}" />
    <span class="oid">${o.id}</span>
    <span class="buyer">${o.buyer?.name||''}</span>
    <div class="meta">${o.computed_weight||''} lb / ${o.shipping_tier} / ${o.destination.zip}</div>
    <div class="meta">${summary(o)}</div>
    <div class="meta">Tracking: ${o.tracking_number||''}</div>
    <div class="meta">${last?last.event:''} @ ${last?last.ts:''}</div>
    <div class="actions">
      <button onclick="printInvoice('${o.id}')">Invoice</button>
      <button onclick="markAddressed('${o.id}')">Addressed</button>
      <button onclick="bagsPulled('${o.id}')">Bags</button>
      <button onclick="approveShipping('${o.id}')">Approve</button>
      <button onclick="buyLabel('${o.id}')">Label</button>
      <button onclick="complete('${o.id}')">Complete</button>
    </div>`;
  div.onclick = ()=>{focusedId=o.id;};
  return div;
}

function summary(o){
  if(o.approved_shipping_method){
    const m=o.approved_shipping_method;return `${m.carrier} ${m.service}`;
  }
  if(o.proposed_shipping_method){
    const m=o.proposed_shipping_method;return `Proposed: ${m.carrier} ${m.service}`;
  }
  return '';
}

function renderBoard(){
  const board=document.getElementById('board');
  board.innerHTML='';
  columns.forEach(col=>{
    const c=document.createElement('div');
    c.className='column';
    c.innerHTML=`<h3>${col}</h3>`;
    board.appendChild(c);
  });
  orders.forEach(o=>{
    const colDiv=[...board.children].find(c=>c.querySelector('h3').innerText===o.status);
    if(colDiv) colDiv.appendChild(tileTemplate(o));
  });
}

async function printInvoice(id){await fetch(`/gl/orders/${id}/print/invoice`,{method:'POST'});loadOrders();}
async function markAddressed(id){await fetch(`/gl/orders/${id}/addressed`,{method:'POST'});loadOrders();}
async function bagsPulled(id){await fetch(`/gl/orders/${id}/status/Bags%20Pulled`,{method:'POST'});loadOrders();}
async function buyLabel(id){await fetch(`/gl/orders/${id}/print/label`,{method:'POST'});loadOrders();}
async function complete(id){await fetch(`/gl/orders/${id}/status/Completed`,{method:'POST'});loadOrders();}

// shipping modal
let modalId=null;
document.getElementById('approveShipBtn').onclick=async()=>{
  const sel=document.querySelector('#shippingOptions input[name=shipopt]:checked');
  if(sel){await fetch(`/gl/orders/${modalId}/shipping/approve`,{method:'POST'});}
  closeModal();loadOrders();
};
document.getElementById('closeShip').onclick=closeModal;
function closeModal(){document.getElementById('shippingModal').classList.add('hidden');}
async function approveShipping(id){
  modalId=id;
  const res=await fetch(`/gl/orders/${id}/shipping/options`);
  const opts=await res.json();
  const box=document.getElementById('shippingOptions');
  box.innerHTML='';
  opts.forEach((o,i)=>{
    const div=document.createElement('div');
    div.innerHTML=`<label><input type="radio" name="shipopt" value="${i}" ${o.rationale?'checked':''}/> ${o.carrier} ${o.service} $${o.cost} (${o.eta_days}d) <em>${o.rationale}</em></label>`;
    box.appendChild(div);
  });
  document.getElementById('shippingModal').classList.remove('hidden');
}

// batch operations
function selectedIds(){return Array.from(document.querySelectorAll('.sel:checked')).map(cb=>cb.dataset.id);}
document.getElementById('batch-invoices').onclick=async()=>{
  const ids=selectedIds();
  if(ids.length) await fetch('/gl/orders/batch/print/invoices',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ids})});
  loadOrders();
};
document.getElementById('batch-labels').onclick=async()=>{
  const ids=selectedIds();
  if(ids.length) await fetch('/gl/orders/batch/print/labels',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ids})});
  loadOrders();
};
document.getElementById('batch-status').onclick=async()=>{
  const ids=selectedIds();
  const status=document.getElementById('batch-status-select').value;
  if(ids.length) await fetch('/gl/orders/batch/status',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ids,status})});
  loadOrders();
};

document.getElementById('refresh').onclick=loadOrders;

// logs
async function loadLogs(){
  let url='/gl/logs';
  if(logSince) url+=`?since=${logSince}`;
  const res=await fetch(url);
  const data=await res.json();
  if(data.length){logSince=data[0].ts;}
  const logDiv=document.getElementById('logs');
  data.forEach(e=>{
    const row=document.createElement('div');
    row.className='log';
    row.innerText=`${e.ts} ${e.topic} ${e.detail||''}`;
    row.onclick=()=>{const t=document.getElementById('tile-'+e.order_id);if(t) t.scrollIntoView();};
    logDiv.prepend(row);
  });
}
setInterval(loadLogs,3000);

document.getElementById('toggle-logs').onclick=()=>{
  document.getElementById('logDrawer').classList.toggle('hidden');
};

// shortcuts
document.addEventListener('keydown',e=>{
  if(!focusedId) return;
  const k=e.key.toUpperCase();
  if(k==='P') printInvoice(focusedId);
  if(k==='A') markAddressed(focusedId);
  if(k==='B') bagsPulled(focusedId);
  if(k==='M') approveShipping(focusedId);
  if(k==='L') buyLabel(focusedId);
  if(k==='C') complete(focusedId);
});

loadOrders();
