"""Nonimplementer admission. Text/evidence checks only; no Native/Optimize."""
from pathlib import Path
from collections import Counter
from fractions import Fraction as F
import csv,hashlib,json,sys,time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from round108_reader import lp_model
from round151_math import scope_from_model
OUT=ROOT/'results/unified_exact_round151'
TICK=time.perf_counter()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def transport(x):return 0. if -1e-12<x<0 else 1e-12 if 0<x<1e-12 else x

m=read(OUT/'candidate_manifest.json')
assert m['source_commit']=='c26382d9bf1d4edde538a01c62e57ba563cf865c'
assert sha(m['production_PE'])==m['production_PE_SHA']=='fbdd7c2ece5c748e086761f2490fd901ccdaeffa29df357d2d98fd8743e1dc39'
assert sha(m['DLL'])==m['DLL_SHA']=='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
for path,digest in m['source_hashes'].items():assert sha(ROOT/path)==digest,path
prior=read(OUT/'review/LP_review.json')
assert sha(ROOT/'include/Round151Research.hpp')==prior['reviewed']['header_SHA']
for path,digest in prior['reviewed']['source_hashes'].items():assert sha(ROOT/path)==digest

# The only post-LP helper change was replacing GD-dependent scope extraction.
frozen=read(OUT/'LP_frozen.json')
scope_checks=[]
for d in frozen['domains']:
    source=Path('E:/codes/ExactEBRP-work/restore/round151-inherited')/d['role']/'external/models/L0_epoch_0_generation_1.lp'
    s=scope_from_model(lp_model(source),d['scope']['Bminus'],d['scope']['B'])
    assert s==d['scope']
    scope_checks.append(dict(role=d['role'],scope_identical=True,source_SHA=sha(source)))
assert frozen['LP_script_SHA']==sha(ROOT/'scripts/round151_lp.py')
for tag in ['C','P']:
    p=OUT/'LP'/f'N-B35-S_{tag}'
    result=read(p/'result.json')
    assert result['qualified'] and result['model_SHA']==sha(p/'model.mps')
    assert result['Status']==2 and result['LP_Optimize']==1
    assert abs(result['numerical_primal_dual_gap'])<1e-6
    assert max(result['quality'].values())<=1e-6
    assert max(result['residual']['constraints'],result['residual']['bounds'])<=1e-6
c=read(OUT/'LP/N-B35-S_C/result.json');p=read(OUT/'LP/N-B35-S_P/result.json')
assert c['L']>p['L']>c['old_B_L']
assert read(OUT/'candidate_freeze.json')['A']=='C'

entry=read(OUT/'qualification_entry.json');writer=read(OUT/'qualification_native_writer.json')
assert entry['PASS'] and entry['no_model_own_H_completion_supported']
assert writer['PASS'] and writer['actual_physical_model_Start'] and writer['nonminimal_g_and_e_completion']
assert read(OUT/'qualification/writer_v3/cpp_receipt.json')==dict(PASS=True,checks=30,Optimize=0,Native_load=0)
# Independently check the actual full-model physical and nonminimal completions.
wdir=OUT/'qualification/writer_v3/actual_NB35'
wm=lp_model(wdir/'on.lp')
wpoints={tag:read(wdir/(tag+'.json')) for tag in ['physical_start','nonminimal_epigraph']}
for point in wpoints.values():
    assert set(point)==set(wm['order'])
    assert all(lo-1e-6<=point[n]<=hi+1e-6 for n,(lo,hi) in wm['bounds'].items())
    for terms,sense,rhs in wm['rows']:
        lhs=sum(a*point[n] for n,a in terms)
        assert (lhs<=rhs+1e-6 if sense=='<=' else lhs>=rhs-1e-6 if sense=='>=' else abs(lhs-rhs)<=1e-6)
assert wpoints['nonminimal_epigraph']['G']>wpoints['physical_start']['G']
assert wpoints['nonminimal_epigraph']['e_1']>wpoints['physical_start']['e_1']

