"""OpenRouter evaluation with complete-response checks and auditable caching."""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import time

import requests
from eval.scoring import parse_answer, score_answer

MODELS = ["anthropic/claude-haiku-5.5", "openai/gpt-6-luna"]
URL = "https://openrouter.ai/api/v1/chat/completions"
RESPONSE_INSTRUCTIONS = ("Solve the task using only the supplied question and image(s). You may reason before answering. "
                         "End with FINAL ANSWER: followed by the requested scalar or a JSON array for a sequence. "
                         "For a spatial reconstruction use the JSON array of placement objects specified in the question.")


def dump(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def redact(text):
    text = re.sub(r"sk-(?:or-|ant-)?[A-Za-z0-9_-]{12,}", "[REDACTED]", str(text))
    key = os.environ.get("OPENROUTER_API_KEY")
    return text.replace(key, "[REDACTED]") if key else text


def input_record(task, folder, model, config):
    files = task.get("images") or [task["image"]]
    public = {"model": model, "question": task["question"], "response_instructions": RESPONSE_INSTRUCTIONS,
              "images": [{"path": p, "sha256": hashlib.sha256((folder / p).read_bytes()).hexdigest()} for p in files],
              "settings": config}
    digest = hashlib.sha256(json.dumps(public, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return public, digest


def request_one(task, folder, model, config, result_dir, force=False):
    public, digest = input_record(task, folder, model, config)
    stem = f"{model.replace('/', '__')}__{task['task_id']}__{digest[:16]}"
    rawpath = result_dir / "raw" / (stem + ".json")
    if rawpath.exists() and not force:
        saved = json.loads(rawpath.read_text(encoding="utf-8"))
        if saved.get("fingerprint") == digest and saved.get("complete") is True:
            return saved
    if rawpath.exists():
        archive = result_dir / "raw" / "archive" / f"{stem}.{time.time_ns()}.json"
        archive.parent.mkdir(parents=True, exist_ok=True)
        rawpath.rename(archive)
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key: raise RuntimeError("OPENROUTER_API_KEY is required at runtime")
    content = [{"type": "text", "text": task["question"]}]
    for i, item in enumerate(public["images"], 1):
        path = folder / item["path"]
        mime = mimetypes.guess_type(path.name)[0] or "image/png"
        if len(public["images"]) > 1:
            content.append({"type": "text", "text": f"Image {i}:"})
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}})
    body = {"model": model, "messages": [{"role": "system", "content": RESPONSE_INSTRUCTIONS},
                                           {"role": "user", "content": content}], **config}
    attempts = []; start = time.monotonic()
    for attempt in range(1, 6):
        try:
            response = requests.post(URL, headers={"Authorization": "Bearer " + key}, json=body, timeout=(30, 900))
            if response.status_code != 200:
                message = redact(response.text[:2000]); retry = response.status_code in (408, 429, 500, 502, 503, 504, 529)
                attempts.append({"attempt": attempt, "status": response.status_code, "error": message})
                if retry and attempt < 5:
                    time.sleep(min(30, 2 ** attempt)); continue
                raise RuntimeError(f"OpenRouter HTTP {response.status_code}: {message}")
            raw = response.json()
            if "error" in raw: raise RuntimeError(redact(raw["error"]))
            if raw.get("model") and raw["model"] != model:
                raise RuntimeError(f"Requested {model} but provider reported {raw['model']}; verify the route before counting this response")
            choice = raw["choices"][0]
            reply = choice["message"].get("content") or ""
            finish = choice.get("finish_reason")
            complete = finish == "stop" and isinstance(reply, str) and bool(reply.strip())
            saved = {"fingerprint": digest, "task_id": task["task_id"], "requested_model": model,
                     "public_input": public, "complete": complete, "finish_reason": finish,
                     "response": reply, "raw_response": raw, "attempts": attempts,
                     "wall_seconds": round(time.monotonic() - start, 3)}
            dump(rawpath, saved)
            if not complete:
                raise RuntimeError(f"Incomplete response for {task['task_id']}/{model}: finish_reason={finish!r}. Fix settings and rerun every task.")
            return saved
        except (requests.Timeout, requests.ConnectionError) as exc:
            attempts.append({"attempt": attempt, "error": redact(exc)})
            if attempt < 5: time.sleep(min(30, 2 ** attempt)); continue
            dump(result_dir / "errors" / (stem + ".json"), {"fingerprint": digest, "attempts": attempts})
            raise RuntimeError(f"API retries exhausted for {task['task_id']}/{model}") from exc
        except Exception as exc:
            dump(result_dir / "errors" / (stem + ".json"), {"fingerprint": digest, "attempts": attempts, "error": redact(exc)})
            raise


