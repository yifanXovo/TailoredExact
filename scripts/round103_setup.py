from round103_common import *
if __name__=='__main__':
    from round100_idle import ensure_idle
    ensure_idle()
    base='0b5640f0de5a29abf6545962dd776a2fab198f90'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==base
    prior=read(ROOT/'results/unified_exact_round102/production_freeze.json')
    assert sha(ROOT/prior['binary'])==prior['binary_sha256']=='f1c071135b6dd7cc84d92a71efec17aec33187747ad1829d53a1058576871c1d'
    assert all(sha(ROOT/p)==v for p,v in prior['source_bindings'].items())
    edits=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines()
    write(OUT/'baseline.json',dict(head=base,branch='codex/round103-resource-hull-separation',base_branch='codex/round102-service-space-resource-cuts',PR=164,
        remote_verified_head=base,AGENTS_found=False,active_solvers=False,protected_files={p:sha(ROOT/p) for p in edits},
        inherited_measured_source='2b65d483ecacd6084782922cff8c8252be9d3a63',inherited_PE=prior['binary_sha256']))
    write(OUT/'development_inputs.json',read(ROOT/'results/unified_exact_round102/development_inputs.json'))
    write(OUT/'protocol.json',dict(max_starts=72,max_outer_seconds=80000,
        stages=dict(member_capacity=12000,substantive_branch=12000,development_protection=18000,confirmation_long=32000,reserve=6000),
        protected_default='ENS-C',not_promoted=['M-B','R101','R102-J'],main_benchmark='P-GRB',
        initial_points=['F2 raw LP','F2 first full native root','R98-C2 raw LP','R98-C2 first full native root','F5 raw LP','F5 first full native root','R99-N2 raw LP','R99-N2 first full native root'],
        domain='R102 actual conservative floating resource predicate; identical support and plan verification',
        scale='physical per-coordinate operation caps, z width one; zero-width validated then removed',
        diagnosis='per model 600s; explicitly preregister exceptions; UNKNOWN on unfinished precision/pricing',
        candidate='one evidence-selected substantive branch; no manually added third direction or multiplier grid',
        native=dict(version='13.0.2',Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6),
        materiality=dict(time_absolute=30,time_relative=.10,UB_absolute=.001,UB_relative=.01,gap_absolute=.001,gap_relative=.10,severe_time_absolute=120,severe_time_relative=.25),
        confirmation='two unused-for-R103-selection roles, at least one nonzero V30/V50; freeze before inspection; no redraw',
        long='worthwhile candidate only: two common3600-7200s full groups, known tail and isolated medium-large confirmation',
        costs='serial performance; each auxiliary LP Optimize and DP separately counted; nested outer cost never double counted'))
    print('Round103 baseline/source/PE/protected files verified; protocol saved; Optimize=0')
