"""Bounded actual historical fault regressions, standard library, zero native."""
from round110_common import *
import copy, csv, math, shutil
from fractions import Fraction
import round110_evidence as rule
import round109_numerical_recovery as oldscope
import round109_interval_pairs as intervals
import round108_reader as core

def prepare():
    old=Path('E:/codes/ExactEBRP-round109');dest=OUT/'qualification/regression_fixture';dest.mkdir(parents=True,exist_ok=False)
    paths=['results/unified_exact_round109/review/mechanism_correction01.json',
        'results/unified_exact_round109/review/cross_arm_diagnosis02/exact_binary64_matrix_witness.json',
        'results/unified_exact_round109/review/main06_diagnosis02/exact_binary64_matrix_witness.json']
    for sub in ['campaign/raw/15_G50-C1_S0_P-GRB','campaign/raw/17_G50-C2_S0_P-GRB','qualification/cli01/raw/04_H100_S1_P-GRB']:
        for name in ['launch.json','observations.json','completion.json','result.json','audit.json','native.log','phases.csv','compact.lp']:
            paths.append('results/unified_exact_round109/'+sub+'/'+name)
        if 'S1' in sub:paths.append('results/unified_exact_round109/'+sub+'/computed_seed_scope.json')
    copied=[]
    for relative in paths:
        target=dest/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/relative,target)
        copied.append(dict(original_relative=relative,path=target.relative_to(ROOT).as_posix(),SHA=sha(target),bytes=target.stat().st_size))
    write(dest/'manifest.json',dict(files=copied,original_R109_HEAD=BASE,zero_Optimize=True,
        old_PE_identity_is_regression_only=True,not_a_R110_rejection_authority=True,
        old_P15_whole_receipt_absent=not (old/'results/unified_exact_round109/campaign/raw/15_G50-C1_S0_P-GRB/whole_arm_receipt.json').exists(),
        old_P17_whole_receipt_absent=not (old/'results/unified_exact_round109/campaign/raw/17_G50-C2_S0_P-GRB/whole_arm_receipt.json').exists()))

