"""Readable final tables derived only from closed audited R86 evidence."""
import json
import time
from pathlib import Path
from round86_analyze import ROOT, OUT, read, write, sha, compare
from round86_analyze import endpoint

def main():
    started=time.perf_counter(); stage=OUT.parent
    assert not (OUT/'active_run.lock').exists()
    assert not (stage/'findings.json').exists() and not (stage/'result_tables.md').exists()
    for name in ['audit.json','mechanism_audit.json','confirmation_audit.json']:
        assert read(OUT/name)['all_checks_passed']
    summary=read(OUT/'summary.json');protocol=read(stage/'protocol.json')
    assert summary['completed']==12
    rows=[];pairs=[];calls=read(OUT/'actual_calls.json')
    for p in protocol['panel']:
        role=p['id'];arms={}
        for arm in protocol['arms']:
            done=next(r for r in summary['records'] if r['id']==role and r['arm']==arm)
            ep=endpoint(done); arms[arm]=ep
            mine=[r for r in calls if r['id']==role and r['arm']==arm]
            rows.append(dict(id=role,arm=arm,cap=p['cap'],V=p['V'],M=p['M'],Q=p['Q'],T=p['T_seconds'],
                stop_reason=done['stop_reason'],returncode=done['returncode'],**ep,
                native_starts=len(mine),LP_starts=sum(not r['native_preconditions'] for r in mine),
                MIP_starts=sum(bool(r['native_preconditions']) for r in mine),
                native_returns=done['audit']['native_calls_returned']))
        for reference,candidate in [('P-GRB','ENS-C'),('P-GRB','K1-R'),('K1-R','ENS-C')]:
            a,b=arms[reference],arms[candidate];difference=compare(a,b,int(p['V']))
            metric='paid_certification_wall' if a['certificate'] and b['certificate'] else 'absolute_gap' if not a['certificate'] and not b['certificate'] else None
            if not (a['available'] and b['available']):metric=None
            av=a['paid_completion_seconds'] if metric=='paid_certification_wall' else a['gap'] if metric else None
            bv=b['paid_completion_seconds'] if metric=='paid_certification_wall' else b['gap'] if metric else None
            percent=100*(bv-av)/abs(av) if av is not None and av!=0 else None
            pairs.append(dict(id=role,reference=reference,candidate=candidate,cap=p['cap'],metric=metric,
                candidate_minus_reference_percent=percent,**difference))
    protection=[r for r in read(OUT/'protection.json') if r['seconds']==next(p['cap'] for p in protocol['panel'] if p['id']==r['id'])]
    result=dict(endpoints=rows,final_pairs=pairs,final_protection=protection,
        source_hashes={name:sha(OUT/name) for name in ['summary.json','audit.json','actual_calls.json','protection.json','confirmation_audit.json']},
        all_outcomes_retained=True,optimizer_calls=0,script_sha256=sha(__file__),
        scope='Descriptive frozen-rule results. Percent changes are undefined across certificate gain/loss. No historical controls or preferred-repeat selection.')
    fmt=lambda v:'unavailable' if v is None else f'{v:.12g}'
    lines=['# R86 audited result tables','',
        '|Role|Arm|Cap|Paid seconds|Physical U|Global L|Signed gap|Relative gap|Certificate / stop|',
        '|---|---|---:|---:|---:|---:|---:|---:|---|']
    for r in rows:
        certificate='yes' if r['certificate'] else 'open'
        lines.append(f"|{r['id']}|{r['arm']}|{r['cap']}|{r['paid_completion_seconds']:.3f}|{fmt(r['U'])}|{fmt(r['L'])}|{fmt(r['gap'])}|{fmt(r['relative_gap'])}|{certificate}; {r['stop_reason']}|")
    lines+=['','|Role|Reference|Candidate|Frozen classification|Material gain|Material loss|Severe loss|Metric change %|',
        '|---|---|---|---|---|---|---|---:|']
    for r in pairs:
        show=lambda k:'n/a' if r.get(k) is None else str(r[k]).lower()
        lines.append(f"|{r['id']}|{r['reference']}|{r['candidate']}|{r['classification']}|{show('material_improvement')}|{show('material_regression')}|{show('severe_regression')}|{fmt(r['candidate_minus_reference_percent'])}|")
    lines+=['','Positive metric change is slower certification or larger gap; no percentage is assigned across certificate gain/loss. The exact U/L direction and all checkpoints remain in the machine-readable evidence.','']
    (stage/'result_tables.md').write_text('\n'.join(lines),encoding='utf-8')
    result['wall_seconds']=time.perf_counter()-started
    write(stage/'findings.json',result)
    print(json.dumps(dict(endpoints=len(rows),final_pairs=len(pairs),protection_roles=len(protection),optimizer_calls=0,wall_seconds=result['wall_seconds'])))

if __name__=='__main__':main()
