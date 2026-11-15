from pathlib import Path
import os

def load_dotenv():
    """Load optional evaluator .env from the handoff root without overriding process vars."""
    path=Path(__file__).resolve().parents[2]/".env"
    if not path.exists(): return
    for line in path.read_text(encoding="utf-8").splitlines():
        line=line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        key,value=line.split("=",1)
        key=key.strip(); value=value.strip().strip("\"").strip("'")
        if key and key not in os.environ: os.environ[key]=value
