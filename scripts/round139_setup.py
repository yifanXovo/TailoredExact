"""Read only relevant sealed R137/R138 evidence; never optimize or import native APIs."""
from round139_common import *
import collections,csv,re
import round108_reader as core
from round138_repair import scaled_rows

def main():
    assert not budget()['unclosed']
    old138=ROOT/'results/unified_exact_round138';old137=ROOT/'results/unified_exact_round137'
    reuse=read(old138/'baseline_reuse.json');m138=read(old138/'matrix_frozen.json')
    reused=[]
    for b in reuse['baselines']:
        role=b['role'];g=next(g for g in m138['groups'] if g['launch']['id']==role and g['launch']['method']=='STOCK')
        p=g['launch']['panel'];assert sha(ROOT/p['input_path'])==p['input_sha256']
        base=b['baseline'];both=next(r for r in csv.DictReader((old138/'reports/new_arms.csv').open()) if r['role']==role and r['method']=='STOCK')
        for row in [base,both]:
            assert row['performance_eligible']=='True' and row['native_proof_qualified']=='True'
            assert int(row['seed'])==0 and int(row['cap'])==p['cap_seconds']
            assert float(row['lambda_value'])==p['lambda'] and float(row['T'])==p['T_seconds']
        reused.append(dict(role=role,panel=p,base_position=b['position'],both_position=g['position'],base=base,both=both,
            BASE_science='e735c3447eb1443713c700942d873de1783a4a26',BOTH_science='1b19897ab5819ab3b7485ddc978954b45225f361',
            BASE_measured_source='779713ad9a0b01edc538ecb64df9438739127be3',BOTH_measured_source='83928377336a860acf78f684d1723a5040467bb5',
            rationale='Frozen same input/physical and objective doubles/Seed0/cap/own-H/full-cost policy, Gurobi13.0.2 one thread affinity4; V1 primary remains V1, R138 V2 bridge reused, new actual 00/11 qualification required.'))
    write(OUT/'baseline_reuse.json',dict(UTC=utc(),positions=reused,new_Optimize=0,new_core_reused=16,
        inherited_v2_bridge_SHA=sha(old138/'repair/primary_native_bridge.json'),
        matching_environment=dict(DLL_SHA=sha(DLL),compiler_SHA=sha(COMPILER),threads=1,affinity=4),
        no_independent_validation_set=True))
    records=[]
    for role in ['K-20-S','R-B35-S-T2','K-15-S','K-35-U']:
        b=next(v for v in reused if v['role']==role);pairs={};facts=[]
        for method,key in [('BASE','base'),('BOTH','both')]:
            row=b[key];d=Path(row['raw_path']) if 'raw_path' in row else Path(row['destination'])
            # Accepted aggregate records retain this exact producer destination.
            assert d.is_dir(),d
            lp=list(csv.DictReader((d/'external/paper_optimize_ledger.csv').open(newline='')))
            am=list(csv.DictReader((d/'external/adaptive_mass_decision_ledger.csv').open(newline='')))
            observations=read(d/'observations.json');calls=[r['payload'] for r in observations if r['payload']['kind']=='call']
            models={}
            for c in calls:
                path=core.portable(ROOT,c['model_path']);assert sha(path)==c['model_sha256']
                parsed=core.lp_model(path);models[c['model_sha256']]=parsed
            initial=read(d/'external/initial_witness.json')
            source_files=['external/paper_optimize_ledger.csv','external/adaptive_mass_decision_ledger.csv','external/initial_witness.json']
            native=[];starts=[]
            for path in sorted((d/'external/native_logs').glob('*terminal_mip.gurobi.log')):
                text=path.read_text();events=[]
                for line in text.splitlines():
                    if re.match(r'^[H*]',line):
                        tokens=line.split();time_match=re.search(r'\s([0-9.]+)s\s*$',line)
                        events.append(dict(line=line,approx_native_seconds=float(time_match[1]) if time_match else None))
                native.append(dict(path=str(path),SHA256=sha(path),incumbent_events=events,
                    root=next((line for line in text.splitlines() if line.startswith('Root relaxation:')),None),
                    Start_lines=[line for line in text.splitlines() if 'MIP start' in line or 'previous solve' in line],
                    intermediate_rounded_native_objectives_not_independently_physical_U=True))
            for path in sorted((d/'external/native_logs').glob('*.round68.start.json')):
                starts.append(dict(path=str(path),SHA256=sha(path),record=read(path)))
            pairs[method]=dict(models=models,calls=calls,initial=initial)
            facts.append(dict(method=method,measured_source=b[key+'_measured_source'] if key+'_measured_source' in b else b[method+'_measured_source'],
                source_files={s:sha(d/s) for s in source_files},LP=sum(c['solve_kind']=='LP' for c in lp),
                target=sum('target' in c['native_log'] for c in lp),terminal=sum('terminal' in c['native_log'] for c in lp),
                optimize=lp,AM=am,Native=native,Starts=starts,U=float(row['U']),L=float(row['L']),
                certificate=row['certificate']=='True',T_cert=float(row['T_cert']) if row['T_cert'] else None))
        left,right=pairs['BASE'],pairs['BOTH'];comparisons=[]
        assert left['initial']==right['initial'],'same H witness required'
        for ca,cb in zip(left['calls'][:3],right['calls'][:3]):
            a=left['models'][ca['model_sha256']];z=right['models'][cb['model_sha256']]
            alpha,beta=z['bounds']['G'];p=b['panel'];data=core.evidence.instance(ROOT,p)
            B=sum(data['b'][1:]);Bm=max(0,B-sum(p['Q_vector']));stock=collections.Counter(scaled_rows(p['V'],alpha,beta,Bm,B))
            common={k:a[k]==z[k] for k in ['order','bounds','types','objective']}
            delta=collections.Counter(z['rows'])-collections.Counter(a['rows'])
            removed=collections.Counter(a['rows'])-collections.Counter(z['rows'])
            comparisons.append(dict(leaf=ca['leaf'],base_SHA=ca['model_sha256'],both_SHA=cb['model_sha256'],
                common=common,removed_rows=sum(removed.values()),added_rows=sum(delta.values()),only_four_stock_rows=(delta==stock and not removed)))
        records.append(dict(role=role,same_initial_H_witness=True,matrices=comparisons,methods=facts))
    write(OUT/'reports/inherited_mechanisms.json',dict(UTC=utc(),roles=records,Optimize=0,
        clock_scope='Native log timestamps are rounded model-objective diagnostics; controller global trace is qualified after return. Neither supplies independent physical intermediate U without a saved vector.',
        controlled_attribution='Exact common matrix comparison and immutable input/domain/H identity; differing call and retained-state paths are disclosed, no additive timing attribution.'))
    write(OUT/'start_receipt.json',dict(UTC=utc(),base=BASE,main='b2b940c1e517a72e226ec60fc49ff19651737632',
        R138_in_main=False,PR_base='codex/round138-shared-product-resource-coupling',
        branch=git('branch','--show-current').decode().strip(),protected_original='E:/codes/ExactEBRP',
        workspace_policy='All new build/raw/temp/restore under E:/codes/ExactEBRP-work; bounded current-round cleanup after delivery/public check',
        compute_limit_seconds=57600,default_new_Gurobi_Seed=0,H_seed=20260626,goal_SHA=sha(OUT/'goal.md'),
        baseline_configs_unchanged=True,no_active_solver_at_start=True))
    print('16 reused BASE/BOTH positions; four selected actual histories, common matrices and starts bound')

if __name__=='__main__':main()
