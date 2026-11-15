#!/bin/bash
# Start the Team 6 demo. The OpenRouter key is read from the environment, or typed in here (hidden, never saved).
cd "$(dirname "$0")"
if [ -z "$OPENROUTER_API_KEY" ]; then
  echo -n "OpenRouter API key (hidden; press Enter to skip model calls): "
  read -s OPENROUTER_API_KEY; echo
  export OPENROUTER_API_KEY
fi
exec .venv/bin/python app.py
