from __future__ import annotations
import random, re, html, json, csv, base64, os, time, urllib.request
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, timezone, timedelta
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
FAMILIES=['quantity','balance','price_rule']
DIFFICULTIES=['easy','medium','hard']
VENDORS=[('Asteron Components Ltd.','V-2084'),('Meridian Industrial Supply','V-5910'),('Northline Motion Systems','V-3367'),('Cobalt Ridge Materials','V-1742')]
BUYERS=[('Pine Harbor Distribution','PH-01'),('Redwood Industrial Group','RI-04'),('Summit Works Supply','SW-12')]
CATALOG=[('AX-104','Precision bearing assembly'),('AX-140','Precision bearing set'),('BR-208','Bronze pressure valve'),('BR-280','Bronze pressure-valve kit'),('CT-310','Carbon seal, industrial'),('CT-301','Carbon seal cartridge'),('DK-420','Drive coupling, keyed'),('DK-402','Drive coupling sleeve'),('EL-515','Control relay, 24 V'),('EL-551','Control relay base, 24 V'),('FM-630','Flow meter impeller'),('FM-603','Flow meter insert'),('GX-744','Gasket sheet, high-temp'),('GX-774','Gasket set, high-temp'),('HP-812','Hydraulic piston rod'),('HP-821','Hydraulic seal rod'),('LM-901','Linear guide carriage'),('LM-910','Linear guide rail')]
CENT=Decimal('0.01')
ROUNDING_INSTRUCTIONS = (
    "For both the authorized PO rate and the billed invoice rate, apply the line discount, "
    "then round the discounted unit price to the nearest USD cent using ROUND_HALF_UP "
    "(an exact half-cent rounds up). Compare those rounded unit rates. Multiply each positive "
    "difference by the combined billed quantity for that line, including linked split invoices, "
    "and sum the line overcharges. Do not offset an overcharge with an undercharge."
)
def D(v): return Decimal(str(v))
def money(v): return D(v).quantize(CENT,rounding=ROUND_HALF_UP)
def fmt(v): return f"{money(v):,.2f}"
def esc(v): return html.escape(str(v))
def q(v): return f"{D(v).quantize(Decimal('0.0001'),rounding=ROUND_HALF_UP):.4f}"

