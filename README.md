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

Open the dashboard at [http://127.0.0.1:8765/gl/ui](http://127.0.0.1:8765/gl/ui).

Helpful test endpoints:

```bash
curl -XPOST http://127.0.0.1:8765/gl/test/order
curl -XPOST http://127.0.0.1:8765/gl/test/print
curl -XPOST http://127.0.0.1:8765/gl/test/ship
```

Batch routes:

```bash
curl -XPOST http://127.0.0.1:8765/gl/orders/batch/print/invoices -d '{"ids":["1"]}'
curl -XPOST http://127.0.0.1:8765/gl/orders/batch/status -d '{"ids":["1"],"status":"Completed"}'
```

Printed invoices and labels are saved under `modules/printing_service/_storage/`.

Note: avoid creating any folder named `fastapi` to prevent import shadowing.

## Testing

```bash
pytest -q
```
