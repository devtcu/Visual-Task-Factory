"""Team 6 live demo: browse the reported tasks, generate a fresh task with any pipeline, and ask both models.

  OPENROUTER_API_KEY=... .venv/bin/python app.py      (or ./start.sh)   then open http://127.0.0.1:8765

Generation runs the real generators (gen_worker.py, one process per task). Asking the models reuses the team's
evaluator (eval/run_eval.request_one) and scoring (eval/scoring) unchanged, so demo answers are scored exactly as in
the submission. The key is read from the environment only and never written to disk or sent to the page."""
import csv
import json
import mimetypes
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import os
import socket

ROOT = Path(__file__).resolve().parent
TEAM6, DEVTCU, TENNIS = ROOT / "vendor/Team6_Track2", ROOT / "vendor/devtcu", ROOT / "vendor/tennis"
RUNS = ROOT / "runs"
sys.path.insert(0, str(TEAM6))
from eval.run_eval import MODELS, request_one          # noqa: E402  (the team's evaluator, unchanged)
from eval.scoring import parse_answer, score_answer    # noqa: E402

SETTINGS = {"temperature": 0, "reasoning": {"effort": "high"}, "max_tokens": 32768}         # as in results/final/run_config.json
TENNIS_SETTINGS = {"temperature": 0, "max_tokens": 64000, "reasoning": {"max_tokens": 40000}}  # capped so replies always finish

AKHIL_PREFIX = {"spc": "heads_", "fiber": "fiber_", "brain": "brain_", "cross_sections": "xsec_"}
LABELS = {"spc": "SPC control charts (factory heads)", "fiber": "Fiber patching (AI cluster)", "brain": "EEG brain reading",
          "cross_sections": "Roadway cross sections", "finance": "Finance reconciliation", "measurebench": "Instrument reading",
          "reconstruction": "Visual reconstruction", "brain_connections": "Brain Connections (connectome)",
          "tennis": "Tennis 3D line call"}

TYPE_NAMES = {
    "heads_first_signal": "First out-of-control signal", "fiber_trace": "Trace a fiber path", "fiber_fault": "Find the cut fiber",
    "brain_spike_location": "Locate the EEG spike", "brain_rem_latency": "Time to first REM sleep", "brain_awakenings": "Count the awakenings",
    "brain_report_audit": "Audit a sleep report", "brain_find_fix": "Find and fix the report error",
    "xsec_max_cut_interval_hard": "Largest cut interval", "xsec_cut_total_easy": "Total cut volume (easy)",
    "xsec_cut_total_medium": "Total cut volume (medium)", "xsec_cut_total_hard": "Total cut volume (hard)",
    "price_rule_L0": "Invoice overcharge", "price_rule_L1": "Invoice overcharge (harder)", "price_rule_L2": "Invoice overcharge (hardest)",
    "analog_dial_single_reading": "Read a dial gauge", "analog_dial_one_tick_counterfactual": "Gauge change between readings",
    "vernier_single_reading": "Read a vernier caliper", "meniscus_single_reading": "Read a measuring cylinder",
    "composite_panel_single_reading": "Read an instrument panel", "composite_panel_comparison": "Compare panel readings",
    "composite_panel_difference": "Difference between panel readings", "global_spatial_reconstruction": "Rebuild the photo from patches",
    "redundant_edge": "Which connection can go?", "min_edge_cut": "Fewest cuts to disconnect", "critical_count": "Count critical connections",
    "delay_after_failure": "Delay after two failures", "multiview_corner_call": "Line call",
}
LEVEL_WORDS = {1: "Level 1 · plain", 2: "Level 2 · delays", 3: "Level 3 · ties", 4: "Level 4 · one-way",
               5: "Level 5 · circuit rules", 6: "Level 6 · connectogram"}


def nice_type(qtype):
    """Plain-English name for a question type; Brain Connections types carry their level (critical_count_L6)."""
    if qtype and "_L" in qtype and qtype.rsplit("_L", 1)[1].isdigit() and qtype.rsplit("_L", 1)[0] in TYPE_NAMES:
        base, lv = qtype.rsplit("_L", 1)
        return f"{TYPE_NAMES[base]} · level {lv}"
    return TYPE_NAMES.get(qtype or "", (qtype or "Default question").replace("_", " ").capitalize())


def title_of(t):
    q, p = t.get("question_type") or "", t.get("pipeline", "")
    if p == "tennis":
        return f"Line call · Shot {int(t['task_id'].rsplit('_', 1)[1])}"
    base = q.rsplit("_L", 1)[0] if p == "brain_connections" else q
    return TYPE_NAMES.get(base, nice_type(q))


TASKS = {}     # task_id -> {"task": record, "folder": Path, "source": label}
JOBS = {}      # job_id -> {"status", "result" | "error", "started"}