def make_scene(seed:int,difficulty:str,family:str,layout:int=0,attempt:int=0):
    rng=random.Random(f"finance:{seed}:{difficulty}:{family}:{attempt}")
    n={'easy':4,'medium':8,'hard':12}[difficulty]
    amended_lines=[min(2,n)] if difficulty in ('medium','hard') or family=='price_rule' else []
    if family=='price_rule' and difficulty=='hard': amended_lines=sorted(set(amended_lines+[n-2,n]))
    vendor,vendor_id=rng.choice(VENDORS); buyer,buyer_id=rng.choice(BUYERS)
    po_id=f"PO-{rng.randint(24000,89999)}"; invoice_id=f"INV-{rng.randint(41000,98999)}"
    invoice_date=date(2026,10,rng.randint(8,13)); as_of=date(2026,10,16)
    amendment_date=date(2026,10,rng.randint(2,20)) if difficulty in ('medium','hard') or family=='price_rule' else date(2026,9,28)
    selected=rng.sample(CATALOG,n); lines=[]
    for i,(sku,desc) in enumerate(selected,1):
        factor=6 if rng.random()<.20 else 1
        qty=6*rng.randint(4,12) if factor==6 else rng.randint(18,75)
        po_uom='EA' if factor==6 else rng.choice(['EA','PCS','BOX']); grn_uom='CASE' if factor==6 else po_uom
        unit=money(D(rng.randint(280,22000))/100)
        discount=D(rng.choice([0,2,3,5]))/100
        amended= i in amended_lines
        amended_unit=money(unit*(D('1.06') if rng.random()<.55 else D('0.97'))) if amended else unit
        # Two staggered partial receipts, with rejected units documented separately.
        r1_base=max(factor,int(qty*D('.55')/factor)*factor); r1=r1_base//factor
        rej1_raw=1 if r1>4 and rng.random()<.20 else 0; acc1_raw=r1-rej1_raw
        r2=max(0,(qty-r1_base)//factor-rng.randint(0,1)) if difficulty!='easy' else 0
        rej2_raw=1 if r2>4 and rng.random()<.12 else 0; acc2_raw=r2-rej2_raw
        acc1=acc1_raw*factor; acc2=acc2_raw*factor; rej1=rej1_raw*factor; rej2=rej2_raw*factor
        returned=min(max(0,acc1+acc2-1),rng.randint(1,3)) if ((difficulty=='hard' or family=='balance') and i==1) else 0
        billed=qty+(rng.randint(0,3) if (difficulty=='hard' and i==n) else 0)
        invoice_base=amended_unit if amended and invoice_date>=amendment_date else unit
        lines.append(dict(line=i,sku=sku,description=desc,uom=po_uom,grn_uom=grn_uom,conversion_factor=factor,qty_ordered=qty,
            po_unit_price=unit,amended=amended,amended_unit_price=amended_unit,amendment_effective=amendment_date.isoformat() if amended else None,
            discount_pct=discount*100,grn1_received_raw=r1,grn1_rejected_raw=rej1_raw,grn1_accepted_raw=acc1_raw,grn1_received=r1*factor,grn1_rejected=rej1,grn1_accepted=acc1,
            grn2_received_raw=r2,grn2_rejected_raw=rej2_raw,grn2_accepted_raw=acc2_raw,grn2_received=r2*factor,grn2_rejected=rej2,grn2_accepted=acc2,
            accepted_return_qty=returned,invoice_qty=billed,invoice_qty_total=billed,sibling_invoice_qty=0,invoice_unit_price=invoice_base))
    grn1_id=f"GRN-{rng.randint(51000,98999)}"; grn2_id=f"GRN-{rng.randint(51000,98999)}"
    while grn2_id==grn1_id: grn2_id=f"GRN-{rng.randint(51000,98999)}"
    credit_id=f"CM-{rng.randint(21000,88000)}"
    # One controlled price exception or a clean invoice; exception is limited to one line.
    split_target=lines[-1] if difficulty=='hard' and family in ('quantity','price_rule') else None
    sibling_invoice_id=f"INV-{rng.randint(41000,98999)}" if split_target else None
    while sibling_invoice_id==invoice_id: sibling_invoice_id=f"INV-{rng.randint(41000,98999)}"
    if split_target:
        split_target['sibling_invoice_qty']=max(1,split_target['invoice_qty']//2)
        split_target['invoice_qty']-=split_target['sibling_invoice_qty']
    exception_max=n-1 if split_target else n
    exception_lines=[]
    if family=='price_rule' and rng.random()<.72:
        max_exceptions=3 if difficulty=='hard' else 2 if difficulty=='medium' else 1
        exception_lines=sorted(rng.sample(range(1,exception_max+1),rng.randint(1,max_exceptions)))
    exception_line=exception_lines[0] if exception_lines else None
    for number in exception_lines:
        # Hard cases use near-equal competing rates to probe exact visual discrimination.
        bump_pool=['0.02','0.03','0.05','0.08','0.40'] if difficulty=='hard' else ['0.40','1.25','2.10']
        ln=lines[number-1]; ln['invoice_unit_price']=money(D(ln['invoice_unit_price'])+D(rng.choice(bump_pool)))
    for ln in lines:
        net_unit=money(D(ln['invoice_unit_price'])*(1-D(ln['discount_pct'])/100))
        po_base=ln['amended_unit_price'] if ln['amended'] and invoice_date>=date.fromisoformat(ln['amendment_effective']) else ln['po_unit_price']
        ln['invoice_net_unit']=net_unit; ln['effective_po_unit']=po_base; ln['effective_po_net_unit']=money(D(po_base)*(1-D(ln['discount_pct'])/100))
        ln['invoice_line_total']=money(net_unit*ln['invoice_qty'])
    subtotal=money(sum((ln['invoice_line_total'] for ln in lines),D(0)))
    freight=money(rng.choice(['35.00','48.50','72.00','110.00']))
    tax_rate=D('0.075'); tax=money((subtotal+freight)*tax_rate); invoice_total=money(subtotal+freight+tax)
    po_subtotal=money(sum((money(money(D(ln['po_unit_price'])*(1-D(ln['discount_pct'])/100))*ln['qty_ordered']) for ln in lines),D(0)))
    po_tax=money((po_subtotal+freight)*tax_rate); po_total=money(po_subtotal+freight+po_tax)
    sibling_invoice=None
    if split_target:
        sibline=dict(split_target); sibline['invoice_qty']=split_target['sibling_invoice_qty']; sibline['invoice_line_total']=money(sibline['invoice_net_unit']*sibline['invoice_qty'])
        sibsub=sibline['invoice_line_total']; sibtax=money(sibsub*tax_rate)
        sibling_invoice={'id':sibling_invoice_id,'date':invoice_date.isoformat(),'po_id':po_id,'terms':'Net 30','freight':D('0.00'),'tax_rate':tax_rate*100,'subtotal':sibsub,'tax':sibtax,'total':money(sibsub+sibtax),'lines':[sibline]}
    # A linked return credit, plus an unrelated unapplied credit as a distractor on medium/hard cases.
    retline=next((x for x in lines if x['accepted_return_qty']>0),None)
    credit_sub=money(retline['invoice_net_unit']*retline['accepted_return_qty']) if retline else D('0.00')
    linked_credit=money(credit_sub+money(credit_sub*tax_rate))
    unrelated_credit=money(rng.choice(['17.00','42.50','0.00'])) if difficulty!='easy' else D('0.00')
    payment1=money((invoice_total-linked_credit)*D('.42'))
    payment2=money((invoice_total-linked_credit)*D('.18')) if difficulty=='hard' else D('0.00')
    payment2_date='2026-10-18' if payment2 else None
    payment1_date='2026-10-14'
    pay_status='CLEARED'
    # Evidence/document IDs and display templates are intentionally independent of source ordering.
    scene=dict(schema_version=1,seed=seed,attempt_index=attempt,difficulty=difficulty,family=family,layout=layout,variant=['classic','split-column','warehouse-ledger'][layout%3],
        vendor={'name':vendor,'id':vendor_id,'address':f"{rng.randint(100,990)} Foundry Way, {rng.choice(['Cleveland OH 44114','Milwaukee WI 53202','Pittsburgh PA 15222'])}"},
        buyer={'name':buyer,'id':buyer_id,'address':f"{rng.randint(20,900)} Commerce Park, {rng.choice(['Columbus OH 43215','Detroit MI 48226','Buffalo NY 14202'])}"},
        purchase_order={'id':po_id,'date':'2026-09-24','delivery_terms':'FOB destination','status':'PARTIALLY RECEIVED','lines':lines,'subtotal':po_subtotal,'freight':freight,'tax':po_tax,'total':po_total},
        amendment={'id':f"AMD-{rng.randint(3000,8999)}",'date':amendment_date.isoformat(),'effective_date':amendment_date.isoformat(),'po_id':po_id,'line':next((x['line'] for x in lines if x['amended']),None),'lines':[x['line'] for x in lines if x['amended']]},
        grns=[{'id':grn1_id,'date':'2026-10-04','status':'POSTED','receipt_no':1},{'id':grn2_id,'date':'2026-10-09','status':'POSTED','receipt_no':2}],
        invoice={'id':invoice_id,'date':invoice_date.isoformat(),'po_id':po_id,'terms':'Net 30','freight':freight,'tax_rate':tax_rate*100,'subtotal':subtotal,'tax':tax,'total':invoice_total,'lines':lines},
        sibling_invoice=sibling_invoice,
        credit_memos=[{'id':credit_id,'date':'2026-10-11','invoice_id':invoice_id,'po_id':po_id,'reason':'Accepted return / quality allowance','amount':linked_credit,'tax_rate':tax_rate*100,'line':retline['line'] if retline else None},
          {'id':f"CM-{rng.randint(21000,88000)}",'date':'2026-10-12','invoice_id':f"INV-{rng.randint(41000,98999)}",'po_id':f"PO-{rng.randint(24000,89999)}",'reason':'Unapplied account credit','amount':unrelated_credit,'tax_rate':D('0'),'line':None}],
        payments=[{'id':f"PAY-{rng.randint(60000,99000)}",'date':payment1_date,'invoice_id':invoice_id,'amount':payment1,'status':pay_status},
          {'id':f"PAY-{rng.randint(60000,99000)}",'date':payment2_date or '2026-10-18','invoice_id':invoice_id,'amount':payment2,'status':'PENDING' if payment2 else 'VOID'}],
        as_of_date=as_of.isoformat(),tax_rate=tax_rate,freight=freight,invoice_total=invoice_total,linked_credit_total=linked_credit,
        rounding_policy='Discounted unit price rounded half-up to USD cent; line extensions rounded to cent; tax rounded half-up on merchandise subtotal plus freight.',
        unrelated_credit_total=unrelated_credit,price_exception_line=exception_line,price_exception_lines=exception_lines,quantity_target_line=(1 if family=='quantity' and difficulty=='hard' else rng.randint(1,n)))
    # Keep the quantity query SKU unambiguous and make invoice ID a join key, never a shortcut.
    return scene

def solve(scene):
    family=scene['family']; lines=scene['purchase_order']['lines']; invoice=scene['invoice']; ev=[]
    if family=='quantity':
        # Oracle provenance: compare combined billed quantity with accepted, converted receipts after returns.
        ln=next(x for x in lines if x['line']==scene['quantity_target_line'])
        receipts=sum(ln[f'grn{i}_accepted'] for i in (1,2)); eligible=min(ln['invoice_qty_total'],receipts-ln['accepted_return_qty'])
        unsupported=max(0,ln['invoice_qty_total']-eligible)
        ev=[scene['purchase_order']['id'],invoice['id'],scene['grns'][0]['id']]
        if scene['difficulty']!='easy': ev.append(scene['grns'][1]['id'])
        if ln['accepted_return_qty']: ev.append(scene['credit_memos'][0]['id'])
        trace={'sku':ln['sku'],'accepted_receipts':receipts,'accepted_returns':ln['accepted_return_qty'],'invoice_qty':ln['invoice_qty']}
        trace['eligible_units']=eligible; trace['unsupported_billed_units']=unsupported
        return str(unsupported),ev,trace
    if family=='balance':
        # Oracle provenance: invoice total minus linked credit memos and cleared same-invoice payments posted by the frozen as-of date.
        cleared=sum((p['amount'] for p in scene['payments'] if p['invoice_id']==invoice['id'] and p['status']=='CLEARED' and p['date']<=scene['as_of_date']),D(0))
        linked=sum((c['amount'] for c in scene['credit_memos'] if c['invoice_id']==invoice['id']),D(0))
        bal=money(invoice['total']-linked-cleared)
        ev=[invoice['id']]+[c['id'] for c in scene['credit_memos'] if c['invoice_id']==invoice['id']]+[p['id'] for p in scene['payments'] if p['status']=='CLEARED' and p['date']<=scene['as_of_date']]
        return f"${fmt(bal)}",ev,{'invoice_total':fmt(invoice['total']),'linked_credits':fmt(linked),'cleared_payments_as_of':fmt(cleared),'balance':fmt(bal),'as_of':scene['as_of_date']}
    # Oracle provenance: sum excess merchandise extensions against each effective, discounted PO rate.
    violations=[]; overcharge=D('0.00')
    for ln in invoice['lines']:
        effective=ln['amended_unit_price'] if ln['amended'] and invoice['date']>=ln['amendment_effective'] else ln['po_unit_price']
        limit=money(D(effective)*(1-D(ln['discount_pct'])/100)); billed=money(D(ln['invoice_unit_price'])*(1-D(ln['discount_pct'])/100))
        if billed>limit:
            violations.append(ln['line'])
            overcharge+=money((billed-limit)*ln['invoice_qty_total'])
    if len(violations)>3: raise ValueError('Too many price-rule violations')
    ev=[scene['purchase_order']['id'],scene['amendment']['id'],invoice['id']]
    return f"${fmt(overcharge)}",ev,{'violating_lines':violations,'overcharge':fmt(overcharge),'amendment_effective':scene['amendment']['effective_date']}

def question(scene):
    fam=scene['family']; inv=scene['invoice']; gt,ev,trace=solve(scene)
    if fam=='quantity':
        ln=next(x for x in scene['purchase_order']['lines'] if x['line']==scene['quantity_target_line'])
        qtext=f"Invoice control: for SKU {ln['sku']} on invoice {inv['id']}, calculate billed units minus units supported by the posted receipts. Convert each receipt to {ln['uom']}, exclude rejected quantities, subtract accepted returns, and cap eligible units at the combined billed quantity if billing was split. What is the unsupported billed quantity in {ln['uom']}? Answer with an integer only."
        at='integer'
    elif fam=='balance':
        qtext=f"What is the remaining payable balance for invoice {inv['id']} as of {scene['as_of_date']} after applying only credit memos linked to this invoice and payments marked CLEARED by that date? Answer in USD with two decimal places."
        at='currency'
    else:
        qtext=(f"Use the six document pages: the purchase order, two goods receipts, the main and split invoices, "
               f"and the authorized amendment. For invoice {inv['id']}, reconcile every billed line to the PO "
               f"price effective on the invoice date (including any authorized amendment). {ROUNDING_INSTRUCTIONS} "
               "What is the total merchandise overcharge in USD, excluding freight and tax? "
               "Return one amount to two decimal places.")
        at='currency'
    return qtext,gt,at,ev,trace

def make_docs(scene):
    docs=['purchase_order']
    if scene['difficulty']=='easy': docs+=['grn1']
    else: docs+=['grn1','grn2']
    docs+=['invoice']
    if scene['sibling_invoice'] is not None: docs+=['invoice_sibling']
    if (scene['difficulty'] in ('medium','hard') and scene['family'] in ('quantity','balance')) or scene['family']=='balance': docs+=['credit_memo']
    if scene['family']=='balance': docs+=['ap_ledger']
    if scene['family']=='price_rule': docs+=['amendment']
    if scene['difficulty']=='hard' and scene['family'] not in ('balance',) and scene['sibling_invoice'] is None: docs+=['ap_ledger']
    # Stable unique render order and no more than six page images.
    ordered=['purchase_order','grn1','grn2','invoice','invoice_sibling','credit_memo','amendment','ap_ledger']
    return [d for d in ordered if d in docs]

def render_svg(scene,kind,layout_override=None):
    W,H=1654,2339; ink='#203247'; gray='#627386'; navy='#183858'; teal='#19877e'; gold='#e0a044'; red='#b54650'; purple='#55447e'
    doc={"purchase_order":"PURCHASE ORDER","grn1":"GOODS RECEIPT · 01","grn2":"GOODS RECEIPT · 02","invoice":"TAX INVOICE","invoice_sibling":"TAX INVOICE · SPLIT BILLING","credit_memo":"SUPPLIER CREDIT MEMO","amendment":"PURCHASE ORDER AMENDMENT","ap_ledger":"ACCOUNTS PAYABLE · TRANSACTION LEDGER"}[kind]
    c={'purchase_order':navy,'grn1':'#1b6858','grn2':'#1b6858','invoice':purple,'invoice_sibling':'#3d5f77','credit_memo':red,'amendment':gold,'ap_ledger':'#394d61'}[kind]
    layout=scene['layout'] if layout_override is None else layout_override
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">','<rect width="100%" height="100%" fill="#fff"/>']
    if layout==0: parts.append(f'<rect x="0" y="0" width="{W}" height="210" fill="{c}"/>')
    elif layout==1:
        parts.append(f'<rect x="0" y="0" width="1040" height="210" fill="{c}"/><rect x="1040" y="0" width="614" height="210" fill="#f0f4f8"/><rect x="0" y="200" width="{W}" height="10" fill="{c}"/>')
    else:
        parts.append(f'<rect x="0" y="0" width="{W}" height="34" fill="{c}"/><rect x="0" y="34" width="28" height="176" fill="{c}"/><rect x="28" y="34" width="{W-28}" height="176" fill="#edf2f6"/>')
    def t(x,y,s,size=24,color=ink,bold=False): parts.append(f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="{size}" fill="{color}" font-weight="{700 if bold else 400}">{esc(s)}</text>')
    def r(x,y,w,h,fill='#f4f7fa',stroke='none',rx=0): parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" rx="{rx}"/>')
    def line(x1,y1,x2,y2,col='#d7e0e8',sw=2): parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{sw}"/>')
    vendor=scene['vendor']; buyer=scene['buyer']; po=scene['purchase_order']; inv=scene['invoice']; docinv=scene['sibling_invoice'] if kind=='invoice_sibling' else inv; lines=po['lines']
    # Different top treatments by issuer document type.
    head='#ffffff' if layout<2 else navy; palet='#d7eee7' if layout<2 else gray
    if kind=='grn1' or kind=='grn2':
        parts.append(f'<rect x="0" y="210" width="28" height="2129" fill="{teal}"/>'); t(80,78,'IRONWOOD DISTRIBUTION · RECEIVING',25,palet,True); t(80,150,doc,38,head,True)
    elif kind in ('invoice','invoice_sibling'):
        t(78,72,vendor['name'].upper(),30,palet,True); t(78,145,'TAX INVOICE · SPLIT 2' if kind=='invoice_sibling' else 'TAX INVOICE',43,head,True); t(1240,84,'DOCUMENT COPY',18,palet,True)
    elif kind=='credit_memo':
        t(78,72,vendor['name'].upper(),28,palet,True); t(78,145,'CREDIT ADVICE',42,head,True)
    elif kind=='amendment':
        t(78,74,buyer['name'].upper(),27,palet,True); t(78,148,'AUTHORIZED CHANGE ORDER',39,head,True)
    else:
        t(78,73,buyer['name'].upper(),31,palet,True); t(78,148,doc,42,head,True)
    docid={'purchase_order':po['id'],'grn1':scene['grns'][0]['id'],'grn2':scene['grns'][1]['id'],'invoice':inv['id'],'invoice_sibling':docinv['id'],'credit_memo':scene['credit_memos'][0]['id'],'amendment':scene['amendment']['id'],'ap_ledger':f"AP-{inv['id']}"}[kind]
    idcolor='#ffffff' if layout==0 else navy
    t(1200,150,docid,27,idcolor,True)
    parts.append(f'<rect x="1480" y="48" width="132" height="64" rx="8" fill="none" stroke="{idcolor}" stroke-width="2"/>')
    t(1494,76,'CONTROLLED',13,idcolor,True); t(1508,98,'DOCUMENT',13,idcolor,True)
    if kind=='purchase_order':
        t(80,265,'SUPPLIER',18,gray,True); t(80,310,vendor['name'],27,ink,True); t(80,350,vendor['address'],19,gray)
        t(870,265,'SHIP TO / BUYER',18,gray,True); t(870,310,buyer['name'],27,ink,True); t(870,350,buyer['address'],19,gray)
        meta=[('ORDER DATE',po['date']),('REQUESTED DELIVERY','2026-10-12'),('PAYMENT TERMS','Net 30'),('STATUS',po['status'])]
    elif kind in ('grn1','grn2'):
        g=scene['grns'][int(kind[-1])-1]; t(80,280,'RECEIVING SITE',18,gray,True); t(80,325,buyer['address'],24,ink); t(900,280,'SUPPLIER / PO',18,gray,True); t(900,325,vendor['name'],24,ink); t(900,365,po['id'],22,gray)
        meta=[('POSTED DATE',g['date']),('RECEIPT STATUS',g['status']),('CARRIER','Northstar Freight'),('DOCK','WH-03')]
    elif kind in ('invoice','invoice_sibling'):
        t(80,265,'BILL TO',18,gray,True); t(80,310,buyer['name'],27,ink,True); t(80,350,buyer['address'],19,gray); t(880,265,'REMIT TO',18,gray,True); t(880,310,vendor['name'],26,ink,True); t(880,350,vendor['address'],19,gray)
        meta=[('INVOICE DATE',docinv['date']),('PURCHASE ORDER',docinv['po_id']),('PAYMENT TERMS',docinv['terms']),('DUE DATE',(date.fromisoformat(docinv['date'])+timedelta(days=30)).isoformat())]
    elif kind=='credit_memo':
        cm=scene['credit_memos'][0]; t(80,280,'ISSUED TO',18,gray,True); t(80,325,buyer['name'],27,ink,True); t(850,280,'CREDIT RELATES TO',18,gray,True); t(850,325,inv['id'],27,ink,True); t(80,390,'Reason: Accepted return / quality allowance',22,gray)
        meta=[('CREDIT DATE',cm['date']),('PO REFERENCE',cm['po_id']),('APPLICATION','Linked to invoice'),('CREDIT STATUS','APPROVED')]
    elif kind=='amendment':
        t(80,280,'SUPPLIER',18,gray,True); t(80,325,vendor['name'],27,ink,True); t(850,280,'ORIGINAL ORDER',18,gray,True); t(850,325,po['id'],27,ink,True)
        meta=[('AMENDMENT DATE',scene['amendment']['date']),('EFFECTIVE DATE',scene['amendment']['effective_date']),('APPROVAL','AUTHORIZED'),('SCOPE','Revised unit price')]
    else:
        t(80,275,'SUPPLIER ACCOUNT',18,gray,True); t(80,320,vendor['name'],27,ink,True); t(850,275,'AS-OF DATE',18,gray,True); t(850,320,scene['as_of_date'],27,ink,True)
        meta=[('ACCOUNT',vendor['id']),('CURRENCY','USD'),('TERMS','Net 30'),('DOCUMENT','Invoice activity')]
    if kind!='ap_ledger':
        my=445
        for i,(lab,val) in enumerate(meta):
            x=80+i*380; r(x,my,350,96,'#f2f5f8',rx=8); t(x+18,my+32,lab,17,gray,True); t(x+18,my+70,val,23,ink,True)
    # Main body: issuer-specific table content, shared line items remain tied to canonical records.
    if kind in ('purchase_order','invoice','invoice_sibling','amendment'):
        top=610 if kind!='amendment' else 630
        if kind=='amendment': t(80,585,'Changes apply only on and after the effective date shown above.',20,gray)
        is_invoice=kind in ('invoice','invoice_sibling')
        headers={'purchase_order':['LINE','SKU','DESCRIPTION','QTY','UOM','UNIT PRICE','DISC.'], 'invoice':['LINE','ITEM / SKU','DESCRIPTION','BILLED QTY','UOM','UNIT PRICE','DISC.','EXTENDED'], 'invoice_sibling':['LINE','ITEM / SKU','DESCRIPTION','BILLED QTY','UOM','UNIT PRICE','DISC.','EXTENDED'], 'amendment':['LINE','SKU','DESCRIPTION','OLD UNIT','NEW UNIT','EFFECTIVE']}[kind]
        # Keep the extended amount comfortably inside the right table margin.
        xs={'purchase_order':[80,180,360,1030,1170,1310,1490], 'invoice':[80,165,330,850,1025,1145,1300,1430], 'invoice_sibling':[80,165,330,850,1025,1145,1300,1430], 'amendment':[80,180,360,880,1120,1380]}[kind]
        r(70,top,1510,56,c,rx=4)
        for x,h in zip(xs,headers): t(x,top+37,h,18,'#fff',True)
        rowh=76 if len(lines)<=8 else 64
        amendment_row=0
        for i,ln in enumerate(lines):
            if kind=='amendment':
                if ln['line'] not in scene['amendment']['lines']: continue
                rowindex=amendment_row; amendment_row+=1
            else: rowindex=i
            y=top+56+rowindex*rowh
            if y+rowh>top+56+16*rowh: break
            r(70,y,1510,rowh,'#f5f7fa' if i%2==0 else '#fff')
            po_unit=ln['amended_unit_price'] if ln['amended'] else ln['po_unit_price']
            if kind=='purchase_order': vals=[ln['line'],ln['sku'],ln['description'],ln['qty_ordered'],ln['uom'],f"${fmt(ln['po_unit_price'])}",f"{ln['discount_pct']}%"]
            elif is_invoice:
                source=next((x for x in docinv['lines'] if x['line']==ln['line']),None)
                if source is None: continue
                vals=[source['line'],source['sku'],source['description'],source['invoice_qty'],source['uom'],f"${fmt(source['invoice_unit_price'])}",f"{source['discount_pct']}%",f"${fmt(source['invoice_line_total'])}"]
            else:
                vals=[ln['line'],ln['sku'],ln['description'],f"${fmt(ln['po_unit_price'])}",f"${fmt(ln['amended_unit_price'])}",scene['amendment']['effective_date']]
            for x,v in zip(xs,vals): t(x,y+rowh//2+7,v,19,ink,x==xs[0])
            line(70,y+rowh,1580,y+rowh,'#dfe5eb',1)
        row_count=len(scene['amendment']['lines']) if kind=='amendment' else len(lines)
        bottom=top+56+row_count*rowh+35
        if is_invoice:
            for i,(label,val) in enumerate([('Merchandise subtotal',docinv['subtotal']),('Freight',docinv['freight']),('Tax 7.50%',docinv['tax']),('INVOICE TOTAL',docinv['total'])]):
                y=bottom+i*54; t(1030,y,label,22,gray,i==3); t(1410,y,f"${fmt(val)}",24,ink,i==3); line(1010,y+15,1570,y+15)
            if kind=='invoice':
                ay=bottom+245; r(80,ay,1500,118,'#f4f6fa',rx=8); t(105,ay+38,'REMITTANCE ADVICE',17,gray,True); t(105,ay+77,f"Quote {docinv['id']} and PO {docinv['po_id']} on payment. Terms {docinv['terms']}.",19,ink); t(105,ay+103,'Disputes should identify the invoice line and related receiving record.',16,gray)
            t(80,2140,'Please reference invoice number on remittance. Disputes must be submitted within 10 business days.',17,gray)
        if kind=='amendment':
            ay=bottom+145; r(80,ay,1500,128,'#fff8e9',rx=8); t(105,ay+38,'CHANGE AUTHORIZATION',18,'#8a6222',True); t(105,ay+77,'Revised commercial terms approved for the stated effective date.',19,ink); line(1050,ay+82,1535,ay+82,'#a99068',1); t(1050,ay+112,'AUTHORIZED BUYER',15,gray,True)
        if kind=='purchase_order':
            pord=scene['purchase_order']
            for i,(label,val) in enumerate([('Merchandise subtotal',pord['subtotal']),('Freight allowance',pord['freight']),('Estimated tax 7.50%',pord['tax']),('ORDER TOTAL',pord['total'])]):
                y=bottom+i*54; t(1030,y,label,22,gray,i==3); t(1410,y,f"${fmt(val)}",24,ink,i==3); line(1010,y+15,1570,y+15)
            ay=bottom+245
            r(80,ay,700,128,'#f4f7fa',rx=8); t(105,ay+36,'PURCHASING APPROVAL',17,gray,True); line(105,ay+76,735,ay+76,'#98a8b7',1); t(105,ay+108,'Released · Buyer authorization on file',17,ink)
            r(820,ay,760,128,'#f4f7fa',rx=8); t(845,ay+36,'DELIVERY / INSPECTION TERMS',17,gray,True); t(845,ay+77,'FOB destination · Count and condition verified at receiving',17,ink); t(845,ay+108,'Invoice quantities subject to accepted receipt records',17,ink)
            t(80,2140,'Unit prices in USD. Line discounts apply before tax. Freight allowance per FOB destination terms.',17,gray)
    elif kind in ('grn1','grn2'):
        gidx=int(kind[-1]); top=650; headers=['LINE','SKU','DESCRIPTION','EXPECTED','RECEIVED','ACCEPTED (PO UOM)','REJ.','CONVERSION']; xs=[80,165,310,760,920,1060,1270,1390]
        t(80,615,'Received / rejected use the listed GRN UOM; accepted quantity is converted to the PO UOM using the stated factor.',16,gray)
        r(70,top,1510,58,teal,rx=4)
        for x,h in zip(xs,headers): t(x,top+38,h,17,'#fff',True)
        rowh=76 if len(lines)<=8 else 64
        for i,ln in enumerate(lines):
            y=top+58+i*rowh; r(70,y,1510,rowh,'#f3f8f6' if i%2==0 else '#fff')
            conv=f"1 {ln['grn_uom']}={ln['conversion_factor']} {ln['uom']}" if ln['conversion_factor']>1 else f"1 {ln['uom']}"
            vals=[ln['line'],ln['sku'],ln['description'],ln['qty_ordered'],ln[f'grn{gidx}_received_raw'],ln[f'grn{gidx}_accepted'],ln[f'grn{gidx}_rejected_raw'],conv]
            for x,v in zip(xs,vals): t(x,y+rowh//2+7,v,18,ink,x==80)
            line(70,y+rowh,1580,y+rowh,'#dce7e2',1)
        t(80,2070,'Inspection note: accepted quantity excludes rejected units. Discrepancies are recorded by item and receipt.',19,gray)
        # stamped receiving mark, factual and not an answer cue
        r(1130,2150,350,95,'#edf6f2',teal,10); t(1170,2190,'WAREHOUSE VERIFIED',18,teal,True); t(1170,2225,scene['grns'][gidx-1]['status'],16,teal,True)
    elif kind=='credit_memo':
        cm=scene['credit_memos'][0]; ln=next((x for x in lines if x['line']==cm['line']),None)
        top=590; r(70,top,1510,58,red,rx=4)
        for x,h in zip([80,220,500,980,1210,1400],['LINE','SKU','DESCRIPTION','RETURN QTY','UNIT CREDIT','CREDIT AMOUNT']): t(x,top+38,h,15,'#fff',True)
        if ln:
            vals=[ln['line'],ln['sku'],ln['description'],ln['accepted_return_qty'],f"${fmt(ln['invoice_net_unit'])}",f"${fmt(cm['amount'])}"]
            r(70,top+58,1510,85,'#fff7f7'); line(70,top+143,1580,top+143,'#edd6d8',2)
            for x,v in zip([80,220,500,980,1210,1400],vals): t(x,top+113,v,21,ink,True)
        else: t(100,top+120,'No accepted return was credited on this invoice.',21,gray)
        t(1030,930,'Credit amount',21,gray); t(1370,930,f"${fmt(cm['amount'])}",25,red,True); t(80,1180,'This credit is allocated to the referenced invoice only. Other supplier credits remain unapplied.',19,gray)
        r(1080,1410,390,94,'#fff1f1',red,12); t(1120,1468,'CREDIT APPROVED',21,red,True)
    else:
        top=440; headers=['DATE','REFERENCE','DESCRIPTION','DEBIT','CREDIT','STATUS']; xs=[80,300,600,1090,1280,1460]
        r(70,top,1510,58,'#394d61',rx=4)
        for x,h in zip(xs,headers): t(x,top+38,h,18,'#fff',True)
        records=[]
        records.append((inv['date'],inv['id'],'Invoice posted',inv['total'],D(0),'POSTED'))
        for cm in scene['credit_memos']: records.append((cm['date'],cm['id'],cm['reason'],D(0),cm['amount'],'APPLIED' if cm['invoice_id']==inv['id'] else 'UNAPPLIED'))
        for pay in scene['payments']: records.append((pay['date'],pay['id'],'Cash remittance',D(0),pay['amount'],pay['status']))
        records.sort(key=lambda x:x[0]); bal=D(0)
        for i,(dt,ref,desc,debit,credit,status) in enumerate(records):
            y=top+58+i*75; r(70,y,1510,75,'#f4f6f9' if i%2==0 else '#fff'); bal+=debit-credit
            vals=[dt,ref,desc,f"${fmt(debit)}",f"${fmt(credit)}",status]
            for x,v in zip(xs,vals): t(x,y+45,v,18,ink,x==300)
            line(70,y+75,1580,y+75,'#dfe5eb',1)
        t(1000,top+58+(len(records)+1)*75,'OPEN BALANCE AS OF 16 OCT 2026',21,gray,True); t(1400,top+58+(len(records)+1)*75,f"${fmt(max(D(0),inv['total']-scene['linked_credit_total']-sum((p['amount'] for p in scene['payments'] if p['status']=='CLEARED' and p['date']<=scene['as_of_date']),D(0))))}",24,navy,True)
        t(80,2100,'Cleared payments reduce balance on posting date. Pending items and unapplied credits do not reduce invoice balance.',18,gray)
    if kind in ('purchase_order', 'invoice', 'invoice_sibling', 'amendment'):
        t(80,2180,'Rounding: discount each unit price, then round half-up to the nearest USD cent before multiplying by quantity.',17,gray)
        t(80,2207,'Use the same unit-rounding rule for PO and invoice rates. Sum positive line overcharges without netting undercharges.',17,gray)
    t(80,2290,f"CONTROL COPY  ·  {docid}  ·  Page 1 of 1",14,'#8795a3')
    parts.append('</svg>'); return ''.join(parts)

def validate(scene,kind,svg_text):
    # Keep the legacy generator entry point while housing all checking logic in validate/.
    from validate.finance_reconciliation.checks import validate_source_svg
    return validate_source_svg(scene, kind, svg_text)

def tasks_for(count,seed,difficulty='mixed',family=None):
    families=[family] if family else FAMILIES
    matrix=[(fam,diff) for fam in families for diff in DIFFICULTIES] if difficulty=='mixed' else [(fam,difficulty) for fam in families]
    out=[]
    for i in range(count):
        if i<len(matrix): fam,diff=matrix[i]; sampleseed=seed+i; layout=(seed+i)%3
        elif i in (len(matrix),len(matrix)+1):
            # Paired equivalent data under two layouts for an actual vision-layout comparison.
            fam,diff,sampleseed,layout=(family or 'quantity'),('medium' if difficulty=='mixed' else difficulty),seed+len(matrix),i-len(matrix)
        else:
            extra=i-len(matrix)-2; fam=(family or FAMILIES[extra%len(FAMILIES)]); diff=DIFFICULTIES[(extra//len(families))%len(DIFFICULTIES)] if difficulty=='mixed' else difficulty; sampleseed=seed+i; layout=(seed+i)%3
        for attempt in range(100):
            s=make_scene(sampleseed,diff,fam,layout,attempt)
            try:
                gt,ev,trace=solve(s); docs=make_docs(s)
                rendered={kind:render_svg(s,kind) for kind in docs}
                checks=[validate(s,k,rendered[k]) for k in docs]
                qtext,gt,atype,evidence,trace=question(s)
                # all answer-critical evidence document types must be present.
                if fam=='quantity' and diff!='easy' and ('grn1' not in docs or 'grn2' not in docs): raise ValueError('Missing receipt evidence')
                if fam=='price_rule' and 'amendment' not in docs: raise ValueError('Missing amendment')
                visible=' '.join(rendered.values())
                if not all(eid in visible for eid in evidence): raise ValueError('Answer evidence ID is not visible')
                break
            except (AssertionError,ValueError): layout=(layout+1)%3
        else: raise RuntimeError(f"Could not produce valid finance sample {i}")
        tid=f"fin-{sampleseed:05d}-{fam[:3]}-{diff[:1]}-L{layout}"
        out.append((tid,s,docs,rendered,qtext,gt,atype,evidence,trace,checks))
    return out
