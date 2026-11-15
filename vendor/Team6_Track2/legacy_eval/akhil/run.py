"""Evaluate both models on a task folder and write the results folder (responses.csv, run_config.json, raw/)."""
import csv, json, os, sys
from concurrent.futures import ThreadPoolExecutor
from . import client, score

COLUMNS = ["model", "task_id", "status", "parsed", "question_type", "response", "ref_answer", "correct", "finish_reason", "error",
           "fingerprint", "tokens"]


def load_tasks(task_dir):
    with open(os.path.join(task_dir, "tasks.jsonl"), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def ask(model, task, task_dir, raw_dir, with_image=True, config=None):
    """One model, one task. Cached on disk so the same call is never paid for twice."""
    tag = "" if with_image else ".blind"
    path = os.path.join(raw_dir, f"{model.replace('/', '__')}__{task['task_id']}{tag}.json")
    if os.path.exists(path):
        out = json.load(open(path, encoding="utf-8"))
        if out.get("status") == "ok":
            return out
    image = [os.path.join(task_dir, p) for p in task.get("images", [task["image"]])] if with_image else None
    out = client.call(model, task["question"], image, config)
    os.makedirs(raw_dir, exist_ok=True)
    json.dump(out, open(path, "w", encoding="utf-8"), indent=1)
    return out


def fingerprint(parsed, task, correct):
    """Called shot: which predicted mistake (trap) a wrong answer matches, using the task's own tolerance."""
    if correct or parsed == "":
        return ""
    for name, value in task.get("traps", {}).items():
        if score.is_correct(parsed, {**task, "answer": value}):
            return f"predicted:{name}"
    return "unpredicted"


def row(model, task, out):
    parsed = score.extract(out["response"], task) if out["status"] == "ok" else ""
    correct = score.is_correct(parsed, task) if out["status"] == "ok" else 0
    return {"model": model, "task_id": task["task_id"], "status": out["status"], "parsed": parsed,
            "question_type": task.get("question_type", ""), "response": out["response"],
            "ref_answer": json.dumps(task["answer"]) if isinstance(task["answer"], list) else task["answer"],
            "correct": correct, "finish_reason": out["finish_reason"], "error": out["error"],
            "fingerprint": fingerprint(parsed, task, correct), "tokens": out.get("usage", {}).get("total_tokens", "")}


def evaluate(task_dir, results_dir, models=None, with_image=True, config=None, workers=6):
    models, tasks = models or client.MODELS, load_tasks(task_dir)
    raw_dir = os.path.join(results_dir, "raw")
    jobs = [(m, t) for m in models for t in tasks]
    with ThreadPoolExecutor(workers) as pool:
        outs = list(pool.map(lambda j: ask(j[0], j[1], task_dir, raw_dir, with_image, config), jobs))
    rows = [row(m, t, o) for (m, t), o in zip(jobs, outs)]
    os.makedirs(results_dir, exist_ok=True)
    name = "responses.csv" if with_image else "blind_responses.csv"
    with open(os.path.join(results_dir, name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS); w.writeheader(); w.writerows(rows)
    with open(os.path.join(results_dir, "responses.jsonl" if with_image else "blind_responses.jsonl"), "w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r) + "\n")
    if with_image:
        json.dump({"models": models, **{**client.CONFIG, **(config or {})}, "prompt_template": client.PROMPT_TEMPLATE,
                   "endpoint": client.URL, "scoring": "eval/score.py: FINAL ANSWER line, typed compare, stated tolerance"},
                  open(os.path.join(results_dir, "run_config.json"), "w", encoding="utf-8"), indent=1)
    return rows


def report(rows, tasks=None):
    lines, bad = [], [r for r in rows if r["status"] != "ok"]
    for m in sorted({r["model"] for r in rows}):
        mine = [r for r in rows if r["model"] == m]
        lines.append(f"{m}: {sum(r['correct'] for r in mine)}/{len(mine)} correct")
        for r in mine:
            lines.append(f"    {r['task_id']:<28} {'RIGHT' if r['correct'] else 'wrong'}  said={r['parsed']!s:<16} "
                         f"ref={r['ref_answer']!s:<12} {r.get('fingerprint', '')}")
        wrong = [r for r in mine if not r["correct"] and r["status"] == "ok"]
        hit = [r for r in wrong if r.get("fingerprint", "").startswith("predicted")]
        lines.append(f"    called shots: {len(hit)} of {len(wrong)} wrong answers matched a predicted mistake")
    if bad:
        lines.append(f"INCOMPLETE REPLIES: {len(bad)} (fix the cause and re-run ALL tasks): " + ", ".join(f"{r['model']}/{r['task_id']}:{r['status']}" for r in bad))
    return "\n".join(lines)


if __name__ == "__main__":
    task_dir, results_dir = sys.argv[1], sys.argv[2]
    print(report(evaluate(task_dir, results_dir)))
