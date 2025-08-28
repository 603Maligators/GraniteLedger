#!/bin/bash
set -e
python -m venv .venv
action="install"
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env 2>/dev/null || true
