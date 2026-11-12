"""Independent read-only numeric and document identity review. No solver imports."""
from pathlib import Path
import csv, hashlib, io, json, math, re, subprocess
ROOT=Path(__file__).resolve().parents[3]
P=ROOT/'results/unified_exact_round137'; O=ROOT/'results/unified_exact_round165'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fixed(commit,path):return json.loads(subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT))
checks={}; failures=[]
def check(name,value):
    checks[name]=bool(value)
    if not value:failures.append(name)
new=read(ROOT/'results/unified_exact_round164/reports/complete_arms.json')
old=read(ROOT/'results/unified_exact_round163/reports/complete_arms.json')
fixednew=fixed('b93a8a01ff1b7f3cbee67807be3ac6591db4767f','results/unified_exact_round164/reports/complete_arms.json')
fixedold=fixed('8ae25cbcbb88caa283d345b1b143ff0da6e5c0eb','results/unified_exact_round163/reports/complete_arms.json')
check('24_new_arms_and_18_old_arms',len(new)==24 and len(old)==18)
check('fixed_numeric_new_identity',new==fixednew)
check('fixed_historical_Seed0_identity',old==fixedold)
check('new_no_Eplus',set(r['R164_method'] for r in new)=={'B','P'})
check('old_six_Eplus',sum(r['R163_method']=='Eplus' for r in old)==6)
pairs=read(ROOT/'results/unified_exact_round164/reports/three_seed_comparisons.json')
bykey={(r['id'],r['gurobi_seed'],r['R164_method']):r for r in new}
bykey.update({(r['id'],0,r['R163_method']):r for r in old if r['R163_method'] in ['B','P']})
check('36_unique_BP_observations',len(bykey)==36)
check('18_unique_pairs_six_inputs',len(pairs)==18 and len({(r['id'],r['gurobi_seed']) for r in pairs})==18 and len({r['id'] for r in pairs})==6)
for pair in pairs:
    for method in ['B','P']:
        arm=bykey[(pair['id'],pair['gurobi_seed'],method)]
        for field,armfield in [('U','U'),('L','final_proof_L'),('T_cert','T_cert'),('state','state')]:
            check(f"pair_original_{pair['id']}_S{pair['gurobi_seed']}_{method}_{field}",pair[method+'_'+field]==arm[armfield])
    check(f"pair_deltas_{pair['id']}_S{pair['gurobi_seed']}",abs((pair['B_U']-pair['P_U'])-pair['delta_U'])<1e-15 and abs((pair['B_L']-pair['P_L'])-pair['delta_L'])<1e-15)
for seed in [0,1,2]:
    rows=[r for r in pairs if r['gurobi_seed']==seed]
    check(f'cert_counts_S{seed}',sum(r['B_state']=='CERT' for r in rows)==3 and sum(r['P_state']=='CERT' for r in rows)==1)
    joint=[r for r in rows if r['joint_CERT']]
    check(f'joint_intersection_S{seed}',len(joint)==1 and joint[0]['id']=='R163-B20-B')
check('all_n35_OPEN',all(r['state']=='OPEN' and r['T_cert'] is None for r in bykey.values() if r['V']==35))
c35=sorted([r for r in pairs if r['id']=='R163-C35-U'],key=lambda r:r['gurobi_seed'])
check('C35_reverse_U_persistent_L',[r['delta_U_sign'] for r in c35]==[1,-1,-1] and [r['delta_L_sign'] for r in c35]==[1,1,1])
check('C35_old_P_better_all_B',c35[0]['P_U']==.09331934374779818 and all(c35[0]['P_U']<r['B_U'] for r in c35))
analysis=list(csv.DictReader((O/'analysis/three_seed_endpoints.csv').open(encoding='utf-8')))
check('figure_CSV_36',len(analysis)==36)
for row in analysis:
    arm=bykey[(row['configuration'],int(row['Seed']),row['method'])]
    check('figure_'+row['configuration']+row['Seed']+row['method'],float(row['U'])==arm['U'] and float(row['L'])==arm['final_proof_L'] and row['state']==arm['state'])
