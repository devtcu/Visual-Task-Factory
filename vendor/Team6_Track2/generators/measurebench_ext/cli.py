"""Generate and inspect an offline measurement-reading benchmark run."""
from __future__ import annotations
import argparse, base64, csv, hashlib, html, json, math, os, random, re, time, urllib.request, urllib.error
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge, FancyBboxPatch, Rectangle, Ellipse, PathPatch
from matplotlib.path import Path as MplPath
from .registry import GENERATORS, register, list_generators

VERSION = "measurebench_ext_v2"
TYPES = ("analog_dial", "vernier", "meniscus", "composite_panel")
DIFFICULTIES = ("easy", "medium", "hard")
STYLES = ("industrial_stainless", "navy_bench", "ivory_lab")
PALETTES = {
    "industrial_stainless": ("#e9edf0", "#f8fafb", "#26333b", "#b83b32", "#66757d"),
    "navy_bench": ("#132432", "#e9f0ee", "#203540", "#e0a83e", "#52717b"),
    "ivory_lab": ("#ddd2bf", "#fffdf6", "#303a39", "#b43c37", "#6f7970"),
}

def _style(seed):
    return STYLES[seed % len(STYLES)]

def _dial(ax, value, maximum, unit, ident, style, title=None, minor=10):
    metal, face, ink, accent, muted = PALETTES[style]
    ax.set_aspect("equal"); ax.set_xlim(-1.25,1.25); ax.set_ylim(-1.22,1.3); ax.axis("off")
    ax.add_patch(Circle((0,0),1.12,color=metal,ec="#5b6469",lw=2))
    ax.add_patch(Circle((0,0),1.01,color=face,ec="#7e898e",lw=1.2))
    ax.add_patch(Circle((0,0),.94,fill=False,ec=muted,lw=.7))
    for i in range(51):
        f=i/50; theta=math.radians(225-270*f)
        is_major=i%10==0; is_mid=i%5==0
        r0=.78 if is_major else (.84 if is_mid else .88)
        ax.plot([r0*math.cos(theta),.91*math.cos(theta)],[r0*math.sin(theta),.91*math.sin(theta)],color=ink,lw=1.35 if is_major else .65,zorder=3)
        if is_major:
            x,y=.67*math.cos(theta),.67*math.sin(theta)
            ax.text(x,y,f"{maximum*f:.0f}",ha="center",va="center",fontsize=7,color=ink,weight="bold")
    ax.text(0,-.15,unit,ha="center",fontsize=10,color=accent,weight="bold")
    ax.text(0,-.34,ident,ha="center",fontsize=6.5,color=ink,weight="bold")
    ax.text(0,-.48,"CLASS 1.0  •  IP65",ha="center",fontsize=5.8,color=muted)
    theta=math.radians(225-270*value/maximum)
    ax.plot([-.06*math.cos(theta+math.pi/2),.76*math.cos(theta)],[ -.06*math.sin(theta+math.pi/2),.76*math.sin(theta)],color=accent,lw=3.0,solid_capstyle="round",zorder=6)
    ax.add_patch(Circle((0,0),.09,color="#59646a",ec="#d9dfe1",lw=.8,zorder=7))
    if title: ax.text(0,1.18,title,ha="center",fontsize=8,color=ink,weight="bold")
    return {"needle_angle_deg":225-270*value/maximum,"needle_tip":[.76*math.cos(theta),.76*math.sin(theta)],"scale_min":0,"scale_max":maximum}