# ---------------------------------------------------------------- task catalogue
def register(task, folder, source):
    task = dict(task)
    imgs = task["image"] if isinstance(task["image"], list) else None
    if imgs:                                            # tennis: three camera views under "image"
        task["images"], task["image"] = imgs, imgs[0]
    task.setdefault("wrong_answers", task.get("traps", {}))
    TASKS[task["task_id"]] = {"task": task, "folder": Path(folder), "source": source}
    return task


def load_gallery():
    for line in (TEAM6 / "tasks/final/tasks.jsonl").read_text().splitlines():
        if line.strip():
            register(json.loads(line), TEAM6 / "tasks/final", "Team 6 reported set")
    picks = ["critical_count_L6_s1", "delay_after_failure_L6_s1", "min_edge_cut_L6_s1", "critical_count_L5_s1", "redundant_edge_L4_s1"]
    for line in (DEVTCU / "tasks/tasks.jsonl").read_text().splitlines():
        t = json.loads(line)
        if any(t["task_id"].endswith(p) for p in picks):
            t.update(pipeline="brain_connections", member="devtcu")
            register(t, DEVTCU / "tasks", "Brain Connections handoff")
    for line in (TENNIS / "tasks.jsonl").read_text().splitlines():
        t = json.loads(line)
        t.update(pipeline="tennis", member="tennis teammate")
        register(t, TENNIS, "Tennis 3D (no generator received)")


def sources():
    out = []
    for p in ("spc", "fiber", "brain", "cross_sections", "finance", "measurebench", "reconstruction"):
        try:
            qs = json.loads(subprocess.run([sys.executable, "-c", (
                "import json; from pipelines import adapter_for; a,m,d=adapter_for(%r); print(json.dumps([list(getattr(a,'QUESTION_TYPES',[]) or []), d]))" % p)],
                cwd=TEAM6, capture_output=True, text=True, timeout=120).stdout.strip().splitlines()[-1])
        except Exception:                               # noqa: BLE001 - a broken adapter just offers its default
            qs = [[], None]
        types = [q for q in qs[0] if q.startswith(AKHIL_PREFIX[p])] if p in AKHIL_PREFIX else qs[0]
        out.append({"id": p, "kind": "team6", "label": LABELS[p], "types": types, "default": qs[1] or (types[0] if types else ""),
                    "type_names": {q: nice_type(q) for q in types}})
    manifest = json.loads((DEVTCU / "MANIFEST.json").read_text())
    out.append({"id": "brain_connections", "kind": "devtcu", "label": LABELS["brain_connections"],
                "types": manifest["question_types"], "default": "critical_count_L6",
                "type_names": {q: nice_type(q) for q in manifest["question_types"]}})
    out.append({"id": "tennis", "kind": "none", "label": LABELS["tennis"], "types": [], "default": "", "type_names": {}})
    return out


def public(entry):
    """What the page may show. The answer and predicted wrong answers are sent, but the page hides them until asked."""
    t = entry["task"]
    files = t.get("images") or [t["image"]]
    return {"task_id": t["task_id"], "pipeline": t.get("pipeline", ""), "label": LABELS.get(t.get("pipeline", ""), t.get("pipeline", "")),
            "title": title_of(t), "level": LEVEL_WORDS.get(t.get("level")) if t.get("pipeline") == "brain_connections" else None,
            "source": entry["source"], "question": t["question"], "answer": t["answer"], "answer_type": t["answer_type"],
            "tolerance": t.get("tolerance_abs", t.get("tolerance_rel")), "seed": t.get("seed"),
            "question_type": t.get("question_type"), "images": [f"/file?task={t['task_id']}&path={p}" for p in files],
            "checks_passed": (t.get("checks") or {}).get("passed") if isinstance(t.get("checks"), dict) else None,
            "failed_checks": [f"{k}: {v}" if v is not False else k for k, v in ((t.get("checks") or {}).get("checks") or {}).items()
                              if v is not True and k != "member_validation"] if isinstance(t.get("checks"), dict) else [],
            "wrong_answers": t.get("wrong_answers", {})}


# ---------------------------------------------------------------- jobs
def run_job(fn, *args):
    jid = uuid.uuid4().hex[:10]
    JOBS[jid] = {"status": "running", "started": time.time()}

    def go():
        try:
            JOBS[jid].update(status="done", result=fn(*args))
        except Exception as e:                          # noqa: BLE001 - reported to the page
            JOBS[jid].update(status="error", error=str(e)[:1500])
    threading.Thread(target=go, daemon=True).start()
    return jid


