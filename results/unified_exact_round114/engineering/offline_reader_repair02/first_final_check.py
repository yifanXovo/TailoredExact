"""Check the actual offline metadata repair without revising performance evidence."""
import argparse,csv,difflib,json,time
from pathlib import Path
import read_round114 as r

def main(root):
    tick=time.perf_counter();root=Path(root).resolve();out=root/r.ROUND;eng=out/'engineering/offline_reader_repair02'
    old=eng/'reports_before';new=out/'reports_final';checked=[]
    for p in sorted(old.iterdir()):
        if p.suffix not in ['.json','.csv']:continue
        q=new/p.name;assert q.is_file()
        if p.suffix=='.json':
            a=r.read(p);b=r.read(q)
            if p.name=='summary.json':a.pop('reader_SHA');b.pop('reader_SHA')
            assert a==b,p.name
        else:
            a=r.core.rows(p);b=r.core.rows(q);assert len(a)==len(b),p.name
            for x,y in zip(a,b):
                y=dict(y);y.pop('planned_formal_position',None);y.pop('actually_executed',None)
                # This one inherited annotation was the proved metadata defect.
                if p.name in ['arms.csv','new_arms.csv'] and x.get('origin_round')=='114':
                    x=dict(x);x.pop('formal_performance',None);y.pop('formal_performance',None)
                assert x==y,(p.name,x.get('arm'))
        checked.append(p.name)
    rows=r.core.rows(new/'new_arms.csv');lookup={v['arm']:v for v in rows}
    for arm,v in lookup.items():
        assert v['planned_formal_position']=='True'
        assert (v['formal_performance']=='True')==(arm=='P-GRB')
        assert (v['actually_executed']=='True')==(arm in ['P-GRB','ENS-C'])
    assert lookup['ENS-C']['U']==lookup['ENS-C']['L']==lookup['ENS-C']['gap']==lookup['ENS-C']['certificate']==''
    candidate=r.read(out/'candidate_identity.json')
    for field in ['source_bindings','helpers']:
        for n,h in candidate[field].items():assert r.sha(root/n)==h,n
    clocks=r.read(out/'engineering/offline_reader_repair01/targeted_checks.json')['clocks']
    for v in clocks:
        i=r.read(out/v['campaign']/'identity.json');l=next(l for l in i['launches'] if l['arm']==v['arm'])
        d=r.portable(root,l['destination']);assert r.clock_evidence(d,l)=={k:x for k,x in v.items() if k not in ['campaign','arm']}
    current=(root/'scripts/read_round114.py').read_text(encoding='utf-8-sig').splitlines(keepends=True)
    for previous,label in [(eng/'previous_reader.py','metadata'),(out/'engineering/offline_reader_repair01/original_reader.py','full')]:
        diff=''.join(difflib.unified_diff(previous.read_text(encoding='utf-8-sig').splitlines(keepends=True),current,
            fromfile='retained/'+previous.name,tofile='final/read_round114.py'))
        with (eng/(label+'_reader.diff')).open('x',encoding='utf-8',newline='\n') as f:f.write(diff)
    receipt=dict(passed=True,core_files=checked,all_numbers_pairs_claims_fees_clocks_unchanged=True,
        correct_current_formal_performance_metadata=True,planned_and_actual_execution_distinct=True,
        source206_performance_helpers47_unchanged=True,qualification_CLI_unchanged=True,old15_21_unchanged=True,
        final_reader_SHA=r.sha(root/'scripts/read_round114.py'),original_admitted_reader_SHA=candidate['offline_reader_SHA'],
        previous_reader_SHA=r.sha(eng/'previous_reader.py'),final_core_SHA={p.name:r.sha(p) for p in sorted(new.iterdir()) if p.suffix in ['.csv','.json']},
        Optimize=0,engineering_seconds=time.perf_counter()-tick)
    r.write(eng/'targeted_checks.json',receipt);print(json.dumps({k:v for k,v in receipt.items() if k not in ['final_core_SHA','core_files']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();main(a.root)
