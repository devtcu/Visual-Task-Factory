"""One-instance OpenRouter pilot. Sends only the public puzzle and piece sheet."""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import os
import random
import time
import urllib.error
import urllib.request
from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

from score import score

ROOT = Path(__file__).resolve().parent
RUN = ROOT / "runs" / "level3_square_520"
MODELS = ["anthropic/claude-haiku-5.5", "openai/gpt-6-luna"]


def _data_url(path):
    raw = path.read_bytes()
    mime = "image/png"
    if len(raw) > 4_500_000:
        image = Image.open(path).convert("RGB")
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=90, optimize=True)
        raw = buffer.getvalue()
        mime = "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii"), raw, mime


def _request(model, prompt, puzzle_url, sheet_url, key, max_tokens, reasoning_effort):
    payload = {"model": model, "temperature": 0, "max_completion_tokens": max_tokens,
               "reasoning": {"effort": reasoning_effort},
               "messages": [{"role": "user", "content": [
                   {"type": "text", "text": prompt},
                   {"type": "image_url", "image_url": {"url": puzzle_url}},
                   {"type": "image_url", "image_url": {"url": sheet_url}},
               ]}]}
    body = json.dumps(payload).encode("utf8")
    for attempt in range(4):
        req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body,
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + key,
                     "HTTP-Referer": "https://github.com/Jay-Raval-19/visionforge",
                     "X-Title": "Spatial Reconstruction Benchmark Pilot"})
        try:
            with urllib.request.urlopen(req, timeout=300) as response:
                return json.loads(response.read().decode("utf8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (408, 429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(min(30, 2 ** attempt + random.random()))
                continue
            # Provider error bodies may reflect request details; keep them out of
            # the console and store only a short status/message in our record.
            message = exc.read(1000).decode("utf8", "replace")
            raise RuntimeError(f"OpenRouter HTTP {exc.code}: {message[:350]}") from None
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == 3:
                raise RuntimeError(f"OpenRouter transport error: {type(exc).__name__}") from None
            time.sleep(2 ** attempt)


def _extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text[:-3].strip()
    return json.loads(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, default=RUN)
    ap.add_argument("--max-tokens", type=int, default=16384)
    ap.add_argument("--reasoning-effort", choices=("low", "medium", "high"), default="high")
    ap.add_argument("--models", nargs="+", default=MODELS)
    args = ap.parse_args()
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("Set OPENROUTER_API_KEY in the environment; no key is read from files or printed.")

    task = json.loads((args.run / "public" / "task.json").read_text(encoding="utf8"))
    prompt = task["instruction"] + "\n\nUse the first image as the masked original and the second as the shuffled candidate sheet. Return only the requested JSON array."
    puzzle_url, puzzle_bytes, puzzle_mime = _data_url(args.run / task["image"])
    sheet_url, sheet_bytes, sheet_mime = _data_url(args.run / task["candidate_sheet"])
    prompt_hash = hashlib.sha256(prompt.encode("utf8")).hexdigest()
    out = args.run / "results"
    (out / "predictions").mkdir(parents=True, exist_ok=True)
    attempts_path = out / "attempts.jsonl"
    prior = [json.loads(x) for x in attempts_path.read_text(encoding="utf8").splitlines() if x.strip()] if attempts_path.exists() else []
    records = []
    for model in args.models:
        attempt_no = 1 + sum(r.get("model") == model for r in prior)
        record = {"task_id": task["task_id"], "model": model, "attempt": attempt_no, "prompt": prompt,
                  "prompt_sha256": prompt_hash, "temperature": 0,
                  "max_completion_tokens": args.max_tokens, "reasoning_effort": args.reasoning_effort, "status": "error",
                  "finish_reason": None, "raw_response": "", "parsed": None,
                  "score": None, "error": None,
                  "puzzle_sha256": hashlib.sha256(puzzle_bytes).hexdigest(), "puzzle_mime": puzzle_mime,
                  "candidate_sheet_sha256": hashlib.sha256(sheet_bytes).hexdigest(), "candidate_sheet_mime": sheet_mime,
                  "timestamp": datetime.now(timezone.utc).isoformat()}
        try:
            started = time.perf_counter()
            response = _request(model, prompt, puzzle_url, sheet_url, key, args.max_tokens, args.reasoning_effort)
            choice = response["choices"][0]
            content = choice["message"].get("content") or ""
            record["latency_ms"] = round((time.perf_counter() - started) * 1000)
            record["finish_reason"] = choice.get("finish_reason")
            record["raw_response"] = content
            record["usage"] = response.get("usage")
            record["status"] = "ok" if record["finish_reason"] == "stop" else "incomplete"
            try:
                parsed = _extract_json(content)
                record["parsed"] = parsed
                pred_path = args.run / "results" / "predictions" / (model.replace("/", "__") + ".json")
                pred_path.write_text(json.dumps(parsed, indent=2), encoding="utf8")
                scores, reconstruction = score(pred_path, args.run)
                scores["prediction_file"] = str(pred_path.relative_to(args.run))
                record["score"] = scores
                reconstruction.save(args.run / "results" / (model.replace("/", "__") + "_reconstruction.png"))
            except (json.JSONDecodeError, ValueError, KeyError) as exc:
                if record["status"] == "ok":
                    record["status"] = "unparsed"
                record["error"] = f"answer_parse_or_score: {type(exc).__name__}: {exc}"[:500]
        except Exception as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"[:500]
        records.append(record)
        with attempts_path.open("a", encoding="utf8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"{model}: {record['status']}; finish={record['finish_reason']}")

    all_records = prior + records
    (out / "responses.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in all_records), encoding="utf8")
    fields = ["model", "task_id", "status", "finish_reason", "score", "error", "latency_ms"]
    with (out / "scores.csv").open("w", newline="", encoding="utf8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in all_records:
            writer.writerow({k: json.dumps(r[k], ensure_ascii=False) if k == "score" else r.get(k) for k in fields})
    final = {}
    for r in all_records:
        if r.get("status") == "ok" and r.get("finish_reason") == "stop" and r.get("score") is not None:
            final[r["model"]] = r
    with (out / "final_scores.csv").open("w", newline="", encoding="utf8") as f:
        final_fields = ["model", "task_id", "status", "finish_reason", "score", "latency_ms"]
        writer = csv.DictWriter(f, fieldnames=final_fields); writer.writeheader()
        for r in final.values():
            writer.writerow({k: json.dumps(r[k], ensure_ascii=False) if k == "score" else r.get(k) for k in final_fields})
    config = {"provider": "openrouter", "models": args.models, "temperature": 0,
              "reasoning_effort": args.reasoning_effort, "max_completion_tokens": args.max_tokens,
              "images_sent": [{"file": task["image"], "mime": puzzle_mime},
                              {"file": task["candidate_sheet"], "mime": sheet_mime}],
              "answer_key_sent": False, "prompt_sha256": prompt_hash}
    (out / "evaluation_config.json").write_text(json.dumps(config, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
