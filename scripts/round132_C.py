"""Finite same-build inclusive-root expression workflows; never used for D."""
from round132_common import *
from round132_build import PE,EXPORT
from round132_campaign import api,execute as D_execute
from round127_data import TRAIN
from round132_qualify import export,compare
from compare_round112_startup import reconstruct as startup
import round108_reader as core
import copy,collections,inspect

# Preserve the established producer/verifier exactly while giving C its own
# truthful recovery labels. This changes no command, model, clock or algorithm.
_execute_source=inspect.getsource(D_execute).replace("line='D'","line='C'").replace(
    'Round132 D active.','Round132 C active.').replace(
    'Own frozen E3 only. C/E never supply information to D.',
    'Own separately qualified research PE only. D uses the immutable original E3; never transfer C/E information.')
_execute_namespace=dict(D_execute.__globals__)
exec(compile(_execute_source,__file__+'::C_recovery_labels','exec'),_execute_namespace)
execute=_execute_namespace['execute']

def prepare_group(name,p,expressions,seed,original=False):
    make,_,_=api();make(name,'E3',p,['S2R']*len(expressions),seed)
    path=OUT/name/'identity.json';i=read(path);actual=E3 if original else PE
    i.update(candidate_binary_sha256=sha(actual),measured_source_commit=SOURCE,
             research_build_binding=sha(OUT/'research_build.json') if not original else None)
    i['prereg']['candidate_binary']=str(actual);i['prereg']['candidate_binary_sha256']=sha(actual)
    for l,expression in zip(i['launches'],expressions):
        l['command'][0]=str(actual)
        if not original:l['command']+=['--round132-expression',expression]
        l.update(expression=expression,comparison_method={'off':'S2R','geom':'S2R-GEOM','sp':'S2R-SP'}[expression],
            research_PE=not original,root_semantics='legal inclusive root',binary_layer='E3' if original else 'R132-research')
    write(path,i);return i

def prepare_native():
    p=copy.deepcopy(TRAIN[0]);p.update(cap_seconds=90,pickup_seconds=60,drop_seconds=60,**{'lambda':.15},source='qualification',inventory='unspecified')
    plans=[]
    for name,expression,original in [('E3','off',True),('off','off',False),('geom','geom',False),('sp','sp',False)]:
        n='qualification/C_native_'+name
        if not (OUT/n/'identity.json').exists():prepare_group(n,p,[expression],0,original)
        plans.append(dict(name=n,expression=expression,original=original))
    write(OUT/'qualification/C_native_plan.json',dict(plans=plans,complete_caps=360,
        questions='old/new default-off own H and matrix bridge; actual independent physical Start in every expression; one root LP+MIP chain',
        formal=False))

def native():
    plan=read(OUT/'qualification/C_native_plan.json');facts=[];fleets=[];base_model=None
    for p in plan['plans']:
        name=p['name'];label=name.replace('/','_')+'_01'
        if not (OUT/name/'reconstructed.json').exists():
            assert metered(label,'qualification',[PYTHON,ROOT/'scripts/round132_C.py','group',name,label],timeout=900)==0
        camp=OUT/name;i=read(camp/'identity.json');arms=read(camp/'reconstructed.json')['arms']
        assert len(arms)==1 and arms[0]['formal_protocol_qualified']
        l=i['launches'][0];d=Path(l['destination']);h=startup(ROOT,l['panel'],d);assert h['complete'];fleets.append(h)
        ledger=core.rows(d/'external/paper_optimize_ledger.csv')
        assert [x['solve_kind'] for x in ledger]==['LP','MIP'] and all(x['leaf_id']=='L0' for x in ledger)
        models=list((d/'external').rglob('*.lp'));unique={sha(m):m for m in models}
        assert unique
        # Actual root matrix is located via the native request ledger, retaining
        # its cutoff and own H rather than a filename-derived synthetic scope.
        import round114_audit as audit
        with inherited_extension():j=audit.journal(ROOT,l,d,read(d/'observations.json'))
        call=next(c for c in j['calls'].values() if not c['full_original'])
        m=core.lp_model(core.portable(ROOT,call['model_path']))
        if p['original']:base_model=m
        elif p['expression']=='off':assert m==base_model
        else:compare(base_model,m,p['expression'])
        receipts=[read(q) for q in (d/'external/native_logs').glob('*.round68.start.json')]
        assert sum(bool(q['submitted']) for q in receipts)==1
        facts.append(dict(name=name,expression=p['expression'],qualified=True,certificate=arms[0]['certificate'],
            root_LP_then_MIP=True,own_Start_submitted=True,matrix_SHA=sha(core.portable(ROOT,call['model_path'])),
            W_present='W_SP' in m['types'],H_objective_zero=True))
    assert all(h['fleet']==fleets[0]['fleet'] and h['semantic_traces']==fleets[0]['semantic_traces'] for h in fleets)
    write(OUT/'qualification/C_native_qualification.json',dict(passed=True,records=facts,
        own_H_fleets_and_actions_equal=True,default_off_E3_behavioral_and_matrix_bridge=True,
        same_physical_Start_mapped_to_remaining_actual_columns=True,no_formal_role_screened=True))
    print('C_NATIVE_BEHAVIORAL_AND_START_QUALIFICATION_PASS')

