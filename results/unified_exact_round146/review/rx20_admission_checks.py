"""Independent stage review; read sealed evidence only, never reverify/solve."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/unified_exact_round146'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest=read(OUT/'candidate_manifest.json')
previous=read(OUT/'review/k20_admission.json')
assert sha(OUT/'candidate_manifest.json')==previous['candidate_manifest_SHA']
assert sha(manifest['production_PE'])==previous['production_PE_SHA']==manifest['production_PE_SHA']
for p,h in manifest['source_hashes'].items():assert sha(ROOT/p)==h,p
full=read(OUT/'reports/full.json')
assert len(full['new_arms'])==2 and not full['failed_qualifications']
assert full['standalone_LP_Optimize_separate']==5
assert full['all_entered_observed_Native_Optimize']==full['all_entered_observed_Native_returned']
prior_matrix=read(OUT/'k20_matrix.json')
assert sha(OUT/'k20_matrix.json')==previous['matrix_SHA']
endpoints=[]
for group in prior_matrix['groups']:
    launch=group['launch'];d=Path(launch['destination'])
    a=read(d/'audit.json');e=a['endpoint'];close=read(d/'verification_closeout.json');clock=read(d/'arm_total_receipt.json')
    assert a['passed'] and a['implementation_qualified'] and a['evidence_complete'] and not a['source_rejections']
    assert close['audit_SHA']==sha(d/'audit.json') and close['native_proof_qualified'] and close['necessary_verification_complete']
    assert clock['verification_closeout_SHA']==sha(d/'verification_closeout.json')
    assert clock['producer_receipt_SHA']==sha(d/'producer_receipt.json')
    assert e['certificate'] and e['certificate_qualified'] and e['numbers_qualified'] and e['performance_eligible']
    assert e['H_complete'] and e['declared_calls']==e['returned_calls'] and e['T_cert']==e['T_produce']
    assert e['PE_SHA']==manifest['production_PE_SHA'] and e['source_commit']==manifest['source_commit']
    assert e['T_cert']+clock['T_verify']==clock['T_total']
    c=read(d/'round146_control_audit.json');assert c['PASS']
    if launch['R146_method']=='STOCK_GD':
        assert len(c['Native_audits'])==e['returned_calls']
        assert all(x['PASS'] and x['GD_rows']==2 and x['GD_nonzeros']==330 for x in c['Native_audits'])
    else:assert not c['Native_audits'] and all(x['GD_rows']==0 for x in c['models'])
    r=next(x for x in full['new_arms'] if x['method']==launch['R146_method'])
    assert r['formal_entered'] and r['role']=='K-20-S'
    for k in ['U','L','T_cert','T_produce','H_semantic_SHA','H_fleet_SHA']:assert r[k]==e[k]
    for k in ['T_verify','T_total']:assert r[k]==clock[k]
    endpoints.append(dict(method=launch['R146_method'],U=e['U'],L=e['L'],T_cert=e['T_cert'],T_total=clock['T_total'],
                          H_semantic_SHA=e['H_semantic_SHA'],H_fleet_SHA=e['H_fleet_SHA']))
stock,gd=endpoints
assert stock['U']==gd['U'] and stock['H_semantic_SHA']==gd['H_semantic_SHA'] and stock['H_fleet_SHA']==gd['H_fleet_SHA']
reduction=(stock['T_cert']-gd['T_cert'])/stock['T_cert']
assert .20<reduction<.21 and abs(gd['L']-stock['L'])<2e-14
stage=read(OUT/'stage_k20.json')
assert stage['decision']=='EXTEND_TO_RX20_STABILITY' and abs(stage['certificate_time_reduction_fraction']-reduction)<1e-15
with (OUT/'reports/same_PE_pairs.csv').open(newline='') as f:pairs=list(csv.DictReader(f))
assert len(pairs)==1 and float(pairs[0]['GD_T_cert'])==gd['T_cert'] and float(pairs[0]['STOCK_T_cert'])==stock['T_cert']
with (OUT/'reports/verified_U_trajectories.csv').open(newline='') as f:trajectory=list(csv.DictReader(f))
for group in prior_matrix['groups']:
    l=group['launch'];d=Path(l['destination']);events={x['sequence']:x for x in read(d/'observations.json')}
    selected=[x for x in trajectory if x['method']==l['R146_method']]
    assert selected and float(selected[-1]['U'])==stock['U']
    for row in selected:
        ev=events[int(row['sequence'])]
        assert row['committed_event_SHA']==ev['sha256'] and row['raw_observation_SHA']==sha(d/'observations.json')
        assert float(row['U'])==ev['payload']['objective'] and float(row['producer_seconds'])==ev['effective_available_seconds']

matrix=read(OUT/'rx20_matrix.json')
assert matrix['candidate_manifest_SHA']==previous['candidate_manifest_SHA']
assert matrix['serial'] and matrix['all_own_H'] and matrix['threads']==1 and matrix['affinity_mask']==4
assert matrix['Seed_default']==0 and matrix['H_seed']==20260626
assert len(matrix['groups'])==2 and matrix['new_nominal_caps']==2400
for p,h in matrix['helpers'].items():assert sha(ROOT/p)==h,p
commands=[]
for g,method,flag in zip(matrix['groups'],['STOCK','STOCK_GD'],['off','on']):
    l=g['launch'];p=l['panel'];assert l['id']=='R-X20-S-T1' and l['R146_method']==method
    assert l['seed']==0 and l['cap_seconds']==1200 and l['AM_threshold']==.08
    assert p['V']==20 and p['M']==2 and p['T_seconds']==4800 and p['rho']==1
    assert p['lambda']==1/p['Omega'] and p['round138_stock_rlt']
    assert sha(ROOT/p['input_path'])==p['input_sha256']
    ip=OUT/g['group']/'identity.json';identity=read(ip);assert sha(ip)==g['identity_SHA']
    assert identity['launches']==[l] and identity['candidate_binary_sha256']==manifest['production_PE_SHA']
    assert identity['measured_source_commit']==manifest['source_commit'] and identity['no_cross_arm_information']
    assert not Path(l['destination']).exists()
    c=l['command'];assert c[0]==manifest['production_PE'] and c.count('--round138-stock-rlt')==1
    for key,value in [('--round146-gd',flag),('--threads','1'),('--mip-threads','1'),('--gurobi-seed','0'),
                      ('--round127-mode','ms2'),('--process-wall-time-limit','1200'),('--time-limit','1194')]:
        assert c[c.index(key)+1]==value
    command=[v.replace(l['destination'],'<ARM>') for v in c];command[c.index('--round146-gd')+1]='<GD>'
    commands.append(command)
assert commands[0]==commands[1]
fees=[]
for p in (OUT/'fees').iterdir():
    assert (p/'receipt.json').exists(),p
    r=read(p/'receipt.json');assert r['exit_code']==0 and not r['timeout'] and r['nested_H_LP_MIP_not_added'];fees.append(r)
fees.sort(key=lambda r:r['start_unix'])
assert all(a['end_unix']<=b['start_unix'] for a,b in zip(fees,fees[1:]))
paid=sum(r['G1_seconds'] for r in fees)
assert paid==stage['total_spent']==read(OUT/'k20_run_return.json')['budget']['G1_seconds']
assert paid+2400+3000<28800
assert len(list((OUT/'fees').glob('k20_*')))==2 and not list((OUT/'fees').glob('rx20_*'))
result=dict(decision='ACCEPT',independent_nonimplementer_review=True,reviewer='gd_independent_review',
    UTC=datetime.now(timezone.utc).isoformat(),matrix_SHA=sha(OUT/'rx20_matrix.json'),
    candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),source_commit=manifest['source_commit'],production_PE_SHA=manifest['production_PE_SHA'],
    Optimize=0,Native_load=0,compile=0,reverification=0,
    admitted_scope='Only registered RX20-T1 STOCK / STOCK_GD Seed0 cap1200 pair for certified-role stability/cost; no pressure role, additional Seed or promotion',
    K20=endpoints,K20_certificate_time_reduction_fraction=reduction,K20_L_difference_is_roundoff_scale=True,
    experimental_outer_seconds_before_RX20=paid,new_nominal_caps=2400,remaining_experimental_seconds_before_RX20=28800-paid,
    rationale='K20 same objective certified about20.52% sooner against same-PE strong STOCK; one finite certified-role test is warranted, without a robustness claim',
    evidence_SHA={str(p.relative_to(OUT)):sha(p) for p in [OUT/'stage_k20.json',OUT/'reports/full.json',OUT/'reports/same_PE_pairs.csv',OUT/'reports/verified_U_trajectories.csv',OUT/'k20_run_return.json']})
(OUT/'review/rx20_admission.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['decision','matrix_SHA','K20_certificate_time_reduction_fraction','experimental_outer_seconds_before_RX20','new_nominal_caps']},indent=2))
