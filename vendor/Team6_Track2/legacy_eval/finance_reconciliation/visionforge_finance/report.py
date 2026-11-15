from __future__ import annotations
import html,json
from pathlib import Path

def render_report(run):
    run=Path(run); tasks=[json.loads(x) for x in (run/'tasks.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    resp=[json.loads(x) for x in (run/'responses.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()] if (run/'responses.jsonl').exists() else []
    latest={}; text_ablation={}; vision_by_task={}
    for r in resp:
        if r.get('mode')=='text-only': text_ablation[r['task_id']]=r
        else:
            latest[r['task_id']]=r
            vision_by_task.setdefault(r['task_id'],[]).append(r)
    for r in resp:
        if r['task_id'] not in latest: latest[r['task_id']]=r
    grouped={}
    for t in tasks:
        k=f"{t['family']} / {t['difficulty']}"; grouped.setdefault(k,[]).append(t)
    summary=[]; models=sorted({r.get('model','unknown') for r in resp if r.get('mode')!='text-only'})
    for model in models:
        for k,items in sorted(grouped.items()):
            considered=[r for t in items for r in vision_by_task.get(t['task_id'],[]) if r.get('model')==model]
            ok=sum(r.get('correct') is True for r in considered); fail=sum(r.get('status') in ('error','unparsed') or r.get('correct') is False for r in considered)
            summary.append(f"<tr><td>{html.escape(model)}</td><td>{html.escape(k)}</td><td>{len(items)}</td><td>{len(considered)}</td><td>{ok}</td><td>{fail}</td></tr>")
    cards=[]
    for t in tasks:
        r=latest.get(t['task_id'],{}); gt=json.loads((run/t['ground_truth']).read_text(encoding='utf-8')); im=t['images']
        imgs=''.join(f"<a class='page' href='{html.escape(x)}' target='_blank'><img src='{html.escape(x)}'><span>{html.escape(Path(x).stem)}</span></a>" for x in im)
        status=r.get('status','pending'); pred=r.get('prediction','—'); correct=r.get('correct')
        badge='pending' if not r else ('correct' if correct else status)
        ab=text_ablation.get(t['task_id']); abhtml=f"<p><b>Text-only ({html.escape(ab.get('model',''))}):</b> {html.escape(str(ab.get('prediction','')))} · {html.escape(str(ab.get('status','')))}</p>" if ab else ''
        vision=vision_by_task.get(t['task_id'],[])
        prediction_html=''.join(f"<p><b>{html.escape(x.get('model',''))}:</b> {html.escape(str(x.get('prediction','')))} · {html.escape(str(x.get('status','')))} · {'correct' if x.get('correct') else 'incorrect' if x.get('correct') is False else 'unscored'}</p>" for x in vision) or f"<p><b>Prediction:</b> {html.escape(str(pred))} · {html.escape(status)}</p>"
        raw_html=''.join(f"<details><summary>{html.escape(x.get('model',''))} raw response / error</summary><pre>{html.escape(str(x.get('raw_response',x.get('error',''))))}</pre></details>" for x in vision)
        cards.append(f"<article class='{badge}'><header><b>{html.escape(t['task_id'])}</b> · {html.escape(t['family'])} · {html.escape(t['difficulty'])} · {html.escape(t['layout'])}</header><div class='pages'>{imgs}</div><p class='question'>{html.escape(t['question'])}</p>{prediction_html}{abhtml}<details><summary>Ground truth and evidence</summary><p><b>{html.escape(gt['answer'])}</b></p><p>Evidence: {html.escape(', '.join(gt['evidence_ids']))}</p><pre>{html.escape(json.dumps(gt['evidence_trace'],indent=2))}</pre></details>{raw_html}{'<details><summary>Text-only raw response</summary><pre>'+html.escape(str(ab.get('raw_response',ab.get('error',''))))+'</pre></details>' if ab else ''}</article>")
    doc=f"""<!doctype html><meta charset="utf-8"><title>Financial evidence reconciliation</title><style>
body{{font:16px Arial,sans-serif;background:#eef2f6;color:#23364b;margin:28px}}h1{{color:#173858}}table{{border-collapse:collapse;background:white;margin:16px 0 28px}}td,th{{padding:10px 18px;border:1px solid #d4dee8;text-align:left}}article{{background:#fff;border-radius:12px;padding:20px;margin:22px 0;border-left:7px solid #8292a4;box-shadow:0 3px 12px #1f385014}}article.correct{{border-color:#18856f}}article.incorrect,article.error,article.unparsed{{border-color:#bd4f58}}article.pending{{border-color:#8292a4}}.pages{{display:flex;gap:12px;overflow-x:auto;margin:14px 0}}.page{{min-width:210px;width:22%;max-width:340px;color:#35506b;font-size:13px}}.page img{{width:100%;height:260px;object-fit:cover;object-position:top;border:1px solid #c8d2dd;background:#fff}}.question{{font-size:18px;line-height:1.4}}.status{{margin-left:12px;color:#61758a}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f7f9;padding:12px}}details{{margin:10px 0}}
</style><h1>Financial Evidence Reconciliation Factory</h1><p>{len(tasks)} generated tasks · clickable thumbnails open each full-resolution page. Ground truth and evidence traces are hidden by default.</p><h2>Failure summary by model, question family, and difficulty</h2><table><tr><th>Model</th><th>Group</th><th>Generated</th><th>Evaluated</th><th>Correct</th><th>Failures</th></tr>{''.join(summary)}</table>{''.join(cards)}"""
    (run/'report.html').write_text(doc,encoding='utf-8')

def main():
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--run',required=True); a=p.parse_args(); render_report(a.run)
if __name__=='__main__': main()
