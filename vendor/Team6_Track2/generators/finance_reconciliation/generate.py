from __future__ import annotations
import argparse, csv, json, hashlib
from datetime import datetime, timezone
from pathlib import Path
from .engine import tasks_for, render_svg, validate

def _json(path,obj): path.write_text(json.dumps(obj,indent=2,default=str,ensure_ascii=False),encoding='utf-8')

def render_pngs(jobs):
    """Render every document page in one pinned local Chromium process."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True); page=browser.new_page(viewport={'width':1654,'height':2339},device_scale_factor=1); page.set_default_timeout(120000)
        for svg_path,png_path in jobs:
            page.goto(svg_path.resolve().as_uri(),wait_until='domcontentloaded',timeout=120000); page.screenshot(path=str(png_path),full_page=False,timeout=120000)
        browser.close()

def report_html(run):
    from .report import render_report
    render_report(run)

def generate(count=15,seed=42,output='runs/finance_demo',difficulty='mixed',family=None):
    run=Path(output); run.mkdir(parents=True,exist_ok=True); tasks=[]; renderjobs=[]
    for tid,scene,docs,rendered,qtext,answer,atype,evidence,trace,checks in tasks_for(count,seed,difficulty,family):
        folder=run/tid; imgdir=folder/'images'; imgdir.mkdir(parents=True,exist_ok=True)
        expected={f"{n:02d}_{kind}.{ext}" for n,kind in enumerate(docs,1) for ext in ('svg','png')}
        run_resolved=run.resolve(); imgdir_resolved=imgdir.resolve()
        if not imgdir_resolved.is_relative_to(run_resolved): raise RuntimeError('Image output escaped the run folder')
        # Remove only obsolete renderer outputs from this sample's own images directory.
        for old in imgdir.iterdir():
            if old.is_file() and old.suffix.lower() in ('.svg','.png') and old.name not in expected: old.unlink()
        scene_path=folder/'scene.json'; _json(scene_path,scene)
        (folder/'question.txt').write_text(qtext+'\n',encoding='utf-8')
        prompt=qtext+'\n\nInspect all attached document pages. Return only the requested integer, USD amount with two decimals, or LINE N/NONE. Do not include reasoning.'
        (folder/'model_prompt.txt').write_text(prompt+'\n',encoding='utf-8')
        _json(folder/'ground_truth.json',{'answer':answer,'answer_type':atype,'currency_tolerance':'0.01' if atype=='currency' else None,'evidence_ids':evidence,'evidence_trace':trace})
        direct_leak=(answer.lower() in qtext.lower()) if answer!='NONE' else False
        _json(folder/'validation.json',{'valid':True,'documents':checks,'text_only_ablation':{'question_contains_oracle_answer':direct_leak,'none_is_only_an_allowed_response_token':answer=='NONE','canonical_data_in_prompt':False,'image_required_evidence_ids':evidence}})
        imgpaths=[]
        for n,kind in enumerate(docs,1):
            svgtext=rendered[kind]; stem=f'{n:02d}_{kind}'; sp=imgdir/f'{stem}.svg'; pp=imgdir/f'{stem}.png'
            sp.write_text(svgtext,encoding='utf-8'); renderjobs.append((sp,pp)); imgpaths.append(str(pp.relative_to(run)).replace('\\','/'))
        tasks.append({'task_id':tid,'family':scene['family'],'difficulty':scene['difficulty'],'seed':scene['seed'],'layout':scene['variant'],'folder':tid,'question':qtext,'prompt':prompt,'answer_type':atype,'images':imgpaths,'scene':f'{tid}/scene.json','ground_truth':f'{tid}/ground_truth.json','validation':f'{tid}/validation.json','status':'pending'})
    render_pngs(renderjobs)
    (run/'tasks.jsonl').write_text(''.join(json.dumps(t,ensure_ascii=False)+'\n' for t in tasks),encoding='utf-8')
    if not (run/'responses.jsonl').exists(): (run/'responses.jsonl').write_text('',encoding='utf-8')
    if not (run/'scores.csv').exists():
        with (run/'scores.csv').open('w',newline='',encoding='utf-8') as f: csv.DictWriter(f,fieldnames=['task_id','family','difficulty','model','status','prediction','reference','correct','latency_ms','error']).writeheader()
    _json(run/'run_meta.json',{'generator':'visionforge_finance','seed':seed,'count':len(tasks),'created_utc':datetime.now(timezone.utc).isoformat(),'renderer':'SVG -> Playwright Chromium PNG at 1654x2339','financial_math':'Decimal, ROUND_HALF_UP to cents','references':['https://aclanthology.org/2025.acl-long.1138/','https://arxiv.org/abs/2605.17962','https://ojs.aaai.org/index.php/AAAI/article/view/39785']})
    report_html(run)
    print(f'Generated {len(tasks)} tasks in {run.resolve()} ({len(renderjobs)} full-resolution document pages)')
    for t in tasks: print(f"{t['task_id']} [{t['family']}/{t['difficulty']}/{t['layout']}]: {', '.join(t['images'])}")
    return tasks

def main():
    p=argparse.ArgumentParser(); p.add_argument('--seed',type=int,default=42); p.add_argument('--difficulty',choices=['mixed','easy','medium','hard'],default='mixed'); p.add_argument('--family',choices=['quantity','balance','price_rule']); p.add_argument('--count',type=int,default=15); p.add_argument('--output',default='runs/finance_demo'); a=p.parse_args()
    generate(a.count,a.seed,a.output,a.difficulty,a.family)
if __name__=='__main__': main()
