"""Independent bridge admission; existing JSON/CSV/hash checks only."""
from pathlib import Path
from datetime import datetime,timezone
import csv,hashlib,json
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/unified_exact_round146'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
previous=read(OUT/'review/rb35_admission.json');manifest=read(OUT/'candidate_manifest.json')
assert previous['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
assert sha(manifest['production_PE'])==manifest['production_PE_SHA']==previous['production_PE_SHA']
for p,h in manifest['source_hashes'].items():assert sha(ROOT/p)==h,p
for p,h in previous['evidence_SHA'].items():
    assert any(q.exists() and sha(q)==h for q in [OUT/p,*list((OUT/'stages').glob('*/'+Path(p).name))]),p
old_matrix=read(OUT/'rb35_matrix.json');assert sha(OUT/'rb35_matrix.json')==previous['matrix_SHA']
full=read(OUT/'reports/full.json');assert len(full['new_arms'])==6 and not full['failed_qualifications']
assert full['all_entered_observed_Native_Optimize']==full['all_entered_observed_Native_returned']==31
assert full['standalone_LP_Optimize_separate']==5
with (OUT/'reports/verified_U_trajectories.csv').open(newline='') as f:trajectories=list(csv.DictReader(f))
ends=[]
for group in old_matrix['groups']:
    l=group['launch'];d=Path(l['destination']);a=read(d/'audit.json');e=a['endpoint'];c=read(d/'verification_closeout.json');t=read(d/'arm_total_receipt.json');prod=read(d/'producer_receipt.json')
    assert a['passed'] and a['implementation_qualified'] and a['evidence_complete'] and not a['source_rejections']
    assert c['audit_SHA']==sha(d/'audit.json') and t['verification_closeout_SHA']==sha(d/'verification_closeout.json')
    assert c['native_proof_qualified'] and c['necessary_verification_complete']
    assert not e['certificate'] and e['T_cert'] is None and e['performance_eligible'] and e['H_complete']
    assert e['declared_calls']==e['returned_calls']==4 and e['PE_SHA']==manifest['production_PE_SHA']
    assert e['stop_reason']=='normal_return' and e['raw_tree_termination_reason']=='overall_global_deadline'
    assert prod['cap_seconds']==2400 and 2370<prod['T_produce']<2400 and prod['native_stopped_no_reentry'] and prod['required_outputs_closed']
    r=next(x for x in full['new_arms'] if x['role']=='R-B35-S-T2' and x['method']==l['R146_method'])
    for k in ['U','L','T_produce','T_cert','H_semantic_SHA','H_fleet_SHA']:assert r[k]==e[k]
    for k in ['T_verify','T_total']:assert r[k]==t[k]
    events={x['sequence']:x for x in read(d/'observations.json')};selected=[x for x in trajectories if x['role']==l['id'] and x['method']==l['R146_method']]
    assert selected and abs(float(selected[-1]['U'])-e['U'])<1e-12
    for row in selected:
        event=events[int(row['sequence'])]
        assert row['committed_event_SHA']==event['sha256'] and row['raw_observation_SHA']==sha(d/'observations.json')
        assert float(row['U'])==event['payload']['objective'] and float(row['producer_seconds'])==event['effective_available_seconds']
    ends.append({**{k:r[k] for k in ['method','U','L','relative_gap','T_produce','T_cert','T_verify','T_total','H_semantic_SHA','H_fleet_SHA']},
                 'last_improving_witness_seconds':float(selected[-1]['producer_seconds'])})
stock,gd=ends
assert stock['H_semantic_SHA']==gd['H_semantic_SHA'] and stock['H_fleet_SHA']==gd['H_fleet_SHA']
assert gd['U']<stock['U'] and gd['L']>stock['L']
stage=read(OUT/'stage_rb35.json')
assert stage['decision']=='ENTER_ONE_STABLE_BASE_PRESSURE_BRIDGE' and stage['candidate_unchanged']
assert abs(stage['U_improvement_percent']-100*(stock['U']-gd['U'])/stock['U'])<1e-12
assert abs(stage['gap_improvement_percentage_points']-100*(stock['relative_gap']-gd['relative_gap']))<1e-12
assert stage['historical_BASE']['cross_PE_not_new_same_PE_evidence']
matrix_path=OUT/'base_bridge_matrix.json';matrix=read(matrix_path)
assert sha(matrix_path)=='aa595262ebcffb7ed62f39fc9511637a7aa2a12a8e6d000fd12e4487a1a5b4a2'
assert len(matrix['groups'])==1 and matrix['new_nominal_caps']==2400
assert matrix['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
assert matrix['serial'] and matrix['all_own_H'] and matrix['threads']==1 and matrix['affinity_mask']==4
assert matrix['Seed_default']==0 and matrix['H_seed']==20260626
for p,h in matrix['helpers'].items():assert sha(ROOT/p)==h,p
g=matrix['groups'][0];l=g['launch'];p=l['panel'];c=l['command'];ip=OUT/g['group']/'identity.json';identity=read(ip)
assert sha(ip)==g['identity_SHA'] and identity['launches']==[l] and identity['no_cross_arm_information']
assert identity['measured_source_commit']==manifest['source_commit'] and identity['candidate_binary_sha256']==manifest['production_PE_SHA']
assert l['R146_method']=='BASE' and l['method']=='S2' and l['id']=='R-B35-S-T2' and l['cap_seconds']==2400 and l['seed']==0
assert p['V']==35 and p['M']==3 and p['T_seconds']==7200 and p['rho']==1 and p['lambda']==1/p['Omega']
assert not p['round138_stock_rlt'] and '--round138-stock-rlt' not in c and c[c.index('--round146-gd')+1]=='off'
assert sha(ROOT/p['input_path'])==p['input_sha256'] and not Path(l['destination']).exists()
def normalized(launch):return [v.replace(launch['destination'],'<ARM>') for v in launch['command'] if v!='--round138-stock-rlt']
assert normalized(l)==normalized(old_matrix['groups'][0]['launch'])
fees=[]
for folder in (OUT/'fees').iterdir():
    assert (folder/'receipt.json').exists(),folder
    f=read(folder/'receipt.json');assert f['exit_code']==0 and not f['timeout'] and f['nested_H_LP_MIP_not_added'];fees.append(f)
fees.sort(key=lambda f:f['start_unix']);assert all(a['end_unix']<=b['start_unix'] for a,b in zip(fees,fees[1:]))
paid=sum(f['G1_seconds'] for f in fees)
assert paid==stage['total_spent']==read(OUT/'rb35_run_return.json')['budget']['G1_seconds']
assert not list((OUT/'fees').glob('base_bridge_*')) and len(list((OUT/'fees').glob('rb35_*')))==2
assert paid+2400+3000<28800
result=dict(decision='ACCEPT',independent_nonimplementer_review=True,reviewer='gd_independent_review',UTC=datetime.now(timezone.utc).isoformat(),
    matrix_SHA=sha(matrix_path),candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),source_commit=manifest['source_commit'],production_PE_SHA=manifest['production_PE_SHA'],
    Optimize=0,Native_load=0,compile=0,reverification=0,admitted_scope='One RB35-T2 stable BASE same-PE Seed0 cap2400 bridge only; no repeated STOCK/GD, K35, RN-P, new candidate or extra Seed',
    rationale='The uniform combination improves both endpoints over STOCK, but the historical stable BASE incumbent is materially better. One same-PE BASE run resolves the directly relevant stable-comparison uncertainty before recommendation.',
    RB35=ends,experimental_outer_seconds_before_bridge=paid,remaining_experimental_seconds_before_bridge=28800-paid,new_nominal_caps=2400,
    no_promotion_inferred=True,historical_BASE_is_cross_PE=True,unfavorable_bridge_must_not_trigger_automatic_rescue_grid=True,
    evidence_SHA={str(p.relative_to(OUT)):sha(p) for p in [OUT/'stage_rb35.json',OUT/'reports/full.json',OUT/'reports/same_PE_pairs.csv',OUT/'reports/verified_U_trajectories.csv',OUT/'rb35_run_return.json']})
(OUT/'review/base_bridge_admission.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['decision','matrix_SHA','experimental_outer_seconds_before_bridge','new_nominal_caps']},indent=2))
