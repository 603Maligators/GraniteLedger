# GraniteLedger

Modular order-processing demo built on ForgeCore.

## Setup

```bash
pip install -r requirements.txt
```

## Running

```bash
python run.py
```

This starts the ForgeCore runtime and serves the admin API and GraniteLedger routes.
Open http://localhost:8765/gl/ui for the dashboard.

## Testing

```bash
pytest -q
```

## Example API usage

Create an order:

```bash
curl -X POST http://localhost:8765/gl/orders \
  -H 'Content-Type: application/json' \
  -d '{"id":"1","buyer":{"name":"Alice"},"destination":{"zip":"03224","city":"X","state":"NH"},"items":[{"sku":"SKU1","name":"Thing","qty":1,"weight":1.0}]}'
```

Poll the order until `computed_weight` is populated:

```bash
curl http://localhost:8765/gl/orders/1
```

Print and progress:

```bash
curl -X POST http://localhost:8765/gl/orders/1/print/invoice
curl -X POST http://localhost:8765/gl/orders/1/addressed
curl -X POST http://localhost:8765/gl/orders/1/status/Bags%20Pulled
curl http://localhost:8765/gl/orders/1/shipping/options
curl -X POST http://localhost:8765/gl/orders/1/shipping/approve -H 'Content-Type: application/json' -d '{"carrier":"USPS","service":"Priority","cost":8.5,"eta_days":2,"rationale":"fast"}'
curl -X POST http://localhost:8765/gl/orders/1/print/label
curl -X POST http://localhost:8765/gl/orders/1/status/Completed
```

Batch operations accept a JSON array of order IDs:

```bash
curl -X POST http://localhost:8765/gl/orders/batch/print/invoices -d '["1","2"]' -H 'Content-Type: application/json'
curl -X POST http://localhost:8765/gl/orders/batch/status/Printed -d '["1","2"]' -H 'Content-Type: application/json'
```

Logs:

```bash
curl 'http://localhost:8765/gl/logs?topic=order.&q=printed&since=2024-01-01T00:00:00'
```

If the environment variable `VOLUSION_SYNC_URL` is set, order completion will POST to that URL.

Creating an order is eventually consistent for shipping details; the dashboard polls until updated.
