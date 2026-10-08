"""Exclusive prospective recipe freeze and one draw per new role. Zero Optimize."""
from round108_common import *
import copy
import round96_prepare as generation

VERSION='round108-uniform-candidate-confirmation-v1'
ROLES=[
 dict(id='F2',V=20,M=2,Q_vector=[30,30],T_seconds=3600,cap_seconds=1200,method_order=['P-GRB','ENS-C','M-B'],
      input_path='reference/round86_unadapted_confirmation/F2.txt',input_sha256='ebdf99e77dc9dcc57946970fa6d7e1cdf2defdcd277562a454d4889c716b645e',role_identity='known_development_bridge'),
 dict(id='C2',V=30,M=3,Q_vector=[20,25,30],T_seconds=7200,cap_seconds=1800,method_order=['ENS-C','M-B','P-GRB'],
      input_path='reference/round98_confirmation/C2.txt',input_sha256='07d0964c87b534254e6bf2957911859a6a2bd73e377211728b7e65f44294fc76',role_identity='known_development_bridge'),
 dict(id='S12',V=12,M=2,Q_vector=[8,12],T_seconds=3600,cap_seconds=900,method_order=['M-B','P-GRB','ENS-C'],
      input_path='reference/round106_confirmation/S12.txt',input_sha256='475763e70a2dc3b9d28a88028378e76946cbebf33aa7b7e5b033e018dd13369f',role_identity='sealed_unused_for_selection'),
 dict(id='B24',V=24,M=2,Q_vector=[16,24],T_seconds=5400,cap_seconds=1800,method_order=['P-GRB','ENS-C','M-B'],
      geometry='anisotropic_cloud',inventory='balanced',role_identity='new_draw_unused_for_selection'),
 dict(id='L48',V=48,M=4,Q_vector=[30]*4,T_seconds=18000,cap_seconds=1800,method_order=['ENS-C','M-B','P-GRB'],
      geometry='radial_spokes',inventory='shortage',role_identity='new_draw_unused_for_selection'),
 dict(id='F5',V=50,M=4,Q_vector=[30]*4,T_seconds=7200,cap_seconds=5400,method_order=['M-B','P-GRB','ENS-C'],
      input_path='reference/round86_unadapted_confirmation/F5.txt',input_sha256='5145b134f52dc573900b0b271325639fb04dc5eed37bf996f6b984f74efacc8a',role_identity='known_pressure'),
 dict(id='N36',V=36,M=3,Q_vector=[24,30,36],T_seconds=7200,cap_seconds=5400,method_order=['P-GRB','ENS-C','M-B'],
      input_path='reference/round106_confirmation/N36.txt',input_sha256='52d7e43a1cc3717cfe7183b302212c7ef0a4e81f3e62642c4fe8f83c546e6fea',role_identity='sealed_unused_for_selection'),
]
COMMON=dict(threads=1,mip_threads=1,gurobi_seed=0,gurobi_presolve=-1,gurobi_version='13.0.2',
    affinity_mask=4,native_limit_offset_seconds=6,hard_stop_offset_seconds=2,shutdown_margin_seconds=30,
    requested_mip_gap=0,requested_mip_gap_abs=0,FeasibilityTol=1e-6,OptimalityTol=1e-6,IntFeasTol=1e-5)

def recipe():
    return dict(version=VERSION,roles=ROLES,source_SHA=sha(__file__),
        landscape_SHA=sha(generation.__file__),writer_SHA=sha(generation.citi.__file__),
        draw='SHA256(VERSION|id|field), first eight bytes big endian divided by 2^64',
        writer='R106 heterogeneous Q header; original instance_text, UTF-8 exact LF',
        pickup_seconds=60,drop_seconds=60,lambda_value=.15,Optimize_calls=0,
        retain_every_legal_outcome=True,no_reseed_replace_prescreen_or_adjustment=True,
        generation_reads_performance=False,
        balanced_zero_objective_retained=True,shortage_excludes_zero_only_not_difficulty=True)

def freeze():
    OUT.mkdir(exist_ok=False)
    write(OUT/'generation_recipe.json',recipe())
    write(OUT/'candidate_contract_freeze.json',dict(candidate='R100 frozen M-B',
        original_freeze_commit='b5d6d83bb8fc74682de6f1f6862c2e687712f4cf',
        original_freeze_path='results/unified_exact_round100/candidate_freeze.json',
        original_freeze_SHA=sha(ROOT/'results/unified_exact_round100/candidate_freeze.json'),
        current_base='b5db3f038f64215766a54498d8acc82e384de733',source_bindings=bindings(),
        input_preset='research-round83-vds-equal-net-exchange',
        appended_argv=['--round98-state-service','m-binary'],
        effective_identity='research-round99-ensc-discrete-structure-m-binary',
        round100_continuous_quantities=False,default_ENS_changed=False,
        no_new_mechanism=True,no_instance_dispatch=True,Optimize_calls=0))
    print('recipe/candidate contract frozen; Optimize=0',flush=True)

