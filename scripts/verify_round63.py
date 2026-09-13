"""Independent original-route and resource evidence checks; never calls a solver."""
import argparse
import json
import math
import shutil
from pathlib import Path
from analyze_round63 import ROOT,OUT,RAW,read,csvrows,resource_row,table,audit_strength
from analyze_round61 import physical
from verify_round62 import proof_check
import round63_research as run
run.bind_runner()

def audit_native():
    witnesses=[];resources=[];thresholds=[];panels=run.panel()
    for e in run.runner.entries():
        folder=ROOT/e['destination']
        if not e['charged'] or not (folder/'completion.json').exists() or e['id'] not in panels:continue
        p=panels[e['id']]
        assert run.sha(ROOT/p['instance_path'])==p['input_sha256']
        paths=list(folder.glob('**/*witness.json'))
        if (folder/'result.json').exists() and 'routes' in read(folder/'result.json'):paths.append(folder/'result.json')
        for path in paths:
            w=read(path);checked=physical(p,w);assert checked['original_T_feasible']
            record=dict(number=e['charged_number'],id=e['id'],arm=e['arm'],path=str(path.relative_to(ROOT)),sha256=run.sha(path),**checked)
            witnesses.append(record)
            dest=OUT/'witnesses'/str(e['charged_number'])/path.relative_to(folder);dest.parent.mkdir(parents=True,exist_ok=True)
            if path.name=='result.json':run.write(dest,{k:w[k] for k in ['objective','routes','verification'] if k in w})
            else:shutil.copyfile(path,dest)
        for path in folder.glob('**/*.round62.json'):
            checked=proof_check(p,read(path));thresholds.append(dict(number=e['charged_number'],id=e['id'],path=str(path.relative_to(ROOT)),**checked))
        for path in folder.glob('**/*.round63.cuts.jsonl'):
            base=str(path)[:-len('.cuts.jsonl')]
            stats=read(Path(base+'.json'))
            # All native calls regenerate the same global physical data. The
            # canonical file sidecar can live at a sibling interval directory.
            definitions=[read(q) for q in folder.glob('**/*.lp.round63.json')]
            data=next(q for q in definitions if q['identity']==stats['resource_identity'])
            points={(int(r['query']),int(r['vehicle']),r['variable']):float(r['raw_value']) for r in csvrows(Path(base+'.points.csv'))}
            records=[json.loads(s) for s in path.read_text().splitlines()];seen=set();maximum=0
            for cut in records:
                assert cut['identity']==data['identity'] and cut['scope']=='original_physical_global'
                signature=(cut['vehicle'],tuple(cut['support']));assert signature not in seen;seen.add(signature)
                coefficients=resource_row(data,cut['vehicle'],cut['support']);assert coefficients==cut['coefficients']
                v=math.fsum(c*points[(cut['query'],cut['vehicle'],n)] for n,c in coefficients.items())
                assert v>1e-7 and abs(v-cut['violation'])<1e-9
                assert cut['api_return']==(0 if stats['mode']=='cuts' else -1)
                maximum=max(maximum,v)
            assert stats['queries']<=64 and stats['root_queries']<=16 and stats['selected']<=256
            assert stats['maxflow_calls']<=stats['queries']*data['M']
            assert len(records)==stats['selected']
            if stats['mode']=='cuts':assert stats['submitted']==stats['api_success']==len(records)
            else:assert stats['submitted']==stats['api_success']==0
            resources.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],path=str(path.relative_to(ROOT)),rows=len(records),maximum_violation=maximum,passed=True,disabled_after_failure=stats['disabled_after_failure']))
    table('witness_verification.csv',witnesses);run.write(OUT/'native_resource_verification.json',resources);run.write(OUT/'threshold_verification.json',thresholds)
    print('independent routes',len(witnesses),'resource call traces',len(resources),'threshold proofs',len(thresholds))

def submitted():
    entries={e['charged_number']:e for e in run.runner.entries() if e['charged']};panels=run.panel();count=0
    for path in (OUT/'witnesses').glob('**/*.json'):
        e=entries[int(path.relative_to(OUT/'witnesses').parts[0])]
        result=physical(panels[e['id']],read(path));assert result['original_T_feasible'];count+=1
    assert count>0
    print('submitted independent original-route checks passed:',count)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--submitted',action='store_true');a=p.parse_args()
    if a.submitted:submitted()
    else:audit_strength();audit_native()
