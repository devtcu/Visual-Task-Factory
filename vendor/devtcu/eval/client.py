"""One OpenRouter chat call with an image. Retries 429/5xx/timeouts with backoff. Key comes from the environment only."""
import base64, json, os, time
import requests

URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS = ["anthropic/claude-haiku-5.5", "openai/gpt-6-luna"]
CONFIG = {"temperature": 0, "max_tokens": 32000, "reasoning": {"effort": "high"}, "timeout_s": 600, "max_retries": 6}
PROMPT_TEMPLATE = ("{question}\n\nLook at the image carefully. You may reason step by step. "
                   "Finish with one last line in exactly this form:\nFINAL ANSWER: <your answer>")


def build_messages(question, image_path=None):
    """image_path: one PNG path, a list of paths (several views of one scene, sent in order), or None (blind run)."""
    content = [{"type": "text", "text": PROMPT_TEMPLATE.format(question=question)}]
    for path in ([image_path] if isinstance(image_path, str) else image_path or []):
        b64 = base64.b64encode(open(path, "rb").read()).decode()
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})
    return [{"role": "user", "content": content}]


def call(model, question, image_path=None, config=None):
    """Returns {status, response, finish_reason, error, usage, raw}. status is 'ok' only for a complete reply."""
    cfg = {**CONFIG, **(config or {})}
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("Set OPENROUTER_API_KEY in the environment.")
    body = {"model": model, "messages": build_messages(question, image_path), "temperature": cfg["temperature"],
            "max_tokens": cfg["max_tokens"], "reasoning": cfg["reasoning"]}
    last = ""
    for attempt in range(cfg["max_retries"]):
        try:
            r = requests.post(URL, headers={"Authorization": f"Bearer {key}"}, json=body, timeout=cfg["timeout_s"])
            if r.status_code == 429 or r.status_code >= 500:
                last = f"http {r.status_code}: {r.text[:200]}"
                time.sleep(min(60, 2 ** attempt * 2)); continue
            raw = r.json()
            if r.status_code != 200 or "error" in raw:
                err = raw.get("error", {})
                last = f"http {r.status_code}: {json.dumps(err)[:300]}"
                if isinstance(err, dict) and err.get("code") in (408, 429, 500, 502, 503, 504, 529):
                    time.sleep(min(60, 2 ** attempt * 2)); continue
                return {"status": "api_error", "response": "", "finish_reason": "", "error": last, "usage": {}, "raw": raw}
            choice = raw["choices"][0]
            text = choice["message"].get("content") or ""
            finish = choice.get("finish_reason") or ""
            if finish == "stop" and text.strip():
                return {"status": "ok", "response": text, "finish_reason": finish, "error": "", "usage": raw.get("usage", {}), "raw": raw}
            if finish == "length":
                return {"status": "truncated", "response": text, "finish_reason": finish, "error": "cut off by max_tokens", "usage": raw.get("usage", {}), "raw": raw}
            last = f"finish_reason={finish!r}, empty={not text.strip()}"
            time.sleep(min(60, 2 ** attempt * 2))
        except (requests.Timeout, requests.ConnectionError, ValueError) as e:
            last = f"{type(e).__name__}: {e}"
            time.sleep(min(60, 2 ** attempt * 2))
    return {"status": "api_error", "response": "", "finish_reason": "", "error": last or "retries exhausted", "usage": {}, "raw": {}}
