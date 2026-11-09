"""Finite saved-original scientific review; no Optimize or production execution.

Run once under the outer meter, then seal the review with its actual closed
receipt. Paper and public delivery remain separate acceptance gates.
"""
from fractions import Fraction as F
from round157_inventory import value,family
from round158_common import *

LABEL='final_scientific_review'
TARGET=OUT/'review/final_scientific_review.json'

def row(model,constr):
    expr=model.getRow(constr)
    return (constr.Sense,constr.RHS,
        {expr.getVar(j).VarName:expr.getCoeff(j) for j in range(expr.size())})

def run():
    from round100_idle import ensure_idle
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round153_pricing import Oracle
    from round158_delivery import protect
    ensure_idle();assert os.environ.get('ROUND140_METERED_PARENT_LABEL')==LABEL
    assert all(r['label']==LABEL for r in budget()['unclosed'])
    affinity();assert binding()['sha256']==DLL_SHA
    coef=read(OUT/'qualification/coefficient_v2/result.json')
    adm=read(OUT/'qualification/level_v2/result.json')
    rows=read(OUT/'qualification/level_v2/actual_raw_implication.json')
    prior=read(OUT/'qualification/level_v1/result.json')
    assert all(r['PASS'] for r in (coef,adm,rows,prior))
    assert adm['coefficient_qualification_SHA']==sha(OUT/'qualification/coefficient_v2/result.json')
    assert adm['reused_v1_checks_SHA']==sha(OUT/'qualification/level_v1/result.json')
    assert coef['existing_finite_family_exclusions_preserved_by_guard_and_identical_integer_budgets']
    assert prior['R92_counterexample_retained'] and prior['physical_comparison_boundary_retained']
    assert prior['hard_level_full_coverage'] and prior['known_lower_auxiliary_row_not_used']
    assert prior['rounded_same_integer_domain_and_LP_implication'] and prior['callback_Optimize_calls']==2
    sources=read(OLD157/'inventory_sources.json');candidates=read(OUT/'candidates.json')
    finite=[]
    for role,label in (('R-X35-S-T2','rx35_y3_v1'),('N-B35-S','nb35_continue_v1')):
        source=sources[role];candidate=candidates[role];folder=OUT/'resource'/label
        condition=read(folder/'condition.json');result=read(folder/'result.json')
        checked=read(OUT/'review'/f'{label}_readback/result.json')
        assert checked['PASS'] and checked['source_result_SHA']==sha(folder/'result.json')
        assert family(source['scope'],candidate['Y'])==condition['members']
        assert len(condition['members'])==(10 if role.startswith('R-') else 1)
        assert condition['scope']==source['scope']
        assert all(value(source['scope'],Y)['phi']==F(candidate['J_exact']) for Y in condition['members'])
        assert result['classification']=='FAMILY_RESOURCE_INFEAS' and result['normal_Optimize_return']
        assert result['valid_resource_upper'] is None and checked['U_R'] is None
        panel=source['panel'];assert sha(ROOT/panel['input_path'])==panel['input_sha256']
        fact=next(r for r in coef['facts'] if r['role']==role)
        assert fact['nominal_budget_changes']==fact['guarded_budget_changes']==fact['sqrt_cpp_mismatches']==0
        package=OUT/'qualification/coefficient_v2'/(panel['input_sha256']+'.json')
        assert sha(package)==fact['package_SHA']
        # These numbers belong to the queried v1/hypot models. The actual-C++
        # exclusion at original/guarded T transfers through identical integer
        # budgets; it is not a new unconditional C++ time minimum.
        time_limit=6300 if role.startswith('R-') else 7200
        assert F(result['required_time_lower'])>F(time_limit)+F(time_limit)*F(1e-5)
        finite.append(dict(role=role,members=len(condition['members']),classification=result['classification'],
            queried_v1_time_lower=result['required_time_lower'],actual_cpp_fixed_T_exclusion_preserved=True,
            no_novel_U_R=True,result_SHA=sha(folder/'result.json'),readback_SHA=sha(OUT/'review'/f'{label}_readback/result.json')))
    main=OUT/'level/rx35_raw_quarter_deep_v3';call=read(main/'call.json');result=read(main/'result.json')
    fee=read(OUT/'fees/level_rx35_raw_quarter_deep_v3/receipt.json')
    mainreview=read(OUT/'review/rx35_raw_quarter_deep_v3_level.json')
    assert mainreview['PASS'] and mainreview['classification']=='UNKNOWN' and mainreview['points']==[]
    assert result['status']==9 and result['SolCount']==0 and result['classification']=='UNKNOWN'
    assert result['normal_Optimize_return'] and not result['graceful_external_stop']
    assert result['Runtime']>=129600 and result['NodeCount']==258972 and result['IterCount']==160559495
    assert not result['level_excluded'] and result['U_R'] is None and result['physical_U'] is None
    assert result['new_lower']==read(OUT/'initial_intervals.json')['R-X35-S-T2']['L_I']
    assert fee['exit_observed'] and fee['exit_code']==0 and not fee['timeout'] and fee.get('supervisor_failure') is None
    assert fee['outer_seconds']>=result['Runtime']
    assert sha(main/'model.mps')==call['model_SHA']==result['model_SHA']
    assert sha(OUT/call['admission_relative'])==call['admission_SHA']
    assert sha(OUT/call['actual_row_gate_relative'])==call['actual_row_gate_SHA']
    assert call['assignment_free'] and call['all_inventory_decisions_free']
    assert call['scope']==sources['R-X35-S-T2']['scope']
    assert (call['Seed'],call['Threads'],call['MIPFocus'],call['TimeLimit'],call['NodeLimit'],call['SolutionLimit'])==(0,1,1,129600,2000000000,1)
    log=(main/'native.log').read_text(encoding='utf-8')
    assert 'Time limit reached' in log and 'Solution count 0' in log and 'Explored 258972 nodes (160559495 simplex iterations)' in log
    assert not list(main.glob('incumbent_*.json.gz')) and not (main/'solution.json.gz').exists()
    lp=read(OUT/'qualification/lp_fractional_ownership_v2/result.json')
    point_path=OUT/'qualification/lp_fractional_ownership_v2/point_exact.json.gz'
    assert lp['PASS'] and lp['Optimize']==0 and lp['exact_rational_feasible_in_both_models']
    assert sha(point_path)==lp['point_SHA'] and lp['integer_resource_upper'] is None and lp['physical_U'] is None
    assert not lp['whole_level_exclusion'] and F(lp['J_exact'])==value(call['scope'],lp['Y'])['phi']
    p={n:F(x) for n,x in load_gz(point_path).items()};lp_facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        with gp.read(str(main/'model.mps'),env=env) as model:
            base=Oracle(call['scope'],env,old_joint=True)
            base.model.update();oldvars=base.model.getVars();oldrows=base.model.getConstrs()
            for v in oldvars:
                saved=model.getVarByName(v.VarName)
                assert saved is not None and (saved.VType,saved.LB,saved.UB)==(v.VType,v.LB,v.UB),v.VarName
            for c in oldrows:
                saved=model.getConstrByName(c.ConstrName)
                assert saved is not None and row(model,saved)==row(base.model,c),c.ConstrName
            preserved=dict(columns=len(oldvars),rows=len(oldrows),objective_deliberately_replaced_by_constant_zero=True)
            base.close()
        for variant in ('raw','rounded'):
            fact=next(r for r in adm['facts'] if r['role']=='R-X35-S-T2' and r['variant']==variant)
            path=OUT/'qualification/level_v2'/f'R-X35-S-T2_{variant}.mps';assert sha(path)==fact['model_SHA']
            with gp.read(str(path),env=env) as model:
                assert set(p)=={v.VarName for v in model.getVars()}
                for c in model.getConstrs():
                    sense,rhs,coeff=row(model,c);lhs=sum((F(a)*p[n] for n,a in coeff.items()),F(0));rhs=F(rhs)
                    assert lhs<=rhs if sense=='<' else lhs>=rhs if sense=='>' else lhs==rhs,c.ConstrName
                nonintegral=0
                for v in model.getVars():
                    if math.isfinite(v.LB):assert p[v.VarName]>=F(v.LB),v.VarName
                    else:assert v.LB==-math.inf
                    if math.isfinite(v.UB):assert p[v.VarName]<=F(v.UB),v.VarName
                    else:assert v.UB==math.inf
                    nonintegral+=v.VType!='C' and p[v.VarName].denominator!=1
                assert nonintegral>0
                lp_facts.append(dict(variant=variant,rows=model.NumConstrs,columns=model.NumVars,
                    exact_rows_and_bounds_satisfied=True,nonintegral_columns=nonintegral,model_SHA=sha(path)))
    receipts=[];failed=[]
    for folder in sorted((OUT/'fees').iterdir()):
        if not folder.is_dir() or folder.name==LABEL:continue
        launch=read(folder/'launch.json');r=read(folder/'receipt.json')
        assert r['exit_observed'] and r['G1_seconds']==r['outer_seconds'] and not r['timeout'],folder.name
        assert Path(launch['command'][0])==Path(PYTHON) and Path(launch['cwd'])==ROOT
        snapshot=OUT/'engineering/source_snapshots'/f'{folder.name}.json';s=read(snapshot)
        for name,digest in s['files'].items():assert sha(OUT/'engineering/source_bytes'/f'{digest}.txt')==digest,name
        rec=dict(label=folder.name,exit_code=r['exit_code'],outer_seconds=r['outer_seconds'],receipt_SHA=sha(folder/'receipt.json'),
            launch_SHA=sha(folder/'launch.json'),source_snapshot_SHA=sha(snapshot))
        receipts.append(rec)
        if r['exit_code']:failed.append(rec)
    assert {r['label'] for r in failed}=={'prepare','lp_fractional_witness'}
    assert abs(sum(r['outer_seconds'] for r in receipts)-budget()['G1_seconds'])<1e-8
    assert budget()['G1_seconds']<TOTAL
    changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    assert set(changed)<={'.gitattributes','.gitignore','results/unified_exact_round157/RESUME.md','results/unified_exact_round157/final_report.md'},changed
    runtime=read(OUT/'infra/active_runtime_identity.json')
    assert sha(Path(PYTHON))==runtime['LauncherSHA']
    assert sha(Path(runtime['NativeWorkerExecutable']))==runtime['NativeWorkerExecutableSHA']
    assert runtime['GurobiDLLSHA_verified_by_child_binding_at_start']==DLL_SHA
    pe=WORK/'build-cache/round156/v1/ExactEBRP.exe'
    assert sha(pe)=='e5efe978f33e5c812fc9a0484caaae80696e4197ae27e289b4894d586af9d7e6'
    snap=read(OUT/'engineering/source_snapshots/level_rx35_raw_quarter_deep_v3.json')
    source_manifest=dict(UTC=utc(),dependency_base=BASE,production_source='092bad58d677cd8bef934d91e11d8abff93cba83',
        production_PE=dict(path=str(pe),SHA256=sha(pe),executions=0,new_builds=0),runtime=runtime,
        current_scripts={p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT/'scripts').glob('round158*.py'))},
        actual_main_source_snapshot=snap,actual_main_script_SHA=snap['files']['scripts/round158_level.py'],
        current_level_script_SHA=sha(ROOT/'scripts/round158_level.py'),
        late_assertion_note='Future-call pre-Optimize hash assertion was added after launch; actual launched bytes and manual/closed-matrix hash admission are authoritative. The late assertion is not claimed executed by the completed main.',
        inherited_tracked_changes=changed,production_CPP_or_configuration_changes=False,protected_dirty_files=protect())
    write(OUT/'source_manifest.json',source_manifest)
    write(TARGET,dict(UTC=utc(),PASS=False,scientific_checks_PASS=True,own_receipt_pending_seal=True,Optimize=0,
        review_method='Same agent separate saved-original matrix, rational point, inventory-price, scope and outer-fee readback; no independent reviewer identity',
        main=result,main_result_SHA=sha(main/'result.json'),main_fee_SHA=sha(OUT/'fees/level_rx35_raw_quarter_deep_v3/receipt.json'),
        old_RN_preserved=preserved,finite_family_scope_checks=finite,lp_saved_point_exact_checks=lp_facts,
        prior_qualification_reused=True,no_historical_producer_or_performance_reruns=True,
        closed_other_fees=receipts,failed_calls_retained=failed,other_G1_seconds=budget()['G1_seconds'],
        source_manifest_SHA=sha(OUT/'source_manifest.json'),own_receipt='fees/'+LABEL+'/receipt.json',
        science_question_open=True,new_integer_resource_upper=None,new_physical_U=None,new_original_J_lower=None,
        conditional_EplusR_panel_entered=False,paper_and_public_delivery='Separate pending acceptance gates'))
    print(json.dumps(dict(scientific_checks_PASS=True,own_receipt_pending_seal=True,Optimize=0)),flush=True)

def seal():
    r=read(TARGET);assert r['scientific_checks_PASS'] and r['own_receipt_pending_seal']
    receipt=read(OUT/r['own_receipt']);b=budget()
    assert not b['unclosed'] and receipt['exit_observed'] and receipt['exit_code']==0 and not receipt['timeout']
    assert abs(r['other_G1_seconds']+receipt['G1_seconds']-b['G1_seconds'])<1e-8
    r.update(PASS=True,own_receipt_pending_seal=False,own_receipt_SHA=sha(OUT/r['own_receipt']),
        closed_G1_seconds=b['G1_seconds'],all_fees_closed_at_seal=True,seal_UTC=utc())
    write(TARGET,r);print(json.dumps(dict(PASS=True,G1_seconds=b['G1_seconds'],fees=len(r['closed_other_fees'])+1)),flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
