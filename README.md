# GraniteLedger

Modular order-processing demo built on ForgeCore.

## Setup

```bash
pip install -r requirements.txt
```

## Running

```bash
python run.py
# open http://127.0.0.1:8765/gl/ui
```

## Test helpers

The runtime exposes a few helpers:

- `POST /gl/test/order` – create a test order
- `POST /gl/test/print` – print an invoice for the most recent test order
- `POST /gl/test/ship` – approve shipping and buy/print the label for the most recent test order

## Batch examples

```bash
curl -X POST http://127.0.0.1:8765/gl/orders/batch/print/invoices -d '{"ids":["a","b"]}' -H 'Content-Type: application/json'
curl -X POST http://127.0.0.1:8765/gl/orders/batch/status -d '{"ids":["a"],"status":"Completed"}' -H 'Content-Type: application/json'
```

## Artifacts

Invoices and labels are written under `modules/printing_service/_storage` in `invoices/<id>/` and `labels/<id>/`.

## Notes

- No package or folder named `fastapi` exists to avoid import shadowing.
- Setting `VOLUSION_SYNC_URL` will POST a minimal JSON payload on `order.completed`; otherwise a `volusion.sync.skipped` event is logged.

## Testing

```bash
pytest -q
```
