from __future__ import annotations
import argparse,base64,csv,json,os,re,time,urllib.request,urllib.error
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path

def parse_answer(text,kind):
    s=str(text or '').replace('−','-').strip()
    if kind=='integer':
        tagged=re.findall(r'(?:answer|eligible(?:\s+units?)?|quantity|total)\s*[:=]?\s*(\d+)\b',s,re.I)
        nums=tagged or re.findall(r'\b\d+\b',s)
        return nums[-1] if nums else ''
    if kind=='currency':
        vals=re.findall(r'\$\s*([+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?)',s)
        if not vals:
            vals=re.findall(r'\b([+-]?\d[\d,]*\.\d{2})\b',s)
        return f"${Decimal(vals[-1].replace(',','')):.2f}" if vals else ''
    hits=re.findall(r'\bLINE\s*#?\s*(\d+)\b',s,re.I)
    if hits: return f"LINE {hits[-1]}"
    if re.search(r'\bNONE\b',s,re.I): return 'NONE'
    return ''

def correct(pred,truth,kind):
    if not pred: return False
    if kind=='currency':
        p=Decimal(re.sub(r'[^0-9.\-]','',pred)); t=Decimal(re.sub(r'[^0-9.\-]','',truth)); return abs(p-t)<=Decimal('0.01')
    return pred.strip().upper()==truth.strip().upper()

def read_tasks(run): return [json.loads(x) for x in (Path(run)/'tasks.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
def response_records(run):
    p=Path(run)/'responses.jsonl'; return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()] if p.exists() else []
def write_scores(run):
    records=response_records(run); p=Path(run)/'scores.csv'
    cols=['task_id','family','difficulty','model','status','prediction','reference','correct','latency_ms','error']
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader()
        for r in records: w.writerow({k:r.get(k) for k in cols})

def evaluate(run,model='openai/gpt-6-luna',text_only=False,limit=None,provider='openrouter'):
    from vf.prototype import load_dotenv
    load_dotenv(); env_name='ANTHROPIC_API_KEY' if provider=='claude' else 'OPENROUTER_API_KEY'; key=os.getenv(env_name)
    if not key: raise SystemExit(f'Set {env_name} in .env to opt in to model evaluation.')
    run=Path(run); tasks=read_tasks(run)
    if text_only:
        # One representative per family avoids turning the ablation into a second full benchmark run.
        chosen=[]; seen=set()
        for t in tasks:
            if t['family'] not in seen: chosen.append(t); seen.add(t['family'])
        tasks=chosen
    tasks=tasks[:limit] if limit else tasks; done=0
    for task in tasks:
        gt=json.loads((run/task['ground_truth']).read_text(encoding='utf-8')); kind=task['answer_type']; raw=''; claude_has_text=True
        finish_reason=None; usage=None
        if provider=='claude':
            content=[]
            if not text_only:
                for rel in task['images']:
                    data=base64.b64encode((run/rel).read_bytes()).decode()
                    content.append({'type':'image','source':{'type':'base64','media_type':'image/png','data':data}})
            content.append({'type':'text','text':task['prompt']})
            # This Claude model rejects temperature as deprecated; retain its provider default and set high effort.
            body={'model':model,'max_tokens':16384,'output_config':{'effort':'high'},'messages':[{'role':'user','content':content}]}
            url='https://api.anthropic.com/v1/messages'; headers={'x-api-key':key,'anthropic-version':'2023-06-01','Content-Type':'application/json'}
        else:
            content=[{'type':'text','text':task['prompt']}]
            if not text_only:
                for rel in task['images']:
                    data=base64.b64encode((run/rel).read_bytes()).decode()
                    content.append({'type':'image_url','image_url':{'url':'data:image/png;base64,'+data}})
            body={'model':model,'messages':[{'role':'user','content':content}],'max_tokens':16384,'temperature':0,'reasoning':{'effort':'high'}}
            url='https://openrouter.ai/api/v1/chat/completions'; headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','HTTP-Referer':'http://localhost','X-Title':'VisionForge Finance QA'}
        start=time.time(); raw=''; err=None; status='error'; pred=''
        try:
            req=urllib.request.Request(url,data=json.dumps(body).encode(),headers=headers)
            with urllib.request.urlopen(req,timeout=120) as res: data=json.loads(res.read())
            usage=data.get('usage')
            if provider=='claude':
                raw=' '.join(x.get('text','') for x in data.get('content',[]) if x.get('type')=='text')
                if not raw: raw=json.dumps(data.get('content',[]),ensure_ascii=False); claude_has_text=False
                finish_reason=data.get('stop_reason')
            else: raw=data.get('choices',[{}])[0].get('message',{}).get('content','')
            if provider!='claude': finish_reason=data.get('choices',[{}])[0].get('finish_reason')
            pred=parse_answer(raw,kind) if claude_has_text else ''; status='ok' if pred else 'unparsed'
        except urllib.error.HTTPError as e:
            detail=e.read().decode('utf-8','replace')
            err=f'HTTP {e.code}: {detail[:2000]}'; status='error'
        except Exception as e: err=str(e); status='error'
        is_correct=correct(pred,gt['answer'],kind) if status=='ok' else None
        rec={'task_id':task['task_id'],'family':task['family'],'difficulty':task['difficulty'],'provider':provider,'model':model+(' [text-only]' if text_only else ''),'status':status,'prompt':task['prompt'],'raw_response':raw,'prediction':pred,'reference':gt['answer'],'correct':is_correct,'latency_ms':round((time.time()-start)*1000),'timestamp':datetime.now(timezone.utc).isoformat(),'error':err,'mode':'text-only' if text_only else 'image+text','temperature':0 if provider!='claude' else None,'reasoning_effort':'high','max_tokens':16384,'finish_reason':finish_reason,'usage':usage}
        with (run/'responses.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(rec,ensure_ascii=False)+'\n')
        done+=1
    write_scores(run)
    from .report import render_report
    render_report(run)
    print(f"Recorded {done} {'text-only' if text_only else 'image+text'} attempts with {model} via {provider}.")

def main():
    p=argparse.ArgumentParser(); p.add_argument('--run',required=True); p.add_argument('--model',default='openai/gpt-6-luna'); p.add_argument('--provider',choices=['openrouter','claude'],default='openrouter'); p.add_argument('--text-only',action='store_true'); p.add_argument('--limit',type=int); a=p.parse_args(); evaluate(a.run,a.model,a.text_only,a.limit,a.provider)
if __name__=='__main__': main()