def generate():
    frozen=read(OUT/'generation_recipe.json');current=recipe()
    if frozen!=current:
        repair=read(OUT/'engineering/generation01_failure/repair.json')
        assert sha(__file__)==repair['repaired_source_SHA']
        assert sha(OUT/'engineering/generation01_failure/round108_prepare.py')==frozen['source_SHA']==repair['original_source_SHA']
        assert {k:v for k,v in frozen.items() if k!='source_SHA'}=={k:v for k,v in current.items() if k!='source_SHA'}
    data=ROOT/'reference/round108_confirmation'
    if data.exists():
        assert not any(data.iterdir()),'exclusive generation never overwrites an existing draw'
    else:
        data.mkdir()
    roles=copy.deepcopy(ROLES);generation.VERSION=VERSION
    for r in roles:
        r.update(pickup_seconds=60,drop_seconds=60,**{'lambda':.15})
        if r['id'] in ('B24','L48'):
            obj=generation.landscape(r);p=data/(r['id']+'.txt')
            lines=generation.citi.instance_text(obj,r['M'],r['Q_vector'][0]).splitlines()
            lines[0]=f'{r["V"]} {r["M"]} {r["Q_vector"]}'
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines)+'\n')
            # Preserve bytes before validation; a syntax failure never permits a redraw.
            write(data/(r['id']+'_landscape.json'),obj)
            parsed=generation.citi.parse_instance_mirror(p)
            assert parsed['Q']==r['Q_vector'] and len(parsed['points'])==r['V']+1
            assert len(set(map(tuple,parsed['points'])))==r['V']+1
            assert all(0<=b<=c and 0<d<=c for b,d,c in zip(obj['initial'],obj['target'],obj['capacities']))
            assert all(w>0 for w in obj['weights'])
            r.update(input_path=p.relative_to(ROOT).as_posix(),input_sha256=sha(p),scenario_id=VERSION+'-'+r['id'],
                total_initial=sum(obj['initial']),total_target=sum(obj['target']),
                zero_excluded_by_stock_shortage=sum(obj['initial'])<sum(obj['target']),
                minimum_weight=min(obj['weights']),maximum_weight=max(obj['weights']),
                derived_landscape_path=(data/(r['id']+'_landscape.json')).relative_to(ROOT).as_posix(),
                derived_landscape_SHA=sha(data/(r['id']+'_landscape.json')))
            assert r['id']!='L48' or r['zero_excluded_by_stock_shortage']
        else:
            assert sha(ROOT/r['input_path'])==r['input_sha256']
            parsed=generation.citi.parse_instance_mirror(ROOT/r['input_path'])
            assert parsed['Q']==r['Q_vector'] and len(parsed['initial'])==r['V']+1
    write(OUT/'input_manifest.json',dict(roles=roles,recipe_SHA=sha(OUT/'generation_recipe.json'),Optimize_calls=0,
        sealed_four=['S12','B24','L48','N36'],qualification_inputs_excluded_from_sealed_four=True))
    common=dict(common_parameters=COMMON,nominal_seconds=54900,formal_arms=21,max_conservative_starts=48,
        max_outer_solver_seconds=80000,qualification_per_arm_cap_max=120,qualification_recommended_seconds_max=4000,
        representation_contract='R100 frozen M-B; no ENS-Q flag; original full ENS; P cold compact',
        no_cross_arm_UB_Start_route_cut_cache=True,performance_serial=True,
        no_grid_multiseed_extension_or_third_draw=True,process_shutdown_margin_seconds=30,
        materiality=dict(a_U='max(0.001,0.01*abs(U_P))',a_gap='max(0.001,0.10*abs(gap_P))',a_t='max(30,0.10*t_P)'),
        severe=dict(P_only_certificate=True,both_certified='t_MB>=2*t_P and t_MB-t_P>=120',
            both_uncertified='UB worse by >=max(0.001,0.05*abs(U_P)) AND gap worse by >=max(0.005,0.25*abs(gap_P))'),
        certificate_priority=True,missing_finite_UL_both_uncertified='UNEVALUABLE',
        relative_gap='(U-L)/abs(U) only qualified finite U/L and abs(U)>original zero tolerance; else null',
        signed_gap_not_clipped=True,comparison_tolerance=1e-7,
        percentage_bridge_path='reference gap positive and > original closure tolerance; otherwise certificate branches only',
        stages=['SELECT_MB_FOR_BROAD_EVALUATION','NO_NEW_UNIFORM_CANDIDATE_SELECTED','STOP_MB_REOPENING_AT_BRIDGE','BLOCKED'],
        SELECT_requires=dict(all_21_same_final_PE=True,bridge_pass=True,all_seven_evaluable=True,
            unresolved_certificate_qualifications=0,severe_regressions_vs_P=0,F5_not_LOSS_and_evaluable=True,
            all_four_unseen=True,unseen_min_WIN=2,unseen_max_LOSS=1),
        cancellation='complete started three-arm group; cancel wholly unstarted groups only when SELECT mathematically unreachable; any cancellation prohibits SELECT',
        input_manifest_SHA=sha(OUT/'input_manifest.json'),candidate_contract_SHA=sha(OUT/'candidate_contract_freeze.json'))
    write(OUT/'development_protocol.json',dict(common,roles=roles[:2],phase='six-arm current bridge',stage_nominal_seconds=9000,
        C2_gate='MB certified and P not; OR both certified with reduction>=30s AND>=10%; OR both uncertified with U_MB<=0.99*U_P AND gap_MB<=0.80*gap_P',
        F2_gate='MB certified; OR both uncertified with U_MB<=1.01*U_P AND gap_MB<=1.05*gap_P; also no severe P regression',
        all_six_required_before_gate=True,negative_bridge_cancels_all_unstarted_confirmation=True))
    write(OUT/'confirmation_protocol.json',dict(common,roles=roles[2:],phase='conditional fifteen-arm frozen confirmation',
        stage_nominal_seconds=45900,admission='independently verified complete bridge pass; same candidate/PE/inputs/order'))
    print(json.dumps(dict(generated_once=['B24','L48'],formal_arms=21,nominal_seconds=54900,Optimize_calls=0)),flush=True)

if __name__=='__main__':
    {'freeze':freeze,'generate':generate}[sys.argv[1]]()