def inherited_extension():
    from round130_evidence import extension
    return extension()

def formal_prepare():
    assert read(OUT/'qualification/C_matrix_qualification.json')['passed']
    assert read(OUT/'qualification/C_native_qualification.json')['passed']
    roles=[]
    for rnd,id,cap in [(131,'SC-C15-B',600),(131,'SC-B20-S',1200),(130,'UC-C20-U',1200),(131,'PB-C35-U',2400)]:
        p=copy.deepcopy(next(q for q in read(ROOT/f'results/unified_exact_round{rnd}/input_manifest.json')['roles'] if q['id']==id))
        assert p['cap_seconds']==cap;assert sha(ROOT/p['input_path'])==p['input_sha256']
        p.update(evidence_layer='C',panel_kind='known_diagnostic_expression_role');roles.append(p)
    groups=[];plans=[]
    for p in roles:
        for seed in [0,1]:
            expressions=['off','geom','sp']
            if (len(groups)//2+seed)%2:expressions.reverse()
            name=f'campaign/C_group{len(groups)+1:02d}'
            i=prepare_group(name,p,expressions,seed);plans.append(i)
            groups.append(dict(number=len(groups)+1,name=name,role=p,seed=seed,expressions=expressions))
    assert sum(3*g['role']['cap_seconds'] for g in groups)==32400
    write(OUT/'C_experiment_plan.json',dict(groups=groups,formal_arms=24,cap_sum=32400,
        pairs=[['S2R-GEOM','S2R'],['S2R-SP','S2R']],
        comparison_direction='candidate / same-build S2R baseline',
        denominators='each candidate: 4 known problems x 2 Seeds = 8 repeated comparisons; 8 shared baseline arms; 16 typed comparisons are not independent trials',
        same_research_PE_SHA=sha(PE),same_DLL_SHA=DLL_SHA,C3_preselected=False,
        native_fields_not_exposed='unknown; never inferred from terminal values',canonical_continuous_LP_paid_in_own_workflow=True))
    write(OUT/'C_argv_freeze.json',dict(plans=plans))
    write(OUT/'C_execution_binding.json',dict(plan_SHA=sha(OUT/'C_experiment_plan.json'),argv_SHA=sha(OUT/'C_argv_freeze.json'),
        research_build_SHA=sha(OUT/'research_build.json'),groups={g['name']:sha(OUT/g['name']/'identity.json') for g in groups},
        PE_SHA=sha(PE),DLL_SHA=sha(DLL),runner_SHA=sha(__file__)))

def run():
    gate=read(OUT/'review/C_admission.json');assert gate['decision']=='ACCEPT' and gate['C_execution_binding_SHA']==sha(OUT/'C_execution_binding.json')
    b=read(OUT/'C_execution_binding.json');assert sha(PE)==b['PE_SHA'] and sha(DLL)==b['DLL_SHA'] and sha(__file__)==b['runner_SHA']
    for g in read(OUT/'C_experiment_plan.json')['groups']:
        name=g['name'];assert sha(OUT/name/'identity.json')==b['groups'][name]
        if (OUT/name/'reconstructed.json').exists():continue
        label=f'formal_C{g["number"]:02d}_01';assert not (OUT/'fees'/label).exists()
        assert metered(label,'C',[PYTHON,ROOT/'scripts/round132_C.py','group',name,label],timeout=3*g['role']['cap_seconds']+1800)==0
    print('ALL_24_C_ARMS_SEALED')
if __name__=='__main__':
    a=sys.argv[1]
    if a=='group':execute(sys.argv[2],sys.argv[3])
    else:{'prepare-native':prepare_native,'native':native,'prepare':formal_prepare,'run':run}[a]()
