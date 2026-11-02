"""Independent finite pressure admission from existing sealed evidence only."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/unified_exact_round146'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=read(OUT/'review/rx20_admission.json');m=read(OUT/'candidate_manifest.json')
assert old['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
assert old['production_PE_SHA']==m['production_PE_SHA']==sha(m['production_PE'])
for p,h in m['source_hashes'].items():assert sha(ROOT/p)==h
retained=[]
for p,h in old['evidence_SHA'].items():
    matches=[q for q in [OUT/p,*list((OUT/'stages').glob('*/'+Path(p).name))] if q.exists() and sha(q)==h]
    assert matches,p
    retained.append(dict(logical_path=p,SHA=h,retained_path=str(matches[0].relative_to(OUT))))
prior=read(OUT/'rx20_matrix.json');assert sha(OUT/'rx20_matrix.json')==old['matrix_SHA']
full=read(OUT/'reports/full.json');assert len(full['new_arms'])==4 and not full['failed_qualifications']
assert full['all_entered_observed_Native_Optimize']==full['all_entered_observed_Native_returned']==23
assert full['standalone_LP_Optimize_separate']==5
ends=[]
for g in prior['groups']:
    d=Path(g['launch']['destination']);a=read(d/'audit.json');e=a['endpoint'];c=read(d/'verification_closeout.json');t=read(d/'arm_total_receipt.json')
    assert a['passed'] and a['implementation_qualified'] and a['evidence_complete'] and not a['source_rejections']
    assert c['audit_SHA']==sha(d/'audit.json') and t['verification_closeout_SHA']==sha(d/'verification_closeout.json')
    assert c['native_proof_qualified'] and c['necessary_verification_complete'] and t['necessary_verification_complete']
    assert e['certificate'] and e['certificate_qualified'] and e['numbers_qualified'] and e['performance_eligible'] and e['H_complete']
    assert e['PE_SHA']==m['production_PE_SHA'] and e['source_commit']==m['source_commit']
    assert e['T_cert']==e['T_produce'] and e['declared_calls']==e['returned_calls']
    assert abs(e['T_cert']+t['T_verify']-t['T_total'])<1e-12
    r=next(x for x in full['new_arms'] if x['role']=='R-X20-S-T1' and x['method']==g['launch']['R146_method'])
    for k in ['U','L','T_cert','H_semantic_SHA','H_fleet_SHA']:assert r[k]==e[k]
    for k in ['T_total','T_verify']:assert r[k]==t[k]
    ends.append(dict(method=g['launch']['R146_method'],U=e['U'],L=e['L'],T_cert=e['T_cert'],T_total=t['T_total'],
                     H_semantic_SHA=e['H_semantic_SHA'],H_fleet_SHA=e['H_fleet_SHA']))
assert ends[0]['U']==ends[1]['U'] and ends[0]['H_semantic_SHA']==ends[1]['H_semantic_SHA'] and ends[0]['H_fleet_SHA']==ends[1]['H_fleet_SHA']
assert 2.7<ends[0]['T_cert']-ends[1]['T_cert']<2.71
stage=read(OUT/'stage_rx20.json');assert stage['decision']=='ENTER_RB35_PRESSURE_PAIR'
assert stage['stable_BASE_not_yet_same_PE_on_this_role'] and stage['candidate']=='STOCK+GD-state'
matrix=read(OUT/'rb35_matrix.json');assert matrix['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
assert matrix['new_nominal_caps']==4800 and len(matrix['groups'])==2
assert matrix['serial'] and matrix['all_own_H'] and matrix['threads']==1 and matrix['affinity_mask']==4
assert matrix['Seed_default']==0 and matrix['H_seed']==20260626
for p,h in matrix['helpers'].items():assert sha(ROOT/p)==h,p
commands=[]
for g,method,flag in zip(matrix['groups'],['STOCK','STOCK_GD'],['off','on']):
    l=g['launch'];p=l['panel'];c=l['command'];ip=OUT/g['group']/'identity.json';identity=read(ip)
    assert l['id']=='R-B35-S-T2' and l['R146_method']==method and l['seed']==0 and l['cap_seconds']==2400 and l['AM_threshold']==.08
    assert p['V']==35 and p['M']==3 and p['T_seconds']==7200 and p['rho']==1 and p['lambda']==1/p['Omega']
    assert p['round138_stock_rlt'] and sha(ROOT/p['input_path'])==p['input_sha256']
    assert sha(ip)==g['identity_SHA'] and identity['launches']==[l]
    assert identity['candidate_binary_sha256']==m['production_PE_SHA'] and identity['measured_source_commit']==m['source_commit']
    assert identity['candidate_manifest_SHA']==matrix['candidate_manifest_SHA'] and identity['no_cross_arm_information']
    assert not Path(l['destination']).exists()
    assert c[0]==m['production_PE'] and c.count('--round138-stock-rlt')==1
    for k,v in [('--round146-gd',flag),('--threads','1'),('--mip-threads','1'),('--gurobi-seed','0'),
                ('--round127-mode','ms2'),('--process-wall-time-limit','2400'),('--time-limit','2394'),('--T','7200')]:assert c[c.index(k)+1]==v
    cc=[v.replace(l['destination'],'<ARM>') for v in c];cc[c.index('--round146-gd')+1]='<GD>';commands.append(cc)
assert commands[0]==commands[1]
fees=[]
for p in (OUT/'fees').iterdir():
    assert (p/'receipt.json').exists(),p
    r=read(p/'receipt.json');assert r['exit_code']==0 and not r['timeout'] and r['nested_H_LP_MIP_not_added'];fees.append(r)
fees.sort(key=lambda f:f['start_unix']);assert all(a['end_unix']<=b['start_unix'] for a,b in zip(fees,fees[1:]))
paid=sum(f['G1_seconds'] for f in fees)
assert paid==stage['total_spent']==read(OUT/'rx20_run_return.json')['budget']['G1_seconds']
assert not list((OUT/'fees').glob('rb35_*')) and len(list((OUT/'fees').glob('rx20_*')))==2 and len(list((OUT/'fees').glob('k20_*')))==2
assert paid+4800+3000<28800
result=dict(decision='ACCEPT',independent_nonimplementer_review=True,reviewer='gd_independent_review',UTC=datetime.now(timezone.utc).isoformat(),
    matrix_SHA=sha(OUT/'rb35_matrix.json'),candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),source_commit=m['source_commit'],production_PE_SHA=m['production_PE_SHA'],
    Optimize=0,Native_load=0,compile=0,reverification=0,
    admitted_scope='Only RB35-T2 STOCK / STOCK_GD Seed0 pair, both registered cap2400 windows; no BASE bridge, K35, extra Seed or promotion yet',
    rationale='K20 strong-reference certificate benefit and RX20 same-objective certification with small absolute time benefit warrant one historical-regression pressure role',
    RX20=ends,RX20_certificate_seconds_saved=ends[0]['T_cert']-ends[1]['T_cert'],RX20_L_difference=ends[1]['L']-ends[0]['L'],
    original_tolerance_policy_unchanged=True,stable_BASE_not_yet_same_PE_on_pressure_role=True,
    conditional_recommendation_requirement='If recommending STOCK+GD, obtain needed same-PE BASE pressure-role comparison; superiority to STOCK alone does not establish stable BASE improvement',
    experimental_outer_seconds_before_RB35=paid,remaining_experimental_seconds_before_RB35=28800-paid,new_nominal_caps=4800,
    previous_review_carriers_retained=retained,
    evidence_SHA={str(p.relative_to(OUT)):sha(p) for p in [OUT/'stage_rx20.json',OUT/'reports/full.json',OUT/'reports/same_PE_pairs.csv',OUT/'reports/verified_U_trajectories.csv',OUT/'rx20_run_return.json']})
(OUT/'review/rb35_admission.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['decision','matrix_SHA','experimental_outer_seconds_before_RB35','new_nominal_caps','RX20_certificate_seconds_saved']},indent=2))
