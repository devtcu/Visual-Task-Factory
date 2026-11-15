"""Build an offline gallery of the reported task records (no API or model calls)."""
import html
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]


def esc(value):
    return html.escape(str(value), quote=True)


def task_url(relative):
    return quote("tasks/final/" + relative, safe="/")


def main():
    tasks = [json.loads(line) for line in (ROOT / "tasks/final/tasks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    nav, cards = [], []
    for i, task in enumerate(tasks, 1):
        name = task["pipeline"].replace("_", " ").title()
        nav.append(f'<a href="#task-{i}">{i}. {esc(name)}</a>')
        paths = task.get("images") or [task["image"]]
        figures = []
        for n, path in enumerate(paths, 1):
            label = f"{name}, page {n}" if len(paths) > 1 else name
            figures.append(f'<figure><a href="{task_url(path)}" target="_blank" rel="noopener"><img src="{task_url(path)}" alt="{esc(label)}" loading="lazy"></a><figcaption>{esc(label)} &middot; <a href="{task_url(path)}" target="_blank" rel="noopener">Open full resolution</a></figcaption></figure>')
        checks = task["checks"]
        passed = bool(checks["passed"])
        count = sum(value is True for value in checks["checks"].values())
        answer = json.dumps(task["answer"], ensure_ascii=False, indent=2)
        cards.append(f'''<article id="task-{i}">
          <div class="card-top"><span class="eyebrow">TASK {i:02d} / {len(tasks):02d}</span><span class="status">{'Validation passed' if passed else 'Validation failed'} &middot; {count} checks</span></div>
          <h2>{esc(name)}</h2><p class="task-id">{esc(task['task_id'])}</p>
          <p class="question">{esc(task['question'])}</p>
          <div class="meta">Seed {esc(task['seed'])} &middot; {esc(task['generator_version'])} &middot; <a href="{task_url(task['data'])}">Structured data</a></div>
          <div class="images">{''.join(figures)}</div>
          <details><summary>Reference answer and validation</summary><pre>{esc(answer)}</pre><pre>{esc(json.dumps(checks, ensure_ascii=False, indent=2))}</pre></details>
        </article>''')
    page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Team 6 · Seven-task draft review</title>
    <style>
    :root{color-scheme:light;--ink:#172638;--muted:#596879;--line:#dce3ea;--blue:#175da4}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f1f4f7;color:var(--ink);font:16px/1.65 system-ui,-apple-system,Segoe UI,sans-serif}a{color:var(--blue);text-underline-offset:3px}header{background:#142b45;color:#fff;padding:48px max(24px,calc((100vw - 1140px)/2)) 38px}header h1{font-size:clamp(28px,4vw,44px);line-height:1.2;margin:8px 0 16px;letter-spacing:-1px}header p{max-width:850px;color:#d6e2ed;margin:0}header a{color:#c1e2ff}.eyebrow{font-size:12px;font-weight:750;letter-spacing:1.4px}.draft{margin:22px 0 0;padding:12px 16px;background:#fff0cc;color:#5b3c00;border-radius:6px;max-width:900px}.layout{display:grid;grid-template-columns:205px minmax(0,1fr);gap:28px;max-width:1190px;margin:30px auto;padding:0 24px}nav{position:sticky;top:24px;align-self:start}nav a{display:block;padding:8px 10px;border-radius:5px;font-size:14px;text-decoration:none}nav a:hover{background:#e1e9f2}nav .notes{margin-top:20px;border-top:1px solid var(--line);padding-top:14px}article{padding:28px;background:#fff;border:1px solid var(--line);border-radius:10px;margin-bottom:28px;scroll-margin-top:20px;box-shadow:0 3px 16px #15263806}.card-top{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}.status{font-size:12px;font-weight:650;color:#215f3a;background:#e8f5ed;padding:2px 9px;border-radius:20px}h2{font-size:26px;line-height:1.2;margin:18px 0 6px}.task-id{font-size:12px;color:var(--muted);overflow-wrap:anywhere;margin:0}.question{margin:22px 0;white-space:pre-wrap}.meta{font-size:12px;color:var(--muted);padding-bottom:16px;border-bottom:1px solid var(--line);overflow-wrap:anywhere}figure{margin:22px 0}figure img{display:block;width:100%;height:auto;border:1px solid var(--line)}figcaption{color:var(--muted);font-size:12px;margin-top:5px}details{margin-top:22px;border-top:1px solid var(--line);padding-top:16px}summary{cursor:pointer;font-weight:650}pre{font:12px/1.6 ui-monospace,Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:#f2f5f8;padding:16px;border-radius:6px}footer{max-width:1140px;margin:0 auto 40px;padding:0 24px;color:var(--muted);font-size:13px}@media(max-width:780px){.layout{display:block;padding:0 14px}nav{position:static;display:flex;gap:4px;flex-wrap:wrap;margin-bottom:20px}nav .notes{border:0;margin:0;padding:0}article{padding:19px}header{padding:30px 22px}.question{font-size:15px}}@media print{nav{display:none}.layout{display:block}article{break-before:page;box-shadow:none}details{display:block}body{background:white}}
    </style></head><body><header><div class="eyebrow">TEAM 6 · TRACK 2 · VISUAL TASK FACTORY</div><h1>Seven pipelines. Seven tasks.</h1><p>Review the exact questions and images included in this draft. Open any image at full resolution; expand the reference answer after checking the task.</p><div class="draft"><strong>Preparation draft.</strong> Three more tasks and the final two-model evaluation are pending. These validation results are software checks, not model scores or human team signoff.</div></header><div class="layout"><nav aria-label="Task navigation">NAVIGATION<div>__NAV__</div><div class="notes"><a href="HANDCHECK.md">Hand-check notes</a><a href="README.md">Setup and submission notes</a><a href="COMPLETION_STATUS.json">Completion status</a></div></nav><main>__CARDS__</main></div><footer>Offline gallery. No network requests, tracking, API keys, or external libraries. Generated from tasks/final/tasks.jsonl by tools/build_review.py.</footer></body></html>'''
    (ROOT / "review.html").write_text(page.replace("__NAV__", "".join(nav)).replace("__CARDS__", "".join(cards)), encoding="utf-8")
    print(f"Wrote review.html for {len(tasks)} tasks")


if __name__ == "__main__":
    main()
