#!/bin/bash
set -e
python -m graniteledger.integrations.gmail_intake.cli watch --register "$@"