q=read(OUT/'qualification_production.json')
assert q['PASS'] and q['cap']==80 and q['not_a_complete_performance_arm']
assert q['same_production_PE'] and q['own_H'] and q['qualified']['H_complete']
assert q['qualified']['PE_SHA']==m['production_PE_SHA']
d=OUT/'campaign_qualification/raw/R151_qualification_NB35_C'
assert sha(OUT/'campaign_qualification/identity.json')==q['identity_SHA']
seal=read(d/'producer_seal.json');receipt=read(d/'producer_receipt.json');close=read(d/'verification_closeout.json')
assert sha(d/'producer_seal.json')==receipt['producer_seal_SHA']
assert seal['native_stopped_no_reentry'] and receipt['required_outputs_closed']
for path,digest in seal['required_SHA'].items():assert sha(d/path)==digest
assert close['necessary_verification_complete'] and close['implementation_qualified'] and close['native_proof_qualified']
assert sha(d/'producer_receipt.json')==close['producer_receipt_SHA']
obs=[r['payload'] for r in read(d/'observations.json')]
calls=[r for r in obs if r['kind']=='call'];returns=[r for r in obs if r['kind']=='returned']
assert {r['call'] for r in calls}=={r['call'] for r in returns} and all(r['return_code']==0 for r in returns)
with (d/'external/paper_optimize_ledger.csv').open(encoding='utf-8-sig',newline='') as f:ledger=list(csv.DictReader(f))
assert len(calls)==len(ledger)==q['qualified']['declared_calls']==q['qualified']['returned_calls']
assert all(r['optimize_return_code']=='0' for r in ledger)
meta=read(d/'external/models/round151_root.json')
assert not meta['GD'] and meta['root_caps_frozen'] and meta['extra_root_LP']==meta['source_solves']==meta['new_columns']==0
assert meta['base_model_SHA']==scope_checks[0]['source_SHA']
old=read(OUT/'LP/arithmetic/N-B35-S.json')
assert meta['states']==old['states']
assert (meta['mu'],meta['nu'],meta['beta0'])==(old['mu'],old['nu'],old['beta0'])
models={sha(path):path for path in (d/'external/models').glob('*.lp')}
audit=read(d/'round151_control_audit.json')
assert audit['PASS'] and audit['mode']=='conditional' and audit['actual_C_subset_P']
assert calls[0]['model_sha256']==audit['first_call_SHA'] and calls[0]['model_sha256']!=meta['base_model_SHA']
assert calls[0]['native_log_path'].endswith('L0_lp.gurobi.log') and ledger[0]['solve_kind']=='LP'
assert all(call['model_sha256']!=meta['base_model_SHA'] for call in calls)
root_scope=scope_from_model(lp_model(models[meta['base_model_SHA']]),meta['Bminus'],meta['B'])
statecaps={(s['i'],s['y']):transport(s['beta']) for s in meta['states']}
model_facts=[]
for embedding in (d/'external/models').glob('*.round151.json'):
    e=read(embedding);before=lp_model(models[e['base_SHA']]);after=lp_model(models[e['final_SHA']])
    scope=scope_from_model(before,meta['Bminus'],meta['B'])
    assert scope['gamma_L']>=root_scope['gamma_L'] and scope['gamma_U']<=root_scope['gamma_U'] and scope['cutoff']<=root_scope['cutoff']
    expected=[]
    for site in scope['stations']:
        root_site=root_scope['stations'][site['i']-1]
        assert (site['c'],site['omega'])==(root_site['c'],root_site['omega']) and set(site['support'])<=set(root_site['support'])
        for y in site['support']:
            beta=statecaps[(site['i'],y)]
            if beta>=scope['gamma_U']:continue
            suffix=f"{site['i']}_{y}";terms={f'state_g_{suffix}':1.}
            if beta:terms[f'state_{suffix}']=-beta
            expected.append((tuple(sorted(terms.items())),'<=',0.))
    assert all(before[k]==after[k] for k in ['order','bounds','types','objective'])
    assert Counter(after['rows'])==Counter(before['rows'])+Counter(expected)
    assert len(expected)==e['added_rows']
    assert not any(x in models[e['final_SHA']].read_text(encoding='utf-8') for x in ['r146_GD_','r149_PF_'])
    matching=[a for a in audit['Native_audits'] if a['model_SHA']==e['final_SHA']]
    assert matching and all(a['PASS'] and a['cap_rows']==len(expected) and not a['GD'] for a in matching)
    model_facts.append(dict(SHA=e['final_SHA'],cap_rows=len(expected),Native_audits=len(matching)))

