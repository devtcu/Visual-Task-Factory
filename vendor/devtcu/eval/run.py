"""Evaluate both models on a task folder and write the results folder (responses.csv, run_config.json, raw/)."""
import csv, json, os, sys
from concurrent.futures import ThreadPoolExecutor
from . import client, score

COLUMNS = ["model", "task_id", "status", "parsed", "question_type", "response", "ref_answer", "correct", "trap_hit", "finish_reason", "error"]


def load_tasks(task_dir):
    with open(os.path.join(task_dir, "tasks.jsonl"), encoding="utf-8") as f:
        tasks = [json.loads(line) for line in f if line.strip()]
    return [t for t in tasks if all(c["pass"] for c in t.get("checks", []))]   # failed tasks are excluded, never scored


def ask(model, task, task_dir, raw_dir, with_image=True, config=None):
    """One model, one task. Cached on disk so the same call is never paid for twice."""
    tag = "" if with_image else ".blind"
    path = os.path.join(raw_dir, f"{model.replace('/', '__')}__{task['task_id']}{tag}.json")
    if os.path.exists(path):
        out = json.load(open(path, encoding="utf-8"))
        if out.get("status") == "ok":
            return out
    imgs = task["image"] if isinstance(task["image"], list) else [task["image"]]
    image = [os.path.join(task_dir, i) for i in imgs] if with_image else None
    out = client.call(model, task["question"], image, config)
    os.makedirs(raw_dir, exist_ok=True)
    json.dump(out, open(path, "w", encoding="utf-8"), indent=1)
    return out


def row(model, task, out):
    parsed = score.extract(out["response"], task) if out["status"] == "ok" else ""
    return {"model": model, "task_id": task["task_id"], "status": out["status"], "parsed": parsed,
            "question_type": task.get("question_type", ""), "response": out["response"],
            "ref_answer": json.dumps(task["answer"]) if isinstance(task["answer"], list) else task["answer"],
            "correct": score.is_correct(parsed, task) if out["status"] == "ok" else 0,
            "trap_hit": score.trap_hit(parsed, task) if out["status"] == "ok" else "",
            "finish_reason": out["finish_reason"], "error": out["error"]}


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
        wrong = [r for r in mine if r["status"] == "ok" and not r["correct"]]
        lines.append(f"{m}: {sum(r['correct'] for r in mine)}/{len(mine)} correct; "
                     f"{sum(bool(r['trap_hit']) for r in wrong)}/{len(wrong)} wrong answers landed on a called shot")
        for qt in sorted({r["question_type"] for r in mine}):
            sub = [r for r in mine if r["question_type"] == qt]
            lines.append(f"    {qt}: {sum(r['correct'] for r in sub)}/{len(sub)}")
    if bad:
        lines.append(f"INCOMPLETE REPLIES: {len(bad)} (fix the cause and re-run ALL tasks): " + ", ".join(f"{r['model']}/{r['task_id']}:{r['status']}" for r in bad))
    return "\n".join(lines)


if __name__ == "__main__":
    task_dir, results_dir = sys.argv[1], sys.argv[2]
    print(report(evaluate(task_dir, results_dir)))
