"""Reuse R108 raw rebuild body; narrowly adapt campaigns, Seed and stage tables."""
from round109_common import *
import difflib

def main():
    d=OUT/'engineering/reader_adaptation01';d.mkdir(parents=True,exist_ok=False)
    original=ROOT/'scripts/round107_reader.py';data=original.read_bytes();(d/'round107_reader_before.py').write_bytes(data)
    text=data.decode('utf-8');old='settings=dict(read_return_code=0,Threads=1,Seed=0,Presolve=-1'
    assert text.count(old)==1
    new=text.replace(old,"settings=dict(read_return_code=0,Threads=1,Seed=p.get('gurobi_seed',0),Presolve=-1")
    original.write_bytes(new.encode('utf-8'))
    source=(ROOT/'scripts/round108_reader.py').read_text(encoding='utf-8')
    body=source[source.index('def rebuild('):source.index('\ndef compare(')]
    begin=body.index("    correction=read(");end=body.index('    arms=[];',begin)
    body=body[:begin]+"    campaigns=[('qualification/cli01',False)]+([] if qualification_only else [('campaign',True)])\n"+body[end:]
    body=body.replace("label=dict(campaign=campaign,id=launch['id'],arm=launch['arm'],number=launch['number'])",
        "label=dict(campaign=campaign,id=launch['id'],arm=launch['arm'],number=launch['number'],seed=launch['seed'],panel_kind=launch['panel_kind'])")
    body=body.replace("arm=dict(campaign=campaign,**ep['arm'])","arm=dict(campaign=campaign,seed=launch['seed'],panel_kind=launch['panel_kind'],**ep['arm'])")
    body=body.replace('ep=endpoint(root,launch,ident,d,j,formal);p=launch[\'panel\']',
        "ep=endpoint(root,launch,ident,d,j,formal);p=launch['panel'];check_native_parameters(launch,ep['result'],j);j['actual_frozen_seed']=launch['seed'];ep['physical']=full_fleet(root,p,ep['result'])\n            if not formal:ep['arm']['complete_seconds']=read(d/'whole_arm_receipt.json')['complete_seconds']")
    body=body.replace("dict(label,**w,routes=fleet['routes'],complete_fleet_vehicles=p['M'],","dict(label,**(w|fleet),")
    body=body.replace("    fee_rows=evidence.fees(out)","    fee_rows=fee_records(out)")
    start=body.index('    gate=None;selection=None');end=body.index('    fee_rows=',start)
    body=body[:start]+'''    selection=None
    if not qualification_only:
        roles=read(out/'input_manifest.json')['roles']
        eligibility_record=read(out/'review/sealed_input_eligibility.json')
        assert eligibility_record['input_manifest_SHA']==sha(out/'input_manifest.json')
        eligibility=eligibility_record['eligibility']
        data={(a['id'],a['seed'],a['arm']):a for a in arms}
        for role in roles:
            for candidate_arm,control in [('M-B','P-GRB'),('M-B','ENS-C'),('ENS-C','P-GRB')]:
                key=(role['id'],0,candidate_arm);control_key=(role['id'],0,control)
                if key in data and control_key in data:records['pairs'].append(dict(id=role['id'],seed=0,panel_kind='main',**decision.pair(data[key],data[control_key])))
        for role in ['G20-C2','G50-R1','G100-R2']:
            if (role,1,'M-B') in data and (role,1,'P-GRB') in data:records['seed_pairs'].append(dict(id=role,seed=1,panel_kind='seed',**decision.pair(data[role,1,'M-B'],data[role,1,'P-GRB'])))
        if len(arms)==42:
            selection=decision.selection(arms,roles,eligibility,['formal_failures'] if failures else [])
            write(dest/'selection_decision.json',selection)
            records['seed_flips']=[dict(id=id,Seed0=selection['main_primary_pairs'][id]['classification'],Seed1=selection['seed_primary_pairs'][id]['classification'],WIN_to_LOSS=id in selection['Seed0_WIN_to_Seed1_LOSS']) for id in ['G20-C2','G50-R1','G100-R2']]
            records['stratum_gains']=[dict(dimension=dim,stratum=s,WIN_roles=wins) for dim,group in selection['stratum_WIN_roles'].items() for s,wins in group.items()]
        for comparison in records['pairs']+records['seed_pairs']:
            if comparison['classification'] in ['LOSS','MIXED']:
                delta_U=comparison['candidate_U']-comparison['control_U'];delta_L=comparison['candidate_L']-comparison['control_L']
                records['loss_decomposition'].append(dict(id=comparison['id'],seed=comparison['seed'],panel_kind=comparison['panel_kind'],candidate=comparison['candidate'],control=comparison['control'],classification=comparison['classification'],severe=comparison['severe_regression'],delta_U=delta_U,delta_L=delta_L,delta_gap=delta_U-delta_L,identity_verified=True,causal_identification=False))
''' +body[end:]
    body=body.replace('<=48 and sum(r[\'outer_seconds\'] for r in fee_rows)<=80000','<=72 and sum(r[\'outer_seconds\'] for r in fee_rows)<=100000')
    body=body.replace("original_frozen_decision_reader_SHA=candidate['decision_reader_SHA'],current_decision_reader_SHA=sha(root/'scripts/round108_decisions.py'),\n        independent_reader_correction_review_SHA=sha(out/'review/reader_correction_review01.json'),",
        "current_decision_reader_SHA=sha(root/'scripts/round109_decisions.py'),inherited_core_reader_SHA=sha(root/'scripts/round108_reader.py'),")
    header='''"""Round109 stdlib raw reconstruction using the audited R108 core and rebuild loop.
Only panel bookkeeping, Seed readback, new decision tables and budgets differ.
No solver/environment load; absolute measured paths translate to explicit root.
"""
from round108_reader import *
import round109_decisions as decision
ROUND='results/unified_exact_round109'
_inherited_full_fleet=full_fleet

def full_fleet(root,p,w):
    value=_inherited_full_fleet(root,p,w);a=evidence.instance(root,p);cars=[]
    for route in value['routes']:
        pickup=sum(op['pickup'] if isinstance(op,dict) else op[1] for op in route['operations'])
        travel=sum(math.hypot(a['xy'][i][0]-a['xy'][j][0],a['xy'][i][1]-a['xy'][j][1])/1.5 for i,j in zip(route['nodes'],route['nodes'][1:]))
        handling=(p['pickup_seconds']+p['drop_seconds'])*pickup
        cars.append(dict(vehicle=route.get('vehicle',route.get('vehicle_id')),actual_station_count=len(route['operations']),pickup=pickup,
            travel_seconds=travel,handling_seconds=handling,closed_duration_seconds=travel+handling))
    value.update(lambda_P=p['lambda']*value['P'],sum_omega=sum(a['w'][1:]),total_initial_stock=sum(a['b'][1:]),
        total_final_stock=sum(value['Y'][1:]),total_target=sum(a['D'][1:]),total_return_load=sum(value['return_loads']),
        service_station_count=sum(c['actual_station_count'] for c in cars),cars=sorted(cars,key=lambda c:c['vehicle']))
    return value

def fee_records(out):
    data=[]
    for directory in sorted((out/'fees').iterdir()):
        launch=read(directory/'launch.json');receipt=read(directory/'receipt.json')
        assert not launch.get('engineering',False) and not receipt.get('engineering',False)
        assert launch['conservative_process_starts']==receipt['conservative_process_starts']
        data.append(dict(label=directory.name,outer_seconds=receipt['outer_seconds'],exit_code=receipt['exit_code'],
            stop_reason=receipt['stop_reason'],conservative_process_starts=receipt['conservative_process_starts'],
            wrapper_processes=launch['actual_wrapper_processes'],declared_children=launch['declared_native_children'],
            actual_native_children_with_launch=receipt.get('actual_native_children_with_launch',1),nested_seconds_added=False))
    return data

def require_identity(root,identity,candidate):
    assert identity['candidate_binary_sha256']==candidate['production_PE_SHA'] and identity['dll_sha256']==candidate['DLL_SHA']
    assert identity['source_hashes']==candidate['source_bindings']
    for name,digest in candidate['source_bindings'].items():assert sha(root/name)==digest,name
    for name,digest in identity['helpers'].items():assert sha(root/name)==digest,name
    assert identity['prereg_sha256']==sha(portable(root,identity['protocol_path']))
    assert identity['runner_sha256']==sha(root/'scripts/round109_campaign.py')

def check_native_parameters(launch,result,journal):
    settings=dict(read_return_code=0,Threads=1,Seed=launch['seed'],Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)
    assert launch['command'][launch['command'].index('--gurobi-seed')+1]==str(launch['seed'])
    for call in journal['calls'].values():assert call['settings']==settings
    if journal['started']:
        for name,value in dict(threads=1,seed=launch['seed'],presolve=-1,mip_gap=0.,mip_gap_abs=0.).items():
            for suffix in ['requested','effective']:assert result['gurobi_'+name+'_'+suffix]==value
            for suffix in ['set_return_code','get_return_code']:assert result['gurobi_'+name+'_'+suffix]==0
'''
    footer='''
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--qualification-only',action='store_true');parser.add_argument('--compare');a=parser.parse_args()
    print(json.dumps(rebuild(a.root,a.out,a.qualification_only),allow_nan=False))
    if a.compare:print(json.dumps(compare(a.compare,a.out),allow_nan=False))
'''
    path=ROOT/'scripts/round109_reader.py';assert not path.exists();path.write_text(header+'\n'+body+footer,encoding='utf-8',newline='\n')
    (d/'round108_rebuild_body.txt').write_text(source[source.index('def rebuild('):source.index('\ndef compare(')],encoding='utf-8',newline='\n')
    (d/'round107_seed_compatibility.diff').write_text(''.join(difflib.unified_diff(text.splitlines(True),new.splitlines(True))),encoding='utf-8',newline='\n')
    write(d/'receipt.json',dict(Optimize=0,production_or_performance_helper_changed=False,
        inherited_R108_core_SHA=sha(ROOT/'scripts/round108_reader.py'),old_R107_reader_SHA=sha(d/'round107_reader_before.py'),
        new_R107_reader_SHA=sha(original),new_R109_reader_SHA=sha(path),changes='Seed parameter metadata, fixed panel/decision/budget bookkeeping only'))
    print('R108 physical/model/Start/chronology/partition/endpoint core retained; Seed-aware bookkeeping adapted')

if __name__=='__main__':main()