def _render(kind, values, style, difficulty, outpath, ids):
    metal, face, ink, accent, muted = PALETTES[style]
    scale_ink = "#e2eaeb" if style == "navy_bench" else ink
    scale_muted = "#aec0c3" if style == "navy_bench" else muted
    fig=plt.figure(figsize=(7.2,5.2),dpi=170,facecolor=metal)
    header = face if style == "navy_bench" else ink
    fig.text(.5,.965,"CALIBRATION & INSTRUMENTATION  /  FIELD INSPECTION",ha="center",fontsize=9,color=header,weight="bold")
    fig.text(.5,.925,f"INSTRUMENT {ids[0]}  •  CAL-2026",ha="center",fontsize=7,color=("#afc0c5" if style == "navy_bench" else muted))
    geometry=[]
    dial_axes=[]
    if kind in ("analog_dial","composite_panel"):
        if kind=="analog_dial":
            ax=fig.add_axes([.20,.10,.60,.78]); geometry.append(_dial(ax,values[0],10,"bar",ids[0],style,minor=10)); dial_axes.append(ax)
        else:
            ax=fig.add_axes([.08,.21,.40,.63]); geometry.append(_dial(ax,values[0],10,"bar",ids[0],style)); dial_axes.append(ax)
            ax=fig.add_axes([.53,.21,.40,.63]); geometry.append(_dial(ax,values[1],10,"bar",ids[1],style)); dial_axes.append(ax)
            fig.text(.5,.13,"REFERENCE PRESSURE STATION     •     TOLERANCE TAG: 0.4 bar",ha="center",fontsize=7,color=header,weight="bold")
    elif kind=="vernier":
        ax=fig.add_axes([.07,.20,.86,.65]); ax.set_xlim(0,10); ax.set_ylim(0,3); ax.axis("off")
        ax.add_patch(FancyBboxPatch((.25,.45),9.5,1.55,boxstyle="round,pad=.05",fc=metal,ec=muted,lw=1.2))
        ax.plot([.7,9.3],[1.2,1.2],color=ink,lw=2)
        for i in range(81):
            x=.8+i*.1; h=.55 if i%10==0 else (.34 if i%5==0 else .20)
            ax.plot([x,x],[1.2,1.2+h],color=scale_ink,lw=.9 if i%10==0 else .55)
            if i%10==0: ax.text(x,1.85,str(i//10),ha="center",fontsize=6,color=scale_ink)
        v=values[0]; x=.8+v
        ax.add_patch(Rectangle((x-.30,.55),.60,1.65,fc=face,ec=accent,lw=1.4,alpha=.96))
        ax.plot([x,x],[.53,1.72],color=accent,lw=1.3)
        for i in range(11):
            xx=x-.45+i*.09
            ax.plot([xx,xx],[.60,.92 if i%5==0 else .78],color=ink,lw=.7)
        ax.text(5,2.55,"STAINLESS VERNIER CALIPER  •  0.01 cm / DIV",ha="center",fontsize=8,color=scale_ink,weight="bold")
        ax.text(5,.18,ids[0]+"     MAIN SCALE: cm     •     CLOSE JAWS AT ZERO",ha="center",fontsize=6.5,color=scale_muted)
        geometry.append({"main_scale_cm":math.floor(v*10)/10,"vernier_cm":round(v-math.floor(v*10)/10,2),"reading_cm":v,"jaw_position":x})
    elif kind=="meniscus":
        ax=fig.add_axes([.25,.08,.50,.82]); ax.set_xlim(0,5); ax.set_ylim(0,10); ax.axis("off")
        ax.add_patch(FancyBboxPatch((1,.6),3,8.5,boxstyle="round,pad=.12,rounding_size=.4",fc=face,ec=muted,lw=2,alpha=.8))
        # The printed 0..100 mL scale spans y=1..9. Use that same scale
        # for the liquid; v1's unrelated .062 slope produced wrong readings.
        level=1.0+values[0]*.08
        liquid_path=MplPath([(1.14,.75),(3.86,.75),(3.86,level+.12),(3.15,level+.12),(2.5,level),(1.85,level+.12),(1.14,level+.12),(1.14,.75)],
                            [MplPath.MOVETO,MplPath.LINETO,MplPath.LINETO,MplPath.CURVE3,MplPath.CURVE3,MplPath.CURVE3,MplPath.CURVE3,MplPath.CLOSEPOLY])
        ax.add_patch(PathPatch(liquid_path,fc="#8eb7bd",ec="none",alpha=.78))
        meniscus_path=MplPath([(1.14,level+.12),(1.85,level+.12),(2.5,level),(3.15,level+.12),(3.86,level+.12)],
                              [MplPath.MOVETO,MplPath.CURVE3,MplPath.CURVE3,MplPath.CURVE3,MplPath.CURVE3])
        ax.add_patch(PathPatch(meniscus_path,fill=False,ec="#648d94",lw=1.3))
        for i in range(21):
            y=1+i*.4
            ax.plot([3.15,3.75 if i%5==0 else 3.48],[y,y],color=scale_ink,lw=.9 if i%5==0 else .55)
            if i%5==0: ax.text(3.9,y,str(i*5),va="center",fontsize=6,color=scale_ink)
        ax.text(2.5,9.5,"BOROSILICATE  •  100 mL",ha="center",fontsize=8,color=scale_ink,weight="bold")
        ax.text(2.5,.12,ids[0]+"   READ BOTTOM OF CONCAVE MENISCUS",ha="center",fontsize=6,color=scale_muted)
        geometry.append({"meniscus_bottom_y":level,"calibration_ml_per_unit_height":12.5,
                         "scale_zero_y":1.0,"scale_max_y":9.0,"scale_max_ml":100,
                         "reading_ml":values[0]})
    # Fixed canvas coordinates make independent pixel measurements possible.
    # A tight bounding box would change the origin according to text/font bounds.
    fig.canvas.draw()
    for axis,g in zip(dial_axes,geometry):
        cx,cy=axis.transData.transform((0,0)); rx,_=axis.transData.transform((1,0))
        g["center_px"]=[float(cx),float(fig.bbox.height-cy)]
        g["unit_radius_px"]=float(rx-cx)
        g["needle_color"]=accent
    fig.savefig(outpath)
    plt.close(fig)
    return geometry

@register("analog_dial")
def render_analog_dial(values,style,difficulty,outpath,ids):
    return _render("analog_dial",values,style,difficulty,outpath,ids)

@register("vernier")
def render_vernier(values,style,difficulty,outpath,ids):
    return _render("vernier",values,style,difficulty,outpath,ids)

@register("meniscus")
def render_meniscus(values,style,difficulty,outpath,ids):
    return _render("meniscus",values,style,difficulty,outpath,ids)

@register("composite_panel")
def render_composite_panel(values,style,difficulty,outpath,ids):
    return _render("composite_panel",values,style,difficulty,outpath,ids)

def _samples(kind, seed, difficulty):
    r=random.Random(seed); d=DIFFICULTIES.index(difficulty)
    if kind=="analog_dial": return [round(r.randint(10,45)*.2,1)]
    if kind=="vernier": return [round(r.randint(240,780)*.01,2)]
    if kind=="meniscus": return [r.choice([20,25,30,35,40,45,50,55,60,65,70,75,80])]
    a=r.choice([2.4,3.2,4.0,5.2,6.0]); delta=r.choice([.4,.8,1.2])
    readings=[a,round(min(9.2,a+delta),1)]
    if r.choice((False,True)):
        readings.reverse()
    return readings

def _questions(kind, ids, vals, difficulty):
    unit={"analog_dial":"bar","vernier":"cm","meniscus":"mL","composite_panel":"bar"}[kind]
    rows=[(f"What does instrument {ids[0]} read? Include the unit.",vals[0],unit,"single_reading")]
    if kind=="composite_panel":
        diff=round(abs(vals[0]-vals[1]),1)
        rows += [(f"Which gauge indicates higher pressure, {ids[0]} or {ids[1]}?",ids[0] if vals[0]>vals[1] else ids[1],"label","comparison"),
                 (f"What is the pressure difference between {ids[0]} and {ids[1]}? Report in bar to the nearest 0.2.",diff,"bar","difference")]
    elif kind=="analog_dial": rows.append((f"Read {ids[0]} to the nearest marked minor division.",vals[0],unit,"precision"))
    elif kind=="vernier": rows.append((f"What is the jaw opening on {ids[0]} in centimeters?",vals[0],unit,"precision"))
    elif kind=="meniscus": rows.append((f"Using the bottom of the concave meniscus, what volume is shown in {ids[0]}? Include mL.",vals[0],unit,"meniscus_convention"))
    return rows

def _fmt(value): return f"{value:g}"

def parse_numeric_prediction(text):
    """Extract the final scalar, accepting common fraction and Unicode minus forms."""
    text=text.replace("−","-")
    pattern=r"[-+]?\d+\s*/\s*[-+]?\d+|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?"
    found=re.findall(pattern,text)
    if not found: return None
    token=found[-1]
    try:
        if "/" in token:
            a,b=token.split("/"); value=float(a)/float(b)
        else: value=float(token)
        return value if math.isfinite(value) else None
    except (ValueError,ZeroDivisionError): return None

def grade_prediction(answer, text):
    unit=answer["unit"]
    normalized=html.unescape(text).lower().replace("μ","µ")
    if unit=="label":
        ok=str(answer["value"]).lower() in normalized
        return {"parsed_value":None,"unit_correct":ok,"value_correct":ok}
    unit_alias={"ml":("ml","milliliter","millilitre"),"cm":("cm","centimeter","centimetre"),"bar":("bar",)}.get(unit.lower(),(unit.lower(),))
    unit_ok=any(alias in normalized for alias in unit_alias)
    number=parse_numeric_prediction(text)
    value_ok=number is not None and answer["interval"][0]<=number<=answer["interval"][1]
    return {"parsed_value":number,"unit_correct":unit_ok,"value_correct":value_ok}

def generate_run(out, num_per_type=9, seed=73, types=TYPES, difficulties=DIFFICULTIES):
    out=Path(out); (out/"images").mkdir(parents=True,exist_ok=True); (out/"counterfactuals").mkdir(exist_ok=True); (out/"scenes").mkdir(exist_ok=True)
    tasks=[]; prompts=[]; rejected=[]; pairs=[]; index=0
    for kind in types:
        for j in range(num_per_type):
            difficulty=difficulties[j%len(difficulties)]; sample_seed=seed+j*1009+TYPES.index(kind)*100003
            vals=_samples(kind,sample_seed,difficulty); style=_style(sample_seed)
            ids=["P-101","P-102"] if kind=="composite_panel" else (["VC-07"] if kind=="vernier" else (["LG-22"] if kind=="meniscus" else ["PG-104"]))
            task_id=f"mbext_{kind}_{sample_seed}_{j:02d}"
            image=Path("images")/(task_id+".png"); scene=Path("scenes")/(task_id+".json")
            g=GENERATORS[kind](vals,style,difficulty,out/image,ids)
            sha=hashlib.sha256((out/image).read_bytes()).hexdigest()
            for qidx,(question,answer,unit,qtype) in enumerate(_questions(kind,ids,vals,difficulty)):
                if isinstance(answer,str): interval=[answer,answer]
                else:
                    radius={"analog_dial":.099,"vernier":.0049,"meniscus":2.49,"composite_panel":.099}[kind]
                    interval=[round(answer-radius,4),round(answer+radius,4)]
                row={"task_id":task_id+f"_q{qidx}","seed":sample_seed,"generator":kind,"difficulty":difficulty,"image":image.as_posix(),"scene":scene.as_posix(),"question":question,"answer":{"value":answer,"unit":unit,"interval":interval},"answer_type":"measurement" if unit!="label" else "label","validator":"interval_and_unit","generator_version":VERSION,"image_sha256":sha,"render_style":style,"question_type":qtype}
                tasks.append(row); prompts.append({"task_id":row["task_id"],"image":row["image"],"prompt":question,"model_visible":True})
            if kind=="analog_dial":
                twin_value=round(vals[0]+.2,1); twin_rel=(Path("counterfactuals")/(task_id+"_plus_one_tick.png"))
                twin_geom=GENERATORS[kind]([twin_value],style,difficulty,out/twin_rel,ids)
                pair={"pair_id":task_id+"_one_tick","image_a":image.as_posix(),"image_b":twin_rel.as_posix(),"seed":sample_seed,"generator":kind,"instrument_id":ids[0],"style":style,"difficulty":difficulty,"value_a":vals[0],"value_b":twin_value,"delta":.2,"geometry_a":g,"geometry_b":twin_geom,"sha256_a":sha,"sha256_b":hashlib.sha256((out/twin_rel).read_bytes()).hexdigest()}
                pairs.append(pair)
                q={"task_id":pair["pair_id"],"seed":sample_seed,"generator":kind,"difficulty":difficulty,"image":image.as_posix(),"images":[image.as_posix(),twin_rel.as_posix()],"scene":scene.as_posix(),"question":f"Comparing image A with image B, how much did instrument {ids[0]} increase? Report in bar.","answer":{"value":.2,"unit":"bar","interval":[.101,.299]},"answer_type":"measurement","validator":"interval_and_unit","generator_version":VERSION,"image_sha256":sha,"render_style":style,"question_type":"one_tick_counterfactual"}
                tasks.append(q); prompts.append({"task_id":q["task_id"],"image":q["image"],"images":q["images"],"prompt":q["question"],"model_visible":True})
            spec={"seed":sample_seed,"generator":kind,"difficulty":difficulty,"instrument_ids":ids,"style":style,"values":vals,"units":["bar" if kind in ("analog_dial","composite_panel") else ("cm" if kind=="vernier" else "mL")],"geometry":g,"image_sha256":sha,"questions":[t for t in tasks if t["task_id"].startswith(task_id)]}
            (out/scene).write_text(json.dumps(spec,indent=2),encoding="utf-8")
            index+=1
    def dump(name, rows): (out/name).write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf-8")
    dump("tasks.jsonl",tasks); dump("model_prompts.jsonl",prompts); dump("rejected_samples.jsonl",rejected); dump("counterfactuals.jsonl",pairs)
    (out/"responses.jsonl").touch(exist_ok=True)
    with (out/"scores.csv").open("w",newline="",encoding="utf-8") as f:
        csv.DictWriter(f,fieldnames=["task_id","status","parsed_value","parsed_unit","value_correct","unit_correct","correct","signed_error","absolute_error","latency_seconds"]).writeheader()
    (out/"references.json").write_text(json.dumps({"sources":[{"url":"https://flageval-baai.github.io/MeasureBenchPage/","note":"Task and instrument taxonomy reference. MeasureBench paper HTML is marked CC BY 4.0; no paper figures or code copied."},{"url":"https://www.wika.com/en-us/pressure_gauges.WIKA","note":"WIKA public product overview used as visual-convention reference only; all gauge visuals were independently drawn. No product images reused; manufacturer copyright/license terms remain with WIKA."},{"url":"https://www.mitutoyo.com/products/small-tool-instruments-and-data-management/calipers/","note":"Mitutoyo public caliper product overview used as visual-convention reference only; all caliper visuals were independently drawn. No product images reused; manufacturer copyright/license terms remain with Mitutoyo."},{"url":"https://huggingface.co/datasets/philokey/MeasureBench","note":"Dataset page could not be fetched in this environment; no files downloaded or reused; dataset license and current revision not verified."},{"url":"https://github.com/flageval-baai/MeasureBench","note":"Public implementation inspected for interface/evaluator behavior; repository license file was not confirmed, so no source code was vendored or copied."}]},indent=2),encoding="utf-8")
    (out/"run_meta.json").write_text(json.dumps({"seed":seed,"types":list(types),"num_per_type":num_per_type,"difficulties":list(difficulties),"version":VERSION,"model_evaluation":"not_run","accepted_samples":index,"counterfactual_pairs":len(pairs),"rejected_samples":0},indent=2),encoding="utf-8")
    make_contact_sheet(out); return out

def _lines(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]

def verify_run(run):
    run=Path(run); tasks=_lines(run/"tasks.jsonl"); scenes=list((run/"scenes").glob("*.json")); errors=[]
    for p in scenes:
        s=json.loads(p.read_text(encoding="utf-8")); ip=run/"images"/(p.stem+".png")
        if not ip.is_file(): errors.append(f"missing image: {ip.name}"); continue
        if hashlib.sha256(ip.read_bytes()).hexdigest()!=s["image_sha256"]: errors.append(f"image hash mismatch: {ip.name}")
        if not s.get("values") or not s.get("geometry"): errors.append(f"missing geometry or source value: {p.name}")
        if s["generator"]=="analog_dial":
            a=s["geometry"][0]["needle_angle_deg"]; expected=225-270*s["values"][0]/10
            if abs(a-expected)>1e-8: errors.append(f"dial mapping mismatch: {p.name}")
        if s["generator"]=="meniscus":
            g=s["geometry"][0]
            recovered=(g["meniscus_bottom_y"]-1.2)*g["calibration_ml_per_unit_height"]
            if abs(recovered-s["values"][0])>1e-7: errors.append(f"meniscus calibration mismatch: {p.name}")
            if not 1.2 < g["meniscus_bottom_y"] < 8.8: errors.append(f"meniscus level outside visible marks: {p.name}")
        if s["generator"]=="vernier":
            g=s["geometry"][0]
            recovered=g["jaw_position"]-.8
            if abs(recovered-s["values"][0])>1e-7: errors.append(f"vernier geometry mismatch: {p.name}")
            if round(recovered,2)!=round(s["values"][0],2): errors.append(f"vernier division mismatch: {p.name}")
        if s["generator"]=="composite_panel":
            for value,g in zip(s["values"],s["geometry"]):
                recovered=(225-g["needle_angle_deg"])*10/270
                if abs(recovered-value)>1e-7: errors.append(f"composite dial mapping mismatch: {p.name}")
    for pair in _lines(run/"counterfactuals.jsonl") if (run/"counterfactuals.jsonl").exists() else []:
        for key,hash_key in (("image_a","sha256_a"),("image_b","sha256_b")):
            f=run/pair[key]
            if not f.is_file(): errors.append(f"missing counterfactual image: {f.name}")
            elif hashlib.sha256(f.read_bytes()).hexdigest()!=pair[hash_key]: errors.append(f"counterfactual image hash mismatch: {f.name}")
        if abs((pair["value_b"]-pair["value_a"])-.2)>1e-9: errors.append(f"counterfactual is not one minor tick: {pair['pair_id']}")
        if pair["style"] not in STYLES or pair["geometry_a"][0]["scale_max"]!=pair["geometry_b"][0]["scale_max"]: errors.append(f"counterfactual style/scale mismatch: {pair['pair_id']}")
    if len(tasks)<1: errors.append("no task rows")
    return {"accepted":len(scenes),"questions":len(tasks),"errors":errors,"passed":not errors}

def make_contact_sheet(run):
    run=Path(run); files=sorted((run/"images").glob("*.png"))
    if not files: return
    cols=6; rows=math.ceil(len(files)/cols); fig,axs=plt.subplots(rows,cols,figsize=(15,rows*2.1),facecolor="#e8edf0")
    for ax,p in zip(axs.flat,files):
        ax.imshow(plt.imread(p)); ax.set_title(p.stem.replace("mbext_","")[:30],fontsize=5); ax.axis("off")
    for ax in list(axs.flat)[len(files):]: ax.axis("off")
    fig.tight_layout(pad=.5); fig.savefig(run/"contact_sheet.png",dpi=150); plt.close(fig)

def make_report(run):
    run=Path(run); tasks=_lines(run/"tasks.jsonl"); meta=json.loads((run/"run_meta.json").read_text()); status="not_run" if not (run/"responses.jsonl").stat().st_size else "responses recorded"
    response_map={r.get("task_id"):r for r in _lines(run/"responses.jsonl")} if (run/"responses.jsonl").stat().st_size else {}
    score_map={}
    if (run/"scores.csv").exists():
        with (run/"scores.csv").open(encoding="utf-8",newline="") as f: score_map={r["task_id"]:r for r in csv.DictReader(f)}
    valid=json.loads((run/"validation.json").read_text()) if (run/"validation.json").exists() else {"passed":False,"accepted":0,"errors":["validation not run"]}
    by_difficulty={d:sum(1 for t in tasks if t["difficulty"]==d) for d in DIFFICULTIES}
    by_type={kind:sum(1 for t in tasks if t["generator"]==kind) for kind in TYPES}
    cards=[]
    for t in tasks:
        value=t["answer"]["value"]; unit=t["answer"]["unit"]
        response=response_map.get(t["task_id"],{}); score=score_map.get(t["task_id"],{})
        reply=html.escape(str(response.get("raw_output","not_run")))
        score_text=("correct="+html.escape(str(score.get("correct","")))+" · error="+html.escape(str(score.get("signed_error","")))) if score else "no score"
        image_tags="".join(f'<img src="{html.escape(src)}">' for src in t.get("images",[t["image"]]))
        cards.append(f'<article>{image_tags}<b>{html.escape(t["generator"])} / {html.escape(t["difficulty"])}</b><p>{html.escape(t["question"])}</p><p>Reference: {html.escape(str(value))} {html.escape(unit)} · interval {t["answer"]["interval"]}</p><small>Model: {html.escape(response.get("status",status))} · {score_text} · SHA256 {t["image_sha256"][:12]}</small><blockquote>{reply}</blockquote></article>')
    summary=f'<h2>Run summary</h2><p>{meta["accepted_samples"]} images · {len(tasks)} question rows · model: {html.escape(status)} · validator: {"PASS" if valid["passed"] else "FAIL"} ({valid["accepted"]} accepted)</p><p>By difficulty: '+" · ".join(f"{d} {n}" for d,n in by_difficulty.items())+'<br>By task: '+" · ".join(f"{k} {n}" for k,n in by_type.items())+'</p><p>Validation errors: '+html.escape("; ".join(valid["errors"]) or "none")+'</p>'
    doc='<!doctype html><meta charset="utf-8"><title>MeasureBench Extension Gallery</title><style>body{font:14px system-ui;background:#eef2f4;color:#233;padding:24px}h1{margin-bottom:4px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:18px}article{background:#fff;padding:12px;border-radius:10px;box-shadow:0 2px 10px #0002}img{width:100%;height:210px;object-fit:contain;background:#e9edf0}small{color:#59666e}blockquote{margin:10px 0 0;padding:8px;background:#f1f4f5;white-space:pre-wrap}</style><h1>VisionForge · Measurement Reading Gallery</h1>'+summary+'<div class="grid">'+''.join(cards)+'</div>'
    (run/"report.html").write_text(doc,encoding="utf-8")

def evaluate_run(run, model, provider="openrouter"):
    if provider != "openrouter": raise ValueError("Only the OpenRouter-compatible provider is implemented")
    key=os.environ.get("OPENROUTER_API_KEY")
    if not key: raise RuntimeError("Set OPENROUTER_API_KEY to run model evaluation")
    run=Path(run); tasks=_lines(run/"tasks.jsonl"); response_path=run/"responses.jsonl"
    cache={}
    if response_path.exists():
        for old in _lines(response_path):
            if old.get("cache_key"): cache[old["cache_key"]]=old
    scores=[]
    for task in tasks:
        image_paths=task.get("images",[task["image"]]); encoded=[base64.b64encode((run/path).read_bytes()).decode("ascii") for path in image_paths]
        config={"model":model,"temperature":0,"max_tokens":128}
        cache_key=hashlib.sha256((task["image_sha256"]+task["question"]+json.dumps(config,sort_keys=True)).encode()).hexdigest()
        if cache_key in cache: result=cache[cache_key]
        else:
            payload={"model":model,"temperature":0,"max_tokens":128,"messages":[{"role":"user","content":[{"type":"text","text":task["question"]}]+[{"type":"image_url","image_url":{"url":"data:image/png;base64,"+b64}} for b64 in encoded]}]}
            req=urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json","HTTP-Referer":"https://localhost","X-Title":"VisionForge MeasureBench Extension"})
            start=time.time(); raw=""; status="ok"; usage={};
            try:
                with urllib.request.urlopen(req,timeout=120) as resp: raw=resp.read().decode(); response=json.loads(raw)
                content=response["choices"][0]["message"]["content"]; usage=response.get("usage",{})
            except Exception as exc:
                status="error"; content=""; raw=str(exc)
            result={"task_id":task["task_id"],"cache_key":cache_key,"model":model,"provider":provider,"status":status,"raw_output":content,"raw_response":raw,"latency_seconds":round(time.time()-start,3),"usage":usage,"request_config":config,"truncated":False}
            with response_path.open("a",encoding="utf-8") as f: f.write(json.dumps(result)+"\n")
        answer=task["answer"]; content=result.get("raw_output",""); graded=grade_prediction(answer,content); number=graded["parsed_value"]
        unit_ok=graded["unit_correct"]; value_ok=graded["value_correct"]
        scores.append({"task_id":task["task_id"],"status":result["status"],"parsed_value":number,"parsed_unit":answer["unit"] if unit_ok else "","value_correct":value_ok,"unit_correct":unit_ok,"correct":bool(value_ok and unit_ok) if result["status"]=="ok" else "","signed_error":None if number is None or answer["unit"]=="label" else round(number-answer["value"],6),"absolute_error":None if number is None or answer["unit"]=="label" else round(abs(number-answer["value"]),6),"latency_seconds":result.get("latency_seconds")})
    with (run/"scores.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(scores[0]) if scores else ["task_id"]); writer.writeheader(); writer.writerows(scores)
    meta=json.loads((run/"run_meta.json").read_text()); meta["model_evaluation"]={"provider":provider,"model":model,"attempts":len(scores)}; (run/"run_meta.json").write_text(json.dumps(meta,indent=2))

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    sub.add_parser("list")
    g=sub.add_parser("generate"); g.add_argument("--types",default=",".join(TYPES)); g.add_argument("--num-per-type",type=int,default=9); g.add_argument("--seed",type=int,default=73); g.add_argument("--difficulties",default=",".join(DIFFICULTIES)); g.add_argument("--out",default="visionforge/runs/measurebench_demo"); g.add_argument("--no-api",action="store_true")
    for c in ("verify","report"):
        q=sub.add_parser(c); q.add_argument("--run",required=True)
    e=sub.add_parser("evaluate"); e.add_argument("--run",required=True); e.add_argument("--model",required=True); e.add_argument("--provider",default="openrouter")
    a=p.parse_args()
    if a.cmd=="list": print("\n".join(f"{t}: procedural instrument renderer" for t in list_generators())); return
    if a.cmd=="generate":
        generate_run(a.out,a.num_per_type,a.seed,a.types.split(","),a.difficulties.split(",")); print(f"Generated {a.out}"); return
    if a.cmd=="verify":
        result=verify_run(a.run); (Path(a.run)/"validation.json").write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2)); raise SystemExit(0 if result["passed"] else 1)
    if a.cmd=="evaluate":
        evaluate_run(a.run,a.model,a.provider); make_report(a.run); print(f"Recorded model responses and scores in {a.run}"); return
    make_report(a.run); print(f"Wrote {Path(a.run)/'report.html'}")

if __name__=="__main__": main()
