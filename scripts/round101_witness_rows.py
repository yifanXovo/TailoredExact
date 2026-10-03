"""Offline check of saved physical inventories against every unique saved rank.

No Optimize; run only when production performance is idle. Includes all journal
witnesses, finalized routes and preserved neutral-exchange closure inventories.
"""
import ast,json,re,sys
import analyze_round61 as physical
from round100_idle import ensure_idle
from round101_common import *

def verify(label,campaigns):
    ensure_idle();physical.ROOT=ROOT;panels={};witnesses={};ranks={};sources=[]
    def inventory(panel,witness,path):
        checked=physical.physical(panel,witness)
        assert checked['original_T_feasible']
        text=(ROOT/panel['input_path']).read_text()
        initial=ast.literal_eval(re.search(r'(?m)^initial\s*=\s*(\[[^\n]*\])',text)[1]);y=list(initial)
        for route in witness['routes']:
            for op in route['operations']:
                i,p,d=(op['station'],op['pickup'],op['drop']) if isinstance(op,dict) else op
                y[i]+=d-p
        h=panel['input_sha256'];panels[h]=initial
        witnesses.setdefault(h,set()).add(tuple(y));sources.append(dict(path=str(path),input_sha256=h,F=checked['F']))
    for name in campaigns:
        campaign=OUT/name;q=read(campaign/'identity.json')
        done=[json.loads(x) for x in (campaign/'summary.jsonl').read_text().splitlines()]
        assert len(done)==len(q['launches']) and all(x['audit_passed'] for x in done)
        for launch in q['launches']:
            panel=launch['panel'];folder=Path(launch['destination']);obs=read(folder/'observations.json')
            for r in obs:
                if r['payload']['kind']=='witness':inventory(panel,r['payload'],str(folder/'observations.json')+'#'+str(r['sequence']))
            result=read(folder/'result.json')
            if result.get('routes'):
                inventory(panel,dict(routes=result['routes'],F=result['upper_bound']),folder/'result.json')
            exchange=folder/'hga.csv.exchange'
            for path in [exchange/'initial.json',exchange/'final.json',*sorted(exchange.glob('closure_*.csv.final.json'))]:
                if path.exists():
                    value=read(path)
                    if 'routes' in value:inventory(panel,value,path)
            for path in sorted((folder/'external/native_logs').glob('*.round101.certificates.jsonl')):
                binding=read(Path(str(path).replace('.certificates.jsonl','.contract.json')))
                assert binding['input_sha256']==panel['input_sha256']
                for line in path.read_text().splitlines():
                    row=json.loads(line);p=row['proof'];signature=tuple(tuple(e) for e in p['events'])
                    ranks.setdefault(panel['input_sha256'],set()).add((signature,p['rank']))
    # Original-objective complete-LP qualification selections use the same input.
    development={p['id']:p for p in read(OUT/'development_inputs.json')['roles']}
    for record in read(OUT/'diagnostics/lp01/summary.json')['records']:
        panel=development[record['role']];h=panel['input_sha256']
        for row in read(OUT/'diagnostics/lp01'/record['role']/'raw.separation.json')['rows']:
            p=row['proof'];ranks.setdefault(h,set()).add((tuple(tuple(e) for e in p['events']),p['rank']))
    records=[];checks=0
    for h,rows in ranks.items():
        assert h in witnesses and h in panels
        initial=panels[h]
        for events,rhs in rows:
            for y in witnesses[h]:
                count=sum(y[i]<=initial[i]-q if sign<0 else y[i]>=initial[i]+q for i,sign,q in events)
                assert count<=rhs,(h,events,rhs,y,count)
                checks+=1
        records.append(dict(input_sha256=h,unique_inventories=len(witnesses[h]),unique_event_rank_rows=len(rows),
            row_inventory_checks=len(rows)*len(witnesses[h])))
    write(OUT/label/'summary.json',dict(passed=True,optimizer_calls=0,records=records,total_checks=checks,
        saved_witness_records=len(sources),witness_sources=sources,
        script_sha256=sha(__file__),scope='All measured journal witnesses/final routes and route-bearing saved exchange closure files, versus all saved unique event/rank proofs and original-objective LP selections. This is execution-team validation, not an independent search rerun.'))
    print(json.dumps(dict(passed=True,checks=checks,Optimize=0)))

if __name__=='__main__':verify(sys.argv[1],sys.argv[2:])