def generate(source, qtype, seed):
    src = next(s for s in sources_cache if s["id"] == source)
    if src["kind"] == "none":
        raise RuntimeError("No generator was received for this pipeline; pick one of its tasks from the gallery instead.")
    out = RUNS / "fresh" / f"{source}_{qtype or 'default'}_s{seed}"
    cwd = TEAM6 if src["kind"] == "team6" else DEVTCU
    p = subprocess.run([sys.executable, str(ROOT / "gen_worker.py"), src["kind"], source, qtype or "", str(seed), str(out)],
                       cwd=cwd, capture_output=True, text=True, timeout=900)
    line = next((l for l in p.stdout.splitlines() if l.startswith("@@TASK@@")), None)
    if not line:
        raise RuntimeError("Generation failed:\n" + (p.stderr or p.stdout)[-1200:])
    task = json.loads(line[len("@@TASK@@"):])
    task["task_id"] = f"fresh_{task['task_id']}"         # never collides with a gallery task
    return public(TASKS[register(task, out, "Generated live")["task_id"]])


def ask(task_id, force, model=None):
    entry = TASKS[task_id]
    task, folder = entry["task"], entry["folder"]
    cfg = TENNIS_SETTINGS if task.get("pipeline") == "tennis" else SETTINGS
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise RuntimeError("Set OPENROUTER_API_KEY before starting the demo (see README.md).")

    def one(model):
        t0 = time.time()
        try:
            saved = request_one(task, folder, model, cfg, RUNS / "eval", force=force)
        except Exception as e:                          # noqa: BLE001 - one model failing should not hide the other
            return {"model": model, "error": str(e)[:600]}
        parsed = parse_answer(saved["response"], task)
        verdict = score_answer(task, parsed, folder)
        traps = [name for name, v in task.get("wrong_answers", {}).items()
                 if not verdict["correct"] and score_answer({**task, "answer": v}, parsed, folder).get("correct")]
        usage = (saved.get("raw_response") or {}).get("usage") or {}
        return {"model": model, "parsed": parsed, "correct": verdict["correct"], "reason": verdict.get("reason"),
                "called_shot": traps, "response": saved["response"][-4000:], "seconds": round(time.time() - t0, 1),
                "cached": time.time() - t0 < 1.5, "tokens": usage.get("completion_tokens"), "cost": usage.get("cost")}
    with ThreadPoolExecutor(2) as pool:
        return {"answer": task["answer"], "settings": cfg, "models": list(pool.map(one, [model] if model in MODELS else MODELS))}


# ---------------------------------------------------------------- http
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path == "/":
            return self.send(200, (ROOT / "static/index.html").read_bytes(), "text/html; charset=utf-8")
        if u.path == "/api/sources":
            return self.send(200, sources_cache)
        if u.path == "/api/gallery":
            return self.send(200, [public(e) for e in TASKS.values() if e["source"] != "Generated live"])
        if u.path.startswith("/api/job/"):
            j = JOBS.get(u.path.rsplit("/", 1)[1])
            return self.send(200 if j else 404, j or {"error": "no such job"})
        if u.path == "/file":
            e = TASKS.get(q.get("task", ""))
            if not e:
                return self.send(404, {"error": "no such task"})
            f = (e["folder"] / q.get("path", "")).resolve()
            if not f.is_relative_to(e["folder"].resolve()) or not f.is_file():
                return self.send(404, {"error": "no such file"})
            return self.send(200, f.read_bytes(), mimetypes.guess_type(f.name)[0] or "application/octet-stream")
        self.send(404, {"error": "not found"})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)) or 2) or b"{}")
        if self.path == "/api/generate":
            return self.send(200, {"job": run_job(generate, body["source"], body.get("question_type") or "", int(body.get("seed", 1)))})
        if self.path == "/api/ask":
            if body.get("task_id") not in TASKS:
                return self.send(404, {"error": "no such task"})
            return self.send(200, {"job": run_job(ask, body["task_id"], bool(body.get("force")), body.get("model"))})
        self.send(404, {"error": "not found"})


if __name__ == "__main__":
    RUNS.mkdir(exist_ok=True)
    load_gallery()
    print("Reading each pipeline's question types ...", flush=True)
    sources_cache = sources()
    port = int(os.environ.get("DEMO_PORT", 8765))
    print(f"Team 6 demo: {len(TASKS)} gallery tasks, {len(sources_cache)} pipelines. Open http://localhost:{port}"
          + ("" if os.environ.get("OPENROUTER_API_KEY") else "  (no OPENROUTER_API_KEY: model calls disabled)"), flush=True)
    if os.environ.get("DEMO_NO_BROWSER") != "1":
        webbrowser.open(f"http://localhost:{port}")

    class V6Server(ThreadingHTTPServer):
        address_family = socket.AF_INET6
    try:                                              # "localhost" can mean ::1 in the browser: listen there too (still this machine only)
        v6 = V6Server(("::1", port), Handler)
        threading.Thread(target=v6.serve_forever, daemon=True).start()
    except OSError:
        pass
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
