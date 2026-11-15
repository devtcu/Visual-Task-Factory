"""Build the handoff task set through the adapter, in parallel.

  python build_tasks.py tasks                       # pick seeds: 1..5 per question type, the next seed when one has no valid layout
  python build_tasks.py /tmp/rebuild --seeds tasks/seeds_used.json   # rebuild exactly those seeds (determinism check)

Writes <out>/tasks.jsonl (only tasks that pass validate_task), <out>/rejected.jsonl and <out>/seeds_used.json."""
import argparse
import json
import os
from concurrent.futures import ProcessPoolExecutor

from generators.devtcu import adapter

PER_TYPE, MAX_SEED = 5, 15


def one(job):
    qtype, seed, out = job
    try:
        return adapter.generate_task(seed, qtype, out)
    except ValueError as e:
        return {"skipped": True, "question_type": qtype, "seed": seed, "why": str(e)}


def pick(qtype, out):
    """Seeds 1, 2, ... until PER_TYPE tasks pass every check (or MAX_SEED is reached)."""
    got = []
    for seed in range(1, MAX_SEED + 1):
        r = one((qtype, seed, out))
        if not r.get("skipped") and r["checks"]["passed"]:
            got.append(r)
        elif not r.get("skipped"):
            got.append(r)                          # kept as a rejected task, reported, never counted
        if sum(1 for g in got if g["checks"]["passed"]) == PER_TYPE:
            break
    return got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--seeds", help="seeds_used.json from an earlier build: rebuild exactly those")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    with ProcessPoolExecutor() as pool:
        if a.seeds:
            jobs = [(q, s, a.out) for q, seeds in json.load(open(a.seeds)).items() for s in seeds]
            recs = [r for r in pool.map(one, jobs) if not r.get("skipped")]
        else:
            recs = [r for group in pool.map(pick, adapter.QUESTION_TYPES, [a.out] * len(adapter.QUESTION_TYPES)) for r in group]
    ok = [r for r in recs if r["checks"]["passed"]]
    with open(os.path.join(a.out, "tasks.jsonl"), "w", encoding="utf-8") as f:
        for r in ok:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(a.out, "rejected.jsonl"), "w", encoding="utf-8") as f:
        for r in recs:
            if not r["checks"]["passed"]:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    seeds = {}
    for r in recs:
        seeds.setdefault(r["question_type"], []).append(r["seed"])
    json.dump(seeds, open(os.path.join(a.out, "seeds_used.json"), "w"), indent=1)
    print(f"{len(ok)} valid, {len(recs) - len(ok)} rejected, over {len(seeds)} question types")
    for q in adapter.QUESTION_TYPES:
        n = sum(1 for r in ok if r["question_type"] == q)
        print(f"  {q:<26} {n} valid  seeds {seeds.get(q, [])}")


if __name__ == "__main__":
    main()
