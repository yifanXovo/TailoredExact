"""Conservative whole-round receipt and actual-call reconciliation, no solver.

Run after all numerical readers have closed. Legacy return-only logs remain
explicitly weaker attempted-call evidence, never invented begin records.
"""
import sys,json,csv
from round103_common import *
from round103_budget import account
from round100_idle import ensure_idle

def lines(path):
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []

def counts(label):
    name=label.removeprefix('fees/')
    d=OUT/'diagnostics'/name.removeprefix('point_')
    if name.startswith('point_'):d=OUT/'diagnostics'/name[6:]
    launch=read(OUT/'fees'/name/'launch.json')
    argv=list(map(str,launch['command']))
    for index,arg in enumerate(argv):
        if Path(arg).name=='round103_verify_evidence.py':
            d=OUT/'diagnostics'/argv[index+1]
            break
    out=dict(native_Optimize_calls=0,auxiliary_Optimize_calls=0,DP_calls=0,
        LP_begin_records=0,LP_return_records=0,DP_begin_records=0,DP_return_records=0,
        model_read_attempts=None,attempt_scope='No optimizer invoked by this batch')
    if name=='independent_review01':
        q=read(OUT/'review/independent_review01.conclusion.json')['independent_counts']
        out.update(DP_calls=q['DP_attempts'],DP_begin_records=q['DP_attempts'],DP_return_records=q['DP_returns'],
            model_read_attempts=q['model_read_attempts'],attempt_scope='Independent level DP attempts, two support recomputations; zero Optimize')
        return out
    if not d.exists():
        # Reporting, final read-only review and whole-round source evidence
        # replay declare zero Optimize in their launch/summary records.
        command=' '.join(launch['command'])
        assert any(x in command for x in ['round103_results.py','round103_verify_evidence.py','round103_final_review.py']),command
        out['attempt_scope']='Read-only batch, zero Optimize by implementation; complete receipt charged'
        return out
    if name=='root_faults01':
        rs=read(d/'summary.json')['records']
        out.update(native_Optimize_calls=sum(x['required_LP_Optimize'] for x in rs),
            auxiliary_Optimize_calls=sum(x['auxiliary_Optimize_calls'] for x in rs),
            DP_calls=sum(x['DP_calls'] for x in rs),attempt_scope='Two actual failed production children plus evidence reader, no MIP Optimize')
        return out
    for p in list(d.rglob('master_calls.jsonl'))+list(d.glob('outer_calls.jsonl'))+list(d.glob('enum_master_calls.jsonl')):
        events=lines(p);begin=sum(x.get('event')=='begin' for x in events)
        returned=sum(x.get('event')!='begin' for x in events)
        out['LP_begin_records']+=begin;out['LP_return_records']+=returned
        out['auxiliary_Optimize_calls']+=max(begin,returned)
    if (d/'Optimize_begin.json').exists():
        out['auxiliary_Optimize_calls']+=1;out['LP_begin_records']+=1
        out['LP_return_records']+=int((d/'Optimize_return.json').exists())
    for p in d.rglob('oracle_calls.jsonl'):
        out['DP_return_records']+=len(lines(p))
    for p in d.rglob('oracle_attempts.jsonl'):
        out['DP_begin_records']+=sum(x.get('event')=='begin' for x in lines(p))
    out['DP_calls']=max(out['DP_begin_records'],out['DP_return_records'])
    summary=read(d/'summary.json') if (d/'summary.json').exists() else {}
    if (d/'model_reads.jsonl').exists():
        out['model_read_attempts']=sum(x.get('event')=='begin' for x in lines(d/'model_reads.jsonl'))
    if 'outer_Optimize_calls' in summary:
        assert out['auxiliary_Optimize_calls']==summary['outer_Optimize_calls']+summary['master_Optimize_calls'],(name,out,summary)
    elif 'total_Optimize_calls' in summary:
        assert out['auxiliary_Optimize_calls']==summary['total_Optimize_calls'],(name,out)
    elif 'Optimize_calls' in summary:
        assert out['auxiliary_Optimize_calls']==summary['Optimize_calls'],(name,out)
    for key in ['total_DP_calls','DP_calls']:
        if key in summary:assert out['DP_calls']==summary[key],(name,out,summary[key])
    if 'model_read_attempts' in summary:out['model_read_attempts']=summary['model_read_attempts']
    if out['auxiliary_Optimize_calls'] or out['DP_calls']:
        complete=(out['LP_begin_records']==out['LP_return_records']==out['auxiliary_Optimize_calls'] and
                  out['DP_begin_records']==out['DP_return_records']==out['DP_calls'])
        out['attempt_scope']='Matching begin/return records' if complete else 'Historical return-only records included conservatively; absent begins cannot reconstruct interrupted attempts'
    if (d/'matrix.txt').exists() and out['model_read_attempts'] is None:out['model_read_attempts']=1
    return out

