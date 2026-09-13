"""Independent original-route and resource evidence checks; never calls a solver."""
import argparse
import json
import math
import shutil
from pathlib import Path
from analyze_round63 import ROOT,OUT,RAW,read,csvrows,resource_row,table,audit_strength
from analyze_round61 import physical
from verify_round62 import proof_check,check_lp_point
import round63_research as run
run.bind_runner()

def audit_native():
    witnesses=[];resources=[];thresholds=[];panels=run.panel()
    for e in run.runner.entries():
        folder=ROOT/e['destination']
        if not e['charged'] or not (folder/'completion.json').exists():continue
        if e['id'] in panels:
            p=panels[e['id']]
            assert run.sha(ROOT/p['instance_path'])==p['input_sha256']
        elif e['kind']=='native-micro' and '--input' in e['command']:
            cmd=e['command'];value=lambda arg:cmd[cmd.index(arg)+1]
            p=dict(instance_path=value('--input'),T_seconds=value('--T'),pickup_seconds=value('--pickup-time'),drop_seconds=value('--drop-time'),**{'lambda':value('--lambda')})
        else:continue
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
        for path in folder.glob('**/*.round63_prepare.cuts.jsonl'):
            prefix=str(path)[:-len('.cuts.jsonl')];data=read(Path(prefix+'.data.json'));stats=read(Path(prefix+'.json'))
            points={(int(r['query']),int(r['vehicle']),r['variable']):float(r['raw_value']) for r in csvrows(Path(prefix+'.points.csv'))}
            records=[json.loads(s) for s in path.read_text().splitlines()];seen=set()
            for cut in records:
                assert cut['scope']=='original_physical_global' and cut['identity']==data['identity'] and cut['api_return']==-1
                assert cut['vehicle'] not in seen;seen.add(cut['vehicle'])
                c=resource_row(data,cut['vehicle'],cut['support']);assert c==cut['coefficients']
                v=math.fsum(a*points[(1,cut['vehicle'],n)] for n,a in c.items());assert v>1e-7 and abs(v-cut['violation'])<1e-9
            assert stats['queries']==1 and stats['maxflow_calls']==data['M'] and len(records)==stats['selected']<=data['M']
            for mip in folder.glob('**/*.round63.json'):
                native=read(mip)
                if native.get('mode')=='root':assert native['prepared_static_rows']==native['static_rows_added']==len(records)
                elif native.get('mode')=='root-dry':assert native['prepared_static_rows']==len(records) and native['static_rows_added']==0
            resources.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],path=str(path.relative_to(ROOT)),rows=len(records),passed=True,kind='first_LP_static_pool'))
    table('witness_verification.csv',witnesses);run.write(OUT/'native_resource_verification.json',resources);run.write(OUT/'threshold_verification.json',thresholds)
    print('independent routes',len(witnesses),'resource call traces',len(resources),'threshold proofs',len(thresholds))

def submitted():
    entries={e['charged_number']:e for e in run.runner.entries() if e['charged']};panels=run.panel();count=0
    for path in (OUT/'witnesses').glob('**/*.json'):
        e=entries[int(path.relative_to(OUT/'witnesses').parts[0])]
        if e['id'] in panels:p=panels[e['id']]
        else:
            cmd=e['command'];value=lambda arg:cmd[cmd.index(arg)+1]
            p=dict(instance_path=value('--input'),T_seconds=value('--T'),pickup_seconds=value('--pickup-time'),drop_seconds=value('--drop-time'),**{'lambda':value('--lambda')})
        result=physical(p,read(path));assert result['original_T_feasible'];count+=1
    assert count>0
    print('submitted independent original-route checks passed:',count)

def audit_coupling():
    records=[]
    for path in sorted(RAW.glob('**/coupling_result.json')):
        folder=path.parent;r=read(path);data=read(folder/'resource.json');points={}
        for name in ['explicit','coupled','pinned_coupled']:
            p=folder/(name+'_point.csv')
            if not p.exists():continue
            point={v['variable']:float(v['value']) for v in csvrows(p)};points[name]=point
            model=folder/('explicit.lp' if name=='explicit' else 'coupled.lp')
            residual=check_lp_point(model,point)
            records.append(dict(id=folder.name,kind=name,**residual))
        maximum=max(0,max(data['handling']*points['explicit'][f'load_{k}_{i}']-
            math.fsum(points['explicit'][f'r63f_{k}_{i}_{j}'] for j in range(data['V']+1) if j!=i)
            for k in range(data['M']) for i in range(1,data['V']+1)))
        assert abs(maximum-r['explicit_point_maximum_carried_violation'])<1e-9
        assert len(csvrows(folder/'native_calls.csv'))==r['optimizer_calls']==4
        if 'pinned_coupled' in points:
            discrepancy=max(abs(v-points['pinned_coupled'][n]) for n,v in points['explicit'].items() if not n.startswith('r63f_'))
            assert discrepancy<1e-5
        else:discrepancy=None
        records.append(dict(id=folder.name,kind='projection_diagnostic',maximum_extended_point_violation=maximum,
            pinned_original_variables_match=discrepancy,pinned_explicit_feasible=r['pinned_explicit_feasible'],
            pinned_coupled_feasible=r['pinned_coupled_feasible'],
            strict_projection_witness=bool(r['pinned_explicit_feasible'] and r['pinned_coupled_infeasible'])))
    run.write(OUT/'coupling_verification.json',records)
    print('coupling verification records',len(records))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--submitted',action='store_true');a=p.parse_args()
    if a.submitted:submitted()
    else:audit_strength();audit_coupling();audit_native()
