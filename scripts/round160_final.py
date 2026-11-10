"""One saved-evidence scientific audit, then thin reporting/cost closure."""
from fractions import Fraction as F
from collections import Counter
import csv
from round160_common import *
from round160_prepare import data
from round160_qualify import original
from round157_fleet import verify
from round143_math import outward

def check_point(d,p,parent=None,nb=None):
    physical=verify(d,p);assert physical['original_T_feasible']
    assert physical['Y']==p['Y']
    owner=[-1]*d['n']
    for route in p['routes']:
        for i in route['nodes'][1:-1]:owner[i-1]=route['vehicle']
    assert owner==p['owner']
    J,G=original(d,p['Y']);assert abs(float(J)-p['J'])<1e-12
    if parent is not None:
        B=set(nb['B'])
        for i in range(1,d['n']+1):
            if i not in B:assert (p['Y'][i-1],p['owner'][i-1])==(parent['Y'][i-1],parent['owner'][i-1])
        bycar={r['vehicle']:r['nodes'][1:-1] for r in p['routes']};previous={}
        for seg in nb['segments']:
            route=bycar[seg['car']];ids=seg['ids'];start=route.index(ids[0])
            assert route[start:start+len(ids)]==ids
            assert start>previous.get(seg['car'],-1);previous[seg['car']]=start+len(ids)-1
        assert len(nb['ports'])<=min(8,len(B))
        assert len({(x['vehicle'],*x['arc']) for x in nb['ports']})==len(nb['ports'])
    return dict(J_exact=str(J),physical_U=outward(J,True),physical=physical)

def check_run(run,d):
    initial=read(run/'initial.json');summary=read(run/'summary.json')
    check_point(d,initial);events=0;models=0;worst=0.
    for block in sorted(run.glob('block_*'),key=lambda p:int(p.name.split('_')[1])):
        parent=read(block/'parent.json');nb=read(block/'neighborhood.json');check_point(d,parent)
        assert nb['parent_Y']==parent['Y'] and nb['parent_owner']==parent['owner']
        for branch in ('positive','zero'):
            folder=block/branch
            if not folder.exists():continue
            adm=read(folder/'admission.json');worst=max(worst,adm['parent_lift_residual'])
            assert adm['parent_lift_residual']<=1e-5
            result=read(folder/'result.json');assert not result['callback_failed'] and result['global_proof_changes']==0
            assert (folder/'model.mps').is_file();models+=1;last=parent['J']
            for event in sorted(folder.glob('event_*.json'),key=lambda p:int(p.stem.split('_')[1])):
                p=read(event);check_point(d,p,parent,nb);assert p['J']<last-1e-10;last=p['J'];events+=1
    assert events==summary['accepted']
    final=read(run/'final.json');checked=check_point(d,final);assert final['J']<=initial['J']+1e-12
    return dict(path=run.relative_to(ROOT).as_posix(),models=models,accepted=events,
        max_parent_lift_residual=worst,summary=summary,final=checked)

def matrix_residual():
    from round100_gurobi_runtime import gp,binding
    assert binding()['sha256']==DLL_SHA
    target=OUT/'runs/owner_control_nb/block_0/positive'
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        with gp.read(str(target/'model.mps'),env=env) as m:
            values={}
            for line in (target/'native.sol').read_text().splitlines():
                if line and not line.startswith('#'):
                    name,value=line.split();values[name]=float(value)
            rows=bounds=integer=0.
            for v in m.getVars():
                value=values.get(v.VarName,0.);bounds=max(bounds,v.LB-value,value-v.UB)
                if v.VType!='C':integer=max(integer,abs(value-round(value)))
            for c in m.getConstrs():
                e=m.getRow(c);lhs=sum(F(e.getCoeff(j))*F(values.get(e.getVar(j).VarName,0.)) for j in range(e.size()))
                gap=float(lhs-F(c.RHS));rows=max(rows,abs(gap) if c.Sense=='=' else gap if c.Sense=='<' else -gap)
            assert max(rows,bounds,integer)<=1e-5
    return dict(PASS=True,model_SHA=sha(target/'model.mps'),solution_SHA=sha(target/'native.sol'),
        row_residual=rows,bound_residual=bounds,integer_residual=integer,Optimize=0)