def main(label):
    ensure_idle();target=OUT/label;target.mkdir(exist_ok=False)
    a=account();assert a['within_limits'] and not a['reserved'] and not a['incomplete'],a
    legacy={}
    for camp in OUT.iterdir():
        identity=camp/'identity.json'
        if not identity.exists():continue
        for arm in read(identity).get('launches',[]):
            if arm['arm']!='J-SUBMIT':continue
            records=[]
            for path in sorted((Path(arm['destination'])/'external/native_logs').glob('*.round102.summary.json')):
                summary=read(path)
                records.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),
                    DP_calls=summary['dp_calls'],directions=summary['directions'],cache_hits=summary['cache_hits'],
                    scope='Inherited R102 successful callback summary; no invented begin records or independent repricing'))
            assert records
            legacy[f'{camp.name}/{arm["number"]}/{arm["id"]}/{arm["arm"]}']=records
    fs=[]
    for original in a['fees']:
        f=dict(original)
        if f['label'].startswith('fees/'):f.update(counts(f['label']))
        else:
            f.setdefault('native_Optimize_calls',f.get('Optimize_calls',0))
            f.setdefault('auxiliary_Optimize_calls',0);f.setdefault('DP_calls',0)
            if f['label'] in legacy:
                f['resource_hull_DP_calls']=f['DP_calls']
                f['inherited_R102_DP_calls']=sum(r['DP_calls'] for r in legacy[f['label']])
                f['DP_calls']+=f['inherited_R102_DP_calls']
                f['inherited_R102_DP_evidence']=legacy[f['label']]
        fs.append(f)
    a['fees']=fs
    a.update(actual_native_Optimize_calls=sum(f['native_Optimize_calls'] for f in fs),
        actual_auxiliary_Optimize_calls=sum(f['auxiliary_Optimize_calls'] for f in fs),
        actual_DP_calls=sum(f['DP_calls'] for f in fs),
        actual_inherited_R102_DP_calls=sum(f.get('inherited_R102_DP_calls',0) for f in fs),
        experimental_failures=[f['label'] for f in fs if f.get('failed')],
        limitations='LP counts include successful historical return-only records; inherited R102-J DP calls come from successful callback summaries, without invented begin records. reports_final01 whole_run_costs DP field is new resource-hull calls only; this complete ledger also includes inherited J calls. Final report readers and packaging never Optimize; level DP review calls are included as DP calls, not additional support solves',
        source_sha256=sha(__file__))
    write(target/'fee_reconciliation.json',a)
    fields=list(dict.fromkeys(k for f in fs for k in f))
    with (target/'fees.csv').open('x',newline='',encoding='utf-8') as stream:
        w=csv.DictWriter(stream,fieldnames=fields);w.writeheader();w.writerows(fs)
    engineering=[]
    for p in sorted((OUT/'engineering').glob('*/receipt.json')):
        engineering.append(dict(label=p.parent.name,receipt=p.relative_to(ROOT).as_posix(),**read(p)))
    write(target/'engineering.json',dict(separate=True,records=engineering,
        scope='Builds, enumeration/unit fixtures, byte packaging and pure receipt reconciliation; numerical evidence readers charged above'))
    print(json.dumps({k:a[k] for k in ['completed_starts','completed_seconds','actual_native_Optimize_calls','actual_auxiliary_Optimize_calls','actual_DP_calls','within_limits']}))

if __name__=='__main__':main(sys.argv[1])
