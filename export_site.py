"""Build the static showcase site (for Vercel) from the demo's gallery and its saved model answers.

  .venv/bin/python export_site.py            writes site/: index.html, data.json, img/<task_id>/...

No model is called here. Each task shows the answers saved in runs/eval/raw (run the local demo, or Ask in it, to
record them), scored with the team's own parse_answer / score_answer exactly as the live demo does. A task with no
saved answer for a model shows that model as "not run". The site holds no key and makes no API calls."""
import csv
import glob
import json
import shutil
import sys
from pathlib import Path

import app
from app import MODELS, TASKS, parse_answer, score_answer

SITE = app.ROOT / "site"


def recorded(task, folder, model):
    files = sorted(glob.glob(str(app.RUNS / "eval/raw" / f"{model.replace('/', '__')}__{task['task_id']}__*.json")))
    note = None
    if files:
        saved = json.loads(Path(files[-1]).read_text(encoding="utf-8"))
    else:                                               # tennis: the teammate's own earlier run on the same images
        rows = [r for r in csv.DictReader(open(app.TENNIS / "earlier_responses.csv", encoding="utf-8"))
                if r["task_id"] == task["task_id"] and r["model"] == model and r["status"] == "ok"]
        if not rows:
            return {"model": model, "missing": True}
        saved, note = {"response": rows[-1]["response"]}, "teammate's earlier run"
    parsed = parse_answer(saved["response"], task)
    verdict = score_answer(task, parsed, folder)
    traps = [name for name, v in task.get("wrong_answers", {}).items()
             if not verdict["correct"] and score_answer({**task, "answer": v}, parsed, folder).get("correct")]
    raw = saved.get("raw_response") or {}
    raw = json.loads(raw) if isinstance(raw, str) else raw
    usage = raw.get("usage") or {}
    return {"model": model, "parsed": parsed, "correct": verdict["correct"], "reason": verdict.get("reason"),
            "called_shot": traps, "response": saved["response"][-4000:], "seconds": round(float(saved.get("wall_seconds") or 0), 1),
            "tokens": usage.get("completion_tokens"), "cost": usage.get("cost"), "note": note}


def main():
    app.load_gallery()
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "img").mkdir(parents=True)
    out = []
    for tid, entry in TASKS.items():
        t, folder = entry["task"], entry["folder"]
        p = app.public(entry)
        imgs = []
        for rel in t.get("images") or [t["image"]]:
            dest = SITE / "img" / tid / Path(rel).name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(folder / rel, dest)
            imgs.append(f"img/{tid}/{dest.name}")
        p["images"] = imgs
        p["settings"] = app.TENNIS_SETTINGS if t.get("pipeline") == "tennis" else app.SETTINGS
        p["models"] = [recorded(t, folder, m) for m in MODELS]
        out.append(p)
    (SITE / "data.json").write_text(json.dumps(out, ensure_ascii=False, default=str), encoding="utf-8")
    shutil.copyfile(app.ROOT / "static/showcase.html", SITE / "index.html")
    missing = [(p["task_id"], m["model"]) for p in out for m in p["models"] if m.get("missing")]
    print(f"site/: {len(out)} tasks, {sum(not m.get('missing') for p in out for m in p['models'])} recorded answers"
          + (f", {len(missing)} not run: {missing}" if missing else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