def audit():
    assert read(OUT/'panel_completion.json')['completed']==8
    matrix=read(OUT/'confirmation_matrix.json');manifest=read(OUT/'candidate_manifest.json')
    assert sha(manifest['production_PE'])==manifest['production_PE_SHA'] and sha(DLL)==DLL_SHA
    for name,digest in manifest['source_hashes'].items():assert sha(ROOT/name)==digest,name
    facts=[]
    for role,short in [('R-X35-S-T2','rx'),('N-B35-S','nb')]:
        d=read(OUT/'inputs'/role/'source.json')['data']
        for version in ('v1','v2'):facts.append(check_run(OUT/'runs'/f'core_{short}_{version}',d))
    d=read(OUT/'inputs/N-B35-S/source.json')['data']
    facts.append(check_run(OUT/'runs/owner_control_nb',d))
    for label in ('late','bridge'):facts.append(check_run(OUT/'qualification/late_parent'/label,d))
    arms=[]
    for group in matrix['groups']:
        launch=group['launch'];destination=Path(launch['destination']);arm=read(destination/'round160_endpoint.json')
        assert arm['numbers_qualified'] and arm['implementation_qualified'] and arm['evidence_complete']
        assert arm['PE_SHA']==manifest['production_PE_SHA'] and arm['DLL_SHA']==DLL_SHA
        assert arm['T_produce']<=launch['cap_seconds']
        assert abs(arm['T_total']-arm['T_produce']-arm['T_verify'])<1e-7
        assert arm['certificate_qualified'] or arm['T_cert'] is None
        assert arm['H_complete']
        for row in csv.DictReader((destination/'external/paper_leaf_ledger.csv').open(newline='',encoding='utf8')):
            assert not any(s.startswith('round160') for s in row.get('lower_bound_sources','').split(';'))
        if launch['R160_method']=='EplusR':
            d=data(launch['panel'],ROOT/launch['panel']['input_path'])
            facts.append(check_run(destination/'round160',d))
            raw=read(destination/'hga.csv.exchange/final.json');initial=read(destination/'round160/initial.json')
            assert abs(raw['F']-initial['J'])<1e-12
            if launch['id'] in ('R-X35-S-T2','N-B35-S'):
                offline=read(OUT/'inputs'/launch['id']/'parent.json')
                assert [r['nodes'] for r in offline['routes']]==[r['nodes'] for r in initial['routes']]
                assert [[o['station'],o['pickup'],o['drop']] for r in offline['routes'] for o in r['operations']]==[
                    [o['station'],o['pickup'],o['drop']] for r in initial['routes'] for o in r['operations']]
        helper=destination/'external/round153_floor/result.json'
        arm['common_RN_Optimize']=read(helper)['new_Native_calls'] if helper.exists() else 0
        arm['all_new_Optimize']=arm['native_Optimize']+arm['common_RN_Optimize']+arm.get('local_calls',0)
        arms.append(arm)
    for i in range(0,8,2):
        assert arms[i]['H_semantic_SHA']==arms[i+1]['H_semantic_SHA']
        assert arms[i]['H_fleet_SHA']==arms[i+1]['H_fleet_SHA']
    current=os.environ.get('ROUND140_METERED_PARENT_LABEL')
    assert all(p['label']==current for p in budget()['unclosed'])
    write(OUT/'final_review.json',dict(UTC=utc(),PASS=True,reviewer='same agent; separate Fraction/route/model readback script, not independent personnel',
        runs=facts,arms=arms,matrix=matrix_residual(),source_SHA=sha(__file__),
        original_T_and_sqrt_reader=True,all_outside_stock_owner_and_indivisible_runs_checked=True,
        own_H_R_scope_chain_and_single_deadline_checked=True,no_new_local_bound_in_global_proof=True,
        all_original_qualification_and_failures_retained=True,conditional_complete_panel=True))

def tables():
    review=read(OUT/'final_review.json');assert review['PASS'];folder=OUT/'reports';folder.mkdir(exist_ok=True)
    fields=['id','R160_method','U','raw_search_L','L','gap','relative_gap','T_produce','T_verify','T_total','T_cert',
        'certificate_qualified','certified','local_parent_J','local_final_J','local_seconds','local_calls','local_accepted',
        'native_Optimize','common_RN_Optimize','all_new_Optimize']
    # The inherited qualification flag also qualifies an honestly OPEN state.
    # A real time-to-certificate exists only for a completed global certificate.
    arms=[dict(a,certified=a['T_cert'] is not None) for a in review['arms']]
    with (folder/'complete.csv').open('w',newline='',encoding='utf8') as stream:
        w=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(arms)
    pairs=[]
    for a,b in zip(arms[::2],arms[1::2]):
        pairs.append(dict(role=a['id'],Eplus_U=a['U'],EplusR_U=b['U'],U_gain=a['U']-b['U'],
            Eplus_L=a['L'],EplusR_L=b['L'],gap_reduction=a['gap']-b['gap'],
            total_seconds_delta=b['T_total']-a['T_total'],
            cert_Eplus=a['certified'],cert_EplusR=b['certified'],
            Tcert_Eplus=a['T_cert'],Tcert_EplusR=b['T_cert'],
            local_parent_J=b['local_parent_J'],local_final_J=b['local_final_J'],
            local_seconds=b['local_seconds'],local_calls=b['local_calls'],local_accepted=b['local_accepted']))
    write(OUT/'complete_comparison.json',dict(UTC=utc(),pairs=pairs,complete_roles=4,arms=8,
        no_historical_or_P_GRB_pairing=True,scope='These four roles, one Seed and one frozen candidate; not an independent confirmation'))
    with (folder/'pairs.csv').open('w',newline='',encoding='utf8') as stream:
        w=csv.DictWriter(stream,fieldnames=list(pairs[0]));w.writeheader();w.writerows(pairs)
    print(json.dumps(pairs),flush=True)

def costs():
    configure();value=budget();assert not value['unclosed'];assert value['G1_seconds']<=TOTAL
    receipts=[]
    for path in sorted((OUT/'fees').glob('*/receipt.json')):
        launch=read(path.parent/'launch.json');r=read(path);receipts.append(dict(label=path.parent.name,kind=launch['kind'],**r))
    write(OUT/'cost_report.json',dict(UTC=utc(),TOTAL=TOTAL,**value,outer_receipts=receipts,
        failed_outer_receipts=[r for r in receipts if r['exit_code']!=0],
        old_R159_or_prior_scientific_cost_added=0,production_total_and_postverification_separate=True,
        Native_Runtime_Work_and_callback_validation_are_nested_not_added=True))

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
