#!/bin/bash
# One-time setup: a private Python environment in this folder, plus the headless browser the finance pipeline uses.
set -e
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
"$PY" -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10 or newer is needed (found %s)" % sys.version.split()[0]'
"$PY" -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements-demo.txt
.venv/bin/python -m playwright install chromium
echo "Setup done. Start the demo with: ./start.sh"
