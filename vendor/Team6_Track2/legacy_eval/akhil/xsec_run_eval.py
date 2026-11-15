"""Evaluate models on the tasks via OpenRouter.  Key from env OPENROUTER_API_KEY only.

python -m eval.run_eval --tasks tasks/reported --out results/reported
python -m eval.run_eval --tasks tasks/reported --out results/mock --mock     # offline test of parsing/scoring
"""
import argparse, base64, csv, json, os, re, sys, time

MODELS = ["anthropic/claude-haiku-5.5", "openai/gpt-6-luna"]
URL = "https://openrouter.ai/api/v1/chat/completions"
SUFFIX = ("\n\nThink step by step. End your reply with one final line of the form:\nFINAL ANSWER: <answer>\n"
          "(a plain number with no units for volumes, or the station pair for interval questions).")


def parse(resp, answer_type):
    m = re.findall(r"FINAL ANSWER:\s*(.+)", resp or "", flags=re.I)
    tail = m[-1] if m else (resp or "")[-300:]
    if answer_type == "label":
        s = re.findall(r"\d+\s*\+\s*\d{2}", tail)
        return "%s-%s" % (s[0].replace(" ", ""), s[1].replace(" ", "")) if len(s) >= 2 else ""
    nums = re.findall(r"-?\d[\d,]*\.?\d*", tail)
    return nums[0].replace(",", "") if nums and m else (nums[-1].replace(",", "") if nums else "")


def score(parsed, task):
    if parsed == "":
        return 0
    if task["answer_type"] == "label":
        return int(parsed == task["answer"])
    try:
        return int(abs(float(parsed) - task["answer"]) <= task["tolerance_rel"] * abs(task["answer"]))
    except ValueError:
        return 0


def call(model, task, task_dir, max_tokens, mock):
    if mock:
        return dict(content="Mock reply.\nFINAL ANSWER: %s" % task["answer"], finish_reason="stop", raw={})
    import requests
    b64 = base64.b64encode(open(os.path.join(task_dir, task["image"]), "rb").read()).decode()
    body = dict(model=model, temperature=0, max_tokens=max_tokens, reasoning={"effort": "high"},
                messages=[dict(role="user", content=[dict(type="text", text=task["question"] + SUFFIX),
                                                     dict(type="image_url", image_url=dict(url="data:image/png;base64," + b64))])])
    hdr = {"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]}
    for k in range(6):
        try:
            r = requests.post(URL, headers=hdr, json=body, timeout=600)
            if r.status_code == 429 or r.status_code >= 500:
                raise RuntimeError("HTTP %d" % r.status_code)
            r.raise_for_status()
            j = r.json(); ch = j["choices"][0]
            return dict(content=ch["message"].get("content") or "", finish_reason=ch.get("finish_reason"), raw=j)
        except Exception as e:
            if k == 5:
                return dict(content="", finish_reason="error", raw={}, error=str(e))
            time.sleep(2 ** k * 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="tasks/reported"); ap.add_argument("--out", default="results/reported")
    ap.add_argument("--max-tokens", type=int, default=32000); ap.add_argument("--mock", action="store_true")
    ap.add_argument("--models", nargs="*", default=MODELS)
    a = ap.parse_args()
    tasks = [json.loads(l) for l in open(os.path.join(a.tasks, "tasks.jsonl")) if l.strip()]
    os.makedirs(os.path.join(a.out, "raw"), exist_ok=True)
    cols = ["model", "task_id", "status", "parsed", "question_type", "response", "ref_answer", "correct", "finish_reason", "error"]
    rows, incomplete = [], 0
    for m in a.models:
        for t in tasks:
            r = call(m, t, a.tasks, a.max_tokens, a.mock)
            json.dump(r, open(os.path.join(a.out, "raw", "%s__%s.json" % (m.replace("/", "_"), t["task_id"])), "w"))
            ok = r["finish_reason"] == "stop" and not r.get("error")
            incomplete += (not ok)
            p = parse(r["content"], t["answer_type"])
            rows.append(dict(model=m, task_id=t["task_id"], status="ok" if ok else "incomplete", parsed=p,
                             question_type=t["question_type"], response=r["content"], ref_answer=t["answer"],
                             correct=score(p, t), finish_reason=r["finish_reason"], error=r.get("error", "")))
            print(m, t["task_id"], rows[-1]["correct"], r["finish_reason"])
    with open(os.path.join(a.out, "responses.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)
    lines = ["# Report", "", "| model | accuracy | n |", "|---|---|---|"]
    for m in a.models:
        rs = [r for r in rows if r["model"] == m]
        lines.append("| %s | %.2f | %d |" % (m, sum(r["correct"] for r in rs) / len(rs), len(rs)))
    lines += ["", "| model | question_type | accuracy |", "|---|---|---|"]
    for m in a.models:
        for qt in sorted(set(r["question_type"] for r in rows)):
            rs = [r for r in rows if r["model"] == m and r["question_type"] == qt]
            lines.append("| %s | %s | %.2f (%d) |" % (m, qt, sum(r["correct"] for r in rs) / len(rs), len(rs)))
    open(os.path.join(a.out, "report.md"), "w").write("\n".join(lines))
    if incomplete:
        print("WARNING: %d incomplete replies. Raise --max-tokens and re-run ALL tasks." % incomplete)
        sys.exit(2)


if __name__ == "__main__":
    main()
