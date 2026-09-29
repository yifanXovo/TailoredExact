"""Summarize every predeclared role, retaining missing/censored/negative arms.

Reads already audited evidence only. No Optimize and no merged certificates.
Every invocation needs a fresh output label; prior analyses stay immutable.
"""
import argparse
import csv
import json
import math
from pathlib import Path
from round96_prepare import ROOT, OUT, read, write, sha

def main():
    parser=argparse.ArgumentParser();parser.add_argument('label');args=parser.parse_args()
    assert args.label.replace('_','').replace('-','').isalnum()
    campaign=OUT/('primal_v2' if (OUT/'primal_v2/admission.json').exists() else 'primal');dest=OUT/('primal_report_'+args.label);dest.mkdir(exist_ok=False)
    identity=read(campaign/'identity.json')
    records=[json.loads(line) for line in (campaign/'summary.jsonl').read_text().splitlines()]
    assert len({r['number'] for r in records})==len(records)
    rows=[];certs={arm:0 for arm in ['P-GRB','ENS-C','ORDER-ON']};pairs=[];paid=0
    for launch in identity['launches']:
        matches=[r for r in records if r['number']==launch['number']];assert len(matches)<=1
        row=dict(number=launch['number'],role=launch['id'],arm=launch['arm'],cap=launch['cap_seconds'],
                 state='not_completed',U=None,L=None,absolute_gap=None,relative_gap=None,
                 process_seconds=None,certified_process_seconds=None,certificate=False)
        if matches:
            r=matches[0];assert r['audit_passed']
            audit_path=ROOT/r['audit_path'] if 'audit_path' in r else Path(r['destination'])/'audit.json';audit=read(audit_path);assert audit['passed']
            e=r['endpoint'];c=r['completion'];paid+=c['process_wall_seconds']
            assert e and math.isfinite(e['L'])
            assert e['U'] is None or math.isfinite(e['U']) and e['L']<=e['U']+1e-7
            g=None if e['U'] is None else max(0.,e['U']-e['L'])
            rel=None if g is None else g/max(abs(e['U']),1e-10)
            row.update(U=e['U'],L=e['L'],absolute_gap=g,relative_gap=rel,
                       process_seconds=c['process_wall_seconds'],certificate=e['certificate'],
                       state='certified' if e['certificate'] else 'right_censored' if c['stop_reason'] in
                       ['normal_return','whole_run_hard_stop'] else 'administrative_interruption',
                       certified_process_seconds=c['process_wall_seconds'] if e['certificate'] else None,
                       endpoint_source=e['source'],audit_sha256=sha(audit_path),stop_reason=c['stop_reason'])
            certs[launch['arm']]+=int(e['certificate'])
        rows.append(row)
    for role in dict.fromkeys(r['role'] for r in rows):
        same={r['arm']:r for r in rows if r['role']==role};candidate=same['ORDER-ON']
        for arm in ['P-GRB','ENS-C']:
            reference=same[arm];p=dict(role=role,reference=arm,status='not_completed',
                seconds_difference=None,certified_time_ratio=None,delta_U=None,delta_L=None,delta_gap=None)
            if all(r['state']!='not_completed' for r in [candidate,reference]):
                if candidate['certificate'] and reference['certificate']:
                    p.update(status='both_certified',seconds_difference=candidate['process_seconds']-reference['process_seconds'],
                        certified_time_ratio=candidate['process_seconds']/reference['process_seconds'])
                elif reference['certificate']:p['status']='ORDER_certificate_loss'
                elif candidate['certificate']:p['status']='ORDER_certificate_gain'
                else:p['status']='both_uncertified_final_order_unknown'
                for output,key in [('delta_U','U'),('delta_L','L'),('delta_gap','absolute_gap')]:
                    if all(r[key] is not None for r in [candidate,reference]):p[output]=candidate[key]-reference[key]
                p['UB_worse_LB_better']=p['delta_U'] is not None and p['delta_U']>1e-7 and p['delta_L']>1e-7
            pairs.append(p)
    def table(path,items):
        keys=list(dict.fromkeys(key for r in items for key in r))
        with path.open('x',newline='',encoding='utf-8') as stream:
            writer=csv.DictWriter(stream,fieldnames=keys);writer.writeheader();writer.writerows(items)
    table(dest/'arms.csv',rows);table(dest/'pairs.csv',pairs)
    write(dest/'summary.json',dict(completed=len(records),planned=12,all_completed=len(records)==12,
        certificates=certs,process_seconds=paid,rows=rows,pairs=pairs,
        identity_sha256=sha(campaign/'identity.json'),summary_sha256=sha(campaign/'summary.jsonl'),
        time_definition='Full process cost through validated certificate and exit, never cap as certification time; no certified-time ratio for censored pairs.',
        relative_gap_definition='max(0,U-L)/max(abs(U),1e-10)',optimizer_calls=0))
    lines=['# Frozen finite route-order OFF/ON/P comparison — '+args.label,'',
           f'Completed {len(records)}/12 arms; process cost {paid:.3f} s. Certified: '+str(certs)+'.','',
           'Every predeclared role is retained. A blank endpoint means uncompleted. Censored times are costs, not certificate times.',
           '', '|Role|Arm|State|U|L|Absolute gap|Process seconds|','|---|---|---|---:|---:|---:|---:|']
    def fmt(x):return '' if x is None else f'{x:.10g}'
    for r in rows:lines.append('|'+ '|'.join([r['role'],r['arm'],r['state'],fmt(r['U']),fmt(r['L']),fmt(r['absolute_gap']),fmt(r['process_seconds'])])+'|')
    lines+=['','Full numeric pairs and relative gaps: `pairs.csv` and `arms.csv`.','',
            'This evidence does not combine another arm\'s witness or lower bound into a certificate. Both-censored final-time ranking remains unknown.']
    (dest/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':main()
