const statuses = ["New","Printed","Addressed","Bags Pulled","Ship Method Chosen","Shipped","Completed"];
let orders = [];
let selected = new Set();

async function fetchOrders(){
  const res = await fetch('/gl/orders');
  orders = await res.json();
  render();
}

function render(){
  const board = document.getElementById('board');
  board.innerHTML='';
  statuses.forEach(st=>{
    const col = document.createElement('div');
    col.className='col';
    col.dataset.status=st;
    const h=document.createElement('h2');h.textContent=st;col.appendChild(h);
    board.appendChild(col);
  });
  orders.forEach(o=>{
    const col = board.querySelector(`.col[data-status="${o.status}"]`);
    if(!col)return;
    const tile=document.createElement('div');
    tile.className='tile';
    tile.innerHTML=`<input type="checkbox" class="sel" data-id="${o.id}">`+
      `<div class="info">#${o.id} ${o.buyer.name} (${o.destination.zip})<br>`+
      `wt:${o.computed_weight||''} tier:${o.shipping_tier}`+
      (o.tracking_number?`<br>trk:${o.tracking_number}`:'')+
      `</div>`;
    const actions=document.createElement('div');actions.className='actions';
    function btn(text, fn){const b=document.createElement('button');b.textContent=text;b.onclick=fn;actions.appendChild(b);}
    if(o.status==="New") btn('Print Invoice',()=>doAction(`/gl/orders/${o.id}/print/invoice`));
    if(o.status==="Printed") btn('Addressed',()=>doAction(`/gl/orders/${o.id}/addressed`));
    if(o.status==="Addressed") btn('Bags Pulled',()=>doAction(`/gl/orders/${o.id}/status/Bags%20Pulled`));
    if(o.status==="Bags Pulled") btn('Approve Ship',()=>approveShipping(o.id));
    if(o.status==="Ship Method Chosen") btn('Buy Label',()=>doAction(`/gl/orders/${o.id}/print/label`));
    if(o.status==="Shipped") btn('Complete',()=>doAction(`/gl/orders/${o.id}/status/Completed`));
    tile.appendChild(actions);
    col.appendChild(tile);
  });
  document.querySelectorAll('.sel').forEach(cb=>cb.onchange=()=>{
    if(cb.checked) selected.add(cb.dataset.id); else selected.delete(cb.dataset.id);
  });
}

async function doAction(url, method='POST'){
  await fetch(url,{method});
  fetchOrders();
}

async function approveShipping(id){
  const res = await fetch(`/gl/orders/${id}/shipping/approve`,{method:'POST'});
  if(res.ok) fetchOrders();
}

// batch operations
async function batchPrint(){
  if(selected.size===0)return;
  await fetch('/gl/orders/batch/print/invoices',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ids:[...selected]})});
  fetchOrders();
}
async function batchLabel(){
  if(selected.size===0)return;
  await fetch('/gl/orders/batch/print/labels',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ids:[...selected]})});
  fetchOrders();
}
async function batchStatus(){
  const st=document.getElementById('batch-status').value;
  if(!st||selected.size===0)return;
  await fetch('/gl/orders/batch/status',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ids:[...selected],status:st})});
  fetchOrders();
}

// log drawer poll
async function pollLogs(){
  const res=await fetch('/gl/logs');
  const logs=await res.json();
  const cont=document.getElementById('logs');
  cont.innerHTML='';
  logs.forEach(l=>{
    const div=document.createElement('div');
    div.textContent=`${l.ts} ${l.topic} ${l.detail||''}`;
    cont.appendChild(div);
  });
}
setInterval(pollLogs,3000);

// bindings
window.onload=()=>{
  document.getElementById('refresh').onclick=fetchOrders;
  document.getElementById('batch-print').onclick=batchPrint;
  document.getElementById('batch-label').onclick=batchLabel;
  document.getElementById('batch-status').onchange=batchStatus;
  fetchOrders();
  pollLogs();
}