eplus={r['id']:r for r in old if r['R163_method']=='Eplus'}
b0={r['id']:r for r in old if r['R163_method']=='B'}
check('Eplus_U_equal_all_six',all(eplus[k]['U']==b0[k]['U'] for k in eplus))
gains=[k for k in eplus if abs(eplus[k]['final_proof_L']-b0[k]['final_proof_L'])>1e-7]
check('Eplus_only_X35_L',gains==['R163-X35-S'] and b0[gains[0]]['final_proof_L']==.3949882559151472 and eplus[gains[0]]['final_proof_L']==.42319954961578576)
time_diffs=[]
for k in eplus:
    if eplus[k]['state']==b0[k]['state']=='CERT':
        delta=eplus[k]['T_cert']-b0[k]['T_cert'];scale=max(10,.1*min(eplus[k]['T_cert'],b0[k]['T_cert']))
        time_diffs.append(dict(id=k,seconds=delta,scale=scale,material=abs(delta)>=scale))
check('Eplus_only_C20_material_time',[r['id'] for r in time_diffs if r['material']]==['R163-C20-S'])
arrivals=read(ROOT/'results/unified_exact_round164/reports/primal_target_arrival.json')
check('arrival36_non_exact',len(arrivals)==36 and all(not r['exact_first_discovery_time_known'] and not r['production_target_used'] for r in arrivals))
check('X35_B_new_unreached',all(not r['reached_observed'] for r in arrivals if r['id']=='R163-X35-S' and r['method']=='B' and r['gurobi_seed'] in [1,2]))
check('C35_all_B_unreached',all(not r['reached_observed'] for r in arrivals if r['id']=='R163-C35-U' and r['method']=='B'))
summary=read(P/'reports/summary.json');arms=read(P/'reports/arms.json')
check('R137_120_unique_positions',len(arms)==120 and len({r['position'] for r in arms})==120)
for stage,expect in [('B1',{'S2':9,'P':7,'PS':7}),('B2',{'S2':4,'P':0,'PS':0})]:
    check('R137_'+stage,all(sum(r['certificate'] and r['performance_eligible'] for r in arms if r['stage']==stage and r['method']==m)==count for m,count in expect.items()))
check('OPEN_null_Tcert_all_generations',all(r['T_cert'] is None for r in arms if not r['certificate']) and all(r['T_cert'] is None for r in new+old if r['state']=='OPEN'))
recon=read(O/'main_table_reconciliation.json')
check('CSV_actual91_91_103_no106',[r['rows'] for r in recon['tables']]==[91,91,103] and not recon['full_106_exact_found'])
def csvrows(p):
    b=p.read_bytes()
    for enc in ['utf-8-sig','gb18030']:
        try:return list(csv.reader(io.StringIO(b.decode(enc)))),enc
        except UnicodeDecodeError:pass
master=ROOT/'results/unified_exact_round164/reports/GI_TBC_vs_P_GRB_All_Tested_Instances.csv'
increment=ROOT/'results/unified_exact_round164/reports/GI_TBC_vs_P_GRB_Round164_Increment.csv'
mr,me=csvrows(master);inc,ie=csvrows(increment)
check('CSV103_28cols_increment12',len(mr)==104 and all(len(r)==28 for r in mr) and len(inc)==13 and all(len(r)==28 for r in inc))
check('12_increment_exact_once',all(mr.count(row)==1 for row in inc[1:]))
check('CSV_user_files_unchanged',all(sha(Path(t['path']))==t['SHA256'] for t in recon['tables']))
manifest=read(O/'source_manifest.json');build=read(O/'document_build.json')
check('current_component_bindings',all(sha(ROOT/r['path'])==r['SHA256'] for r in manifest['components']))
check('current_output_bindings',all(sha(ROOT/r['path'])==r['SHA256'] for r in build['outputs']))
check('measured_Cpp_identity',manifest['later_measured_CPP']=='e920b92e199e825ec89a2932f701861ff158e0d4' and manifest['R164_numeric_commit']=='b93a8a01ff1b7f3cbee67807be3ac6591db4767f')
body=(P/'paper_body.md').read_text(encoding='utf-8-sig');app=(P/'model_and_algorithm_appendices.md').read_text(encoding='utf-8-sig')
check('assembled_current_exact', (P/'manuscript.md').read_text(encoding='utf-8-sig')==body.rstrip()+'\n\n\\clearpage\n\n'+app.rstrip()+'\n')
result=dict(reviewer='/root/data_review',checks=checks,failures=failures,check_count=len(checks),Eplus_time_differences=time_diffs,CSV_encoding=dict(master=me,increment=ie),reviewed_components={r['path']:sha(ROOT/r['path']) for r in manifest['components']},reviewed_PDFs={r['path']:sha(ROOT/r['path']) for r in build['outputs']},new_solver_calls=0)
(O/'review/data_review_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(check_count=len(checks),failures=failures,time_diffs=time_diffs)))