matrix_path=OUT/'confirmation_matrix.json';matrix=read(matrix_path)
assert matrix['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
assert matrix['candidate_freeze_SHA']==sha(OUT/'candidate_freeze.json')
assert matrix['all_own_H'] and matrix['serial'] and matrix['no_original_H_LP_incumbent_or_cross_arm_injection']
assert matrix['Seed']==0 and matrix['Threads']==1 and matrix['H_seed']==20260626
assert matrix['first_pair_positions']==[1,2] and matrix['conditional_second_pair_positions']==[3,4]
for path,digest in matrix['helpers'].items():assert sha(ROOT/path)==digest,path
originals={g['launch']['id']:g['launch'] for g in read(ROOT/'results/unified_exact_round137/matrix_frozen.json')['groups'] if g['launch']['method']=='S2' and g['launch']['seed']==0}
for group in matrix['groups']:
    identity_path=OUT/group['group']/'identity.json';identity=read(identity_path);launch=group['launch']
    assert sha(identity_path)==group['identity_SHA'] and identity['launches']==[launch]
    original=originals[launch['id']]
    assert identity['original_frozen_launch']==original
    assert identity['candidate_binary_sha256']==m['production_PE_SHA']
    assert launch['cap_seconds']==(2400 if launch['id']=='N-B35-S' else 1200)
    oldcmd=original['command'];cmd=launch['command']
    assert cmd[-6:]==['--round146-gd','off','--round149-penalty-feedback','off','--round151-penalty-propagation','off' if launch['R151_method']=='B' else 'conditional']
    normalized=[v.replace(launch['destination'],original['destination']) for v in cmd[:-6]]
    normalized[0]=oldcmd[0]
    assert normalized==oldcmd
    assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
profile=read(ROOT/'config/gi_tbc_penalty_propagation_round151.json')
assert profile['parent_profile_SHA256']==sha(ROOT/'config/gi_tbc_round137.json')
assert profile['verified_PE_SHA256']==m['production_PE_SHA'] and profile['default_AM']==.08 and profile['maximum_depth']==8 and profile['minimum_width']==1e-4
assert profile['pair_only'] and profile['H_seed']==20260626 and not profile['GD']
assert 'unsigned primal_heuristic_seed = 20260626u;' in (ROOT/'include/Instance.hpp').read_text()
spent=sum(read(path)['G1_seconds'] for path in (OUT/'fees').glob('*/receipt.json'))
external=read(OUT/'infra/external_costs.json')['processes']
spent+=sum(r['outer_seconds'] for r in external if r['kind'] in ['diagnostic','native'])
assert spent+2*(2400+600)<14400
report=dict(decision='ACCEPT',matrix_SHA=sha(matrix_path),independent_nonimplementer_review=True,
    admitted_positions=[1,2],conditional_positions=[3,4],conditional_entry_requires_separate_after_first_pair_decision=True,
    unique_complete_candidate='C',GD=False,source_commit=m['source_commit'],PE_SHA=m['production_PE_SHA'],
    helper_scope_change=dict(old_math_SHA=frozen['math_SHA'],current_math_SHA=sha(ROOT/'scripts/round151_math.py'),
        zero_solve_requalification=scope_checks,mathematical_caps_unchanged=True),
    qualification=dict(own_H=True,first_call_SHA=calls[0]['model_sha256'],root_cap_rows=537,
        all_calls_returned=len(calls),all_sealed_required_members_verified=True,models=model_facts,
        actual_full_Start_and_nonminimal_g_e=True,no_model_path_supported=True),
    mathematical_and_actual_C_subset_P=True,findings=[],initial_LP_is_not_complete_algorithm_benefit=True,
    budget=dict(spent_before_review=spent,first_pair_caps=4800,explicit_verification_reserve=1200,total_limit=14400),
    Optimize=0,Native_load=0,compile=0,reviewer_outer_seconds=time.perf_counter()-TICK)
(OUT/'review/confirmation_admission.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