def run(label='finite_regressions01'):
    fixture=OUT/'qualification/regression_fixture';manifest=read(fixture/'manifest.json');d=OUT/'qualification'/label;d.mkdir(exist_ok=False)
    raw={v['path']:sha(ROOT/v['path']) for v in manifest['files']};assert all(raw[v['path']]==v['SHA'] for v in manifest['files'])
    cases=[]
    def need(value,name):assert value,name;cases.append(dict(name=name,passed=True))
    def reject(name,action):
        try:action()
        except (AssertionError,KeyError,ValueError,TypeError):cases.append(dict(name=name,rejected=True))
        else:raise AssertionError('bad finite case accepted: '+name)
    get=lambda relative:fixture/'results/unified_exact_round109'/relative
    for ordinal,role,review in [(15,'G50-C1','cross_arm_diagnosis02'),(17,'G50-C2','main06_diagnosis02')]:
        arm=get(f'campaign/raw/{ordinal:02d}_{role}_S0_P-GRB');launch=read(arm/'launch.json');p=launch['panel'];obs=read(arm/'observations.json')
        call=next(v['payload'] for v in obs if v['payload']['kind']=='call');r=read(arm/'result.json');c=read(arm/'completion.json')
        model=core.lp_model(arm/'compact.lp');a=core.evidence.instance(ROOT,p)
        need(sha(arm/'compact.lp')==p['reference']['canonical_sha256']==sha(OUT/'qualification/reference'/role/'original.lp'),f'P{ordinal}_exact_cold_reference')
        rule.floor(p['lambda'],a['w'][1:],a['D'][1:],model['objective'],model['bounds'])
        oldscope.scope(call,c,launch['command'],launch['command'],sha(arm/'compact.lp'))
        vector=read(get('review/'+review+'/exact_binary64_matrix_witness.json'))
        vals={n:Fraction(*v) for n,v in vector['complete_column_values'].items()};need(set(vals)==set(model['bounds']),f'P{ordinal}_complete_vector')
        for n,(lo,hi) in model['bounds'].items():
            assert (not math.isfinite(lo) or vals[n]>=Fraction(lo)) and (not math.isfinite(hi) or vals[n]<=Fraction(hi))
            assert model['types'][n]=='C' or vals[n].denominator==1
        for terms,sense,rhs in model['rows']:
            lhs=sum((vals[n]*Fraction(v) for n,v in terms),Fraction(0));rhs=Fraction(rhs)
            assert lhs==rhs if sense=='=' else lhs<=rhs if sense=='<=' else lhs>=rhs
        terms,constant=model['objective'];F=sum((vals[n]*Fraction(v) for n,v in terms),Fraction(constant))
        need(any(Fraction(v['payload']['native_bound'])>F+Fraction(1,10**7) for v in obs if v['payload']['kind']=='bound'),f'P{ordinal}_real_numerical_contradiction')
        rule.returned_lifecycle(r,c,core.rows(arm/'phases.csv'),(arm/'native.log').read_text(),model)
        for name,change in [('return_error',{'returncode':1}),('interruption',{'stop_reason':'hard_stop'}),('cap_overrun',{'within_cap':False})]:
            reject(f'P{ordinal}_{name}',lambda change=change:oldscope.scope(call,dict(c,**change),launch['command'],launch['command'],call['model_sha256']))
        for name,change in [('wrong_model',{'model_sha256':'0'*64}),('local_scope',{'model_scope':'local'}),('not_original',{'full_original':0})]:
            reject(f'P{ordinal}_{name}',lambda change=change:oldscope.scope(dict(call,**change),c,launch['command'],launch['command'],call['model_sha256']))
        for name,index,value in [('negative_lambda',0,-.1),('nan_lambda',0,float('nan')),('negative_weight',1,[-1.]),('nonpositive_target',2,[0]),
                                 ('negative_objective_constant',3,([('G',1.)],-1.)),('negative_G_bound',4,dict(model['bounds'],G=(-1.,1.)))]:
            args=[p['lambda'],a['w'][1:],a['D'][1:],model['objective'],model['bounds']];args[index]=value
            reject(f'P{ordinal}_{name}',lambda args=args:rule.floor(*args))
        for field in ['native_mip_evidence_capture_complete','native_mip_problem_freed','native_mip_environment_closed','native_mip_lifecycle_valid']:
            reject(f'P{ordinal}_missing_{field}',lambda field=field:rule.returned_lifecycle(dict(r,**{field:False}),c,core.rows(arm/'phases.csv'),(arm/'native.log').read_text(),model))
        if ordinal==17:
            rule.functional(r,c,core.rows(arm/'phases.csv'),(arm/'native.log').read_text())
            need(not any(v['payload']['kind']=='returned' for v in obs),'P17_missing_return_not_fabricated')
            need(any(v['payload']['kind']=='failure' for v in obs) and not read(arm/'audit.json')['passed'],'P17_raw_failure_and_false_preserved')
            need(core.full_fleet(ROOT,p,r)['F']==0.,'P17_own_exact_zero_floor_certificate')
        else:need(core.full_fleet(ROOT,p,r)['F']>0.,'P15_own_positive_U_not_certified_by_floor')
        need(not (arm/'whole_arm_receipt.json').exists(),f'P{ordinal}_unknown_exact_clock')
    seed=get('qualification/cli01/raw/04_H100_S1_P-GRB');obs=read(seed/'observations.json');proof=read(seed/'computed_seed_scope.json')
    calls=[v['payload'] for v in obs if v['payload']['kind']=='call'];need(calls and all(c['settings']==rule.computed.expected(1) and c['native_preconditions']==0 for c in calls),'actual_R109_Seed1_false_raw_prerequisite')
    projected=rule.computed.projected_records(obs,proof,legacy_seed=True)
    need(all(v['payload']['settings']['Seed']==0 for v in projected if v['payload']['kind']=='call'),'legacy_Seed_metadata_projection_only')
    need(all(v['payload']['settings']['Seed']==1 for v in obs if v['payload']['kind']=='call'),'original_actual_Seed1_unchanged')
    reject('unsupported_Seed',lambda:rule.computed.expected(2))
    correction=read(get('review/mechanism_correction01.json'))
    need(correction['decision']=='ACCEPT_CORRECTION' and all(m['LP']==3 and m['terminal_MIP']==1 and m['actual_Optimize']==4 for m in correction['mechanisms']),'mechanism_correction_threeLP_oneMIP_each')
    for name,values in [('negative_time',(-1,200,[],900)),('reversed_time',(500,200,[],900)),('cap_overrun',(100,1000,[],900)),('nonfinite_time',(100,float('inf'),[],900))]:
        reject(name,lambda values=values:rule.clock_interval(*values))
    need(rule.clock_interval(100,250,[50],900)[0]<100 and rule.clock_interval(100,250,[50],900)[1]>200,'outward_record_clock_interval')
    reject('evidence_path_escape',lambda:rule.located(ROOT,'../outside.json'))
    a=dict(id='fixture',arm='M-B',U=0.,L=0.,gap=0.,certificate=True,certificate_qualified=True,numbers_qualified=True,
           complete_seconds=None,original_whole_clock_unknown=True,numerical_reader_recovery='regression',complete_seconds_interval=[100.,200.],cap_seconds=900)
    b=dict(a,arm='P-GRB',complete_seconds=150.)
    need(intervals.pair(a,b)['classification']=='UNEVALUABLE' and intervals.pair(a,b)['certified_time_ratio'] is None,'crossing_clock_rectangle_not_TIE_or_exact_speedup')
    need(manifest['old_P15_whole_receipt_absent'] and manifest['old_P17_whole_receipt_absent'],'original_missing_clocks_remain_missing')
    statement=next(line.strip() for line in (ROOT/'scripts/round110_reader.py').read_text().splitlines()
                   if "records['rejected_raw_native_chronology'].extend" in line)
    rows=core.collections.defaultdict(list)
    rejected=dict(kind='native_final_claim',native_bound_mathematically_qualified=False)
    exec(statement,dict(records=rows,label=dict(campaign='regression',number=1),ep=dict(rejected_raw_native_chronology=[rejected])))
    need(len(rows['rejected_raw_native_chronology'])==1 and rows['rejected_raw_native_chronology'][0]['native_bound_mathematically_qualified'] is False,
         'actual_reader_rejected_chronology_assembly_retains_false_without_duplicate_keyword')
    raw.update({p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'scripts/round110_evidence.py',ROOT/'scripts/round110_reader.py',ROOT/'scripts/round110_decisions.py']})
    audit=dict(passed=True,Optimize=0,native_environment=0,cases=cases,checks=len(cases),raw_bindings=raw,
        subjects=dict(actual_Seed1=True,actual_P15=True,actual_P17=True,missing_return=True,nonnegative_floor=True,unknown_clock=True,
            interval_thresholds=True,mechanism_correction01=True),all_old_tuple_sidecars_regression_only=True)
    write(d/'audit.json',audit);print(json.dumps(dict(passed=True,checks=len(cases),Optimize=0)),flush=True)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='run':run(sys.argv[2] if len(sys.argv)>2 else 'finite_regressions01')
    else:raise ValueError(sys.argv[1])