def evaluate(task_dir, results_dir, models=None, max_tokens=32768, workers=2, force=False):
    task_dir, results_dir = Path(task_dir), Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    tasks = [json.loads(line) for line in (task_dir / "tasks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if any(t.get("checks", {}).get("passed") is not True for t in tasks): raise RuntimeError("Refusing to evaluate invalid tasks")
    models = models or MODELS
    # A failed rerun must not leave an older successful dataset beside a new configuration.
    published = ("responses.jsonl", "summary.json", "run_config.json", "scoring_details.json", "incomplete_run.json")
    previous = [results_dir / name for name in published if (results_dir / name).exists()]
    if previous:
        history = results_dir / "history" / f"run_{time.time_ns()}"
        history.mkdir(parents=True, exist_ok=True)
        for path in previous:
            path.rename(history / f"{path.stem}.previous{path.suffix}")
    config = {"temperature": 0, "reasoning": {"effort": "high"}, "max_tokens": max_tokens}
    registry = []
    try:
        response = requests.get("https://openrouter.ai/api/v1/models", timeout=30); response.raise_for_status()
        registry = [{k: m.get(k) for k in ("id", "supported_parameters", "context_length", "pricing")} for m in response.json()["data"] if m["id"] in models]
        if {m["id"] for m in registry} != set(models): raise RuntimeError("A requested model ID is unavailable")
    except requests.RequestException as exc:
        raise RuntimeError("Could not verify required OpenRouter model IDs") from exc
    run_config = {"models": models, **config, "endpoint": URL, "prompt_template": {"system": RESPONSE_INSTRUCTIONS, "user": "Exact task.question, followed by the task images in order"},
                  "input_mode": "task.images when present, otherwise task.image", "model_registry": registry,
                  "temperature_note": "temperature=0 is sent to OpenRouter for both models. Registry supported_parameters may omit temperature; the response does not attest provider enforcement.",
                  "scoring": "eval/scoring.py; reconstruction delegates to validate/visual_reconstruction/scoring.py",
                  "cache_key": "SHA-256 of exact question, image bytes, model, response instructions and requested settings"}
    dump(results_dir / "run_config.json", run_config)
    jobs = [(m, task) for m in models for task in tasks]
    rows = []; details = {}; failures = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(request_one, t, task_dir, m, config, results_dir, force): (m, t) for m, t in jobs}
        for future in as_completed(futures):
            model, task = futures[future]
            try:
                saved = future.result()
                parsed = parse_answer(saved["response"], task)
                scored = score_answer(task, parsed, task_dir)
                rows.append({"model": model, "task_id": task["task_id"], "status": "ok", "parsed": parsed if parsed is not None else "",
                             "question_type": task["question_type"], "response": saved["response"], "ref_answer": task["answer"],
                             "correct": int(bool(scored["correct"])), "finish_reason": "stop", "error": ""})
                details[f"{model}/{task['task_id']}"] = scored
                print(f"EVAL {model} {task['task_id']}: {'CORRECT' if scored['correct'] else 'INCORRECT'}", flush=True)
            except Exception as exc:
                failures.append({"model": model, "task_id": task["task_id"], "error": redact(exc)})
                print(f"EVAL INCOMPLETE {model} {task['task_id']}: {redact(exc)}", flush=True)
    order = {(m, t["task_id"]): i for i, (m, t) in enumerate(jobs)}
    rows.sort(key=lambda row: order[(row["model"], row["task_id"])])
    dump(results_dir / "scoring_details.json", details)
    if failures:
        dump(results_dir / "incomplete_run.json", {"complete_rows": len(rows), "required_rows": len(jobs), "failures": failures})
        raise RuntimeError(f"{len(failures)} incomplete evaluations; final responses file was not written")
    (results_dir / "responses.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    summary = {m: {"correct": sum(r["correct"] for r in rows if r["model"] == m), "total": sum(r["model"] == m for r in rows)} for m in models}
    dump(results_dir / "summary.json", {"models": summary, "n_tasks": len(tasks), "complete_rows": len(rows), "all_responses_complete": True})
    print(json.dumps(summary, indent=2), flush=True)
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--tasks", required=True); parser.add_argument("--results", required=True)
    parser.add_argument("--model", action="append", choices=MODELS); parser.add_argument("--max-tokens", type=int, default=32768)
    parser.add_argument("--workers", type=int, default=2); parser.add_argument("--force", action="store_true")
    args = parser.parse_args(); evaluate(args.tasks, args.results, args.model, args.max_tokens, args.workers, args.force)
