# GraniteLedger

Modular order-processing demo built on ForgeCore.

## Runbook

### Install

```bash
pip install -r requirements.txt
```

### Run

```bash
python run.py
```

Then open <http://127.0.0.1:8765/gl/ui> for the operator dashboard.

### Batch examples

```bash
curl -X POST http://127.0.0.1:8765/gl/orders/batch/print/invoices \
  -H 'Content-Type: application/json' \
  -d '{"ids":["o1","o2"]}'

curl -X POST http://127.0.0.1:8765/gl/orders/batch/print/labels \
  -H 'Content-Type: application/json' \
  -d '{"ids":["o1","o2"]}'

curl -X POST http://127.0.0.1:8765/gl/orders/batch/status/Printed \
  -H 'Content-Type: application/json' \
  -d '{"ids":["o1","o2"]}'
```

### Log filters

`GET /gl/logs?topic=&q=&since=` allows filtering by topic, free-text (`q`), and timestamp (`since`).

### Environment

Setting `VOLUSION_SYNC_URL` will enable the optional completion sync webhook.

## Testing

```bash
pytest -q
```
