# Gmail Invoice Intake

Backup path for pulling order invoices from Gmail when the primary Volusion API is unavailable.

## Setup

1. Create OAuth credentials and store `client_secret.json` and `token.json` under `./secrets/`.
2. Copy `.env.example` to `.env` and adjust values.
3. Install dependencies and run `scripts/dev_setup.sh`.
4. Run a single poll:

```bash
python -m graniteledger.integrations.gmail_intake.cli once
```

## Testing

Run unit tests with:

```bash
pytest tests/integrations/gmail_intake -q
```

## Notes

This module implements polling and basic push handling. Attachment parsing supports PDF and CSV invoices and posts normalized envelopes to the GraniteLedger intake endpoint using HMAC authentication.
