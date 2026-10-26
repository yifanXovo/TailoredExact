from round101_common import *
if __name__=='__main__':
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='541c032f04b35f90d750c83e4938e02df3ebf008'
    paths=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines()
    preexisting={p:sha(ROOT/p) for p in paths if p.startswith('results/') and not p.startswith('results/unified_exact_round101/')}
    write(OUT/'baseline.json',dict(base='541c032f04b35f90d750c83e4938e02df3ebf008',source_stage='b5d6d83bb8fc74682de6f1f6862c2e687712f4cf',
        stacked_pr=162,branch='codex/round101-fleet-event-cuts',user_edit_sha256=preexisting,active_solver_processes=0,AGENTS_found=False))
    sources=[ROOT/'results/unified_exact_round100/development_inputs.json',ROOT/'results/unified_exact_round100/certification_CF_protocol01.json',ROOT/'results/unified_exact_round100/certification_N2_protocol01.json']
    roles={p['id']:p for file in sources for p in read(file)['roles']}
    ids=['F2','R98-C2','R99-N2','F5'];data=[]
    for id in ids:
        p=dict(roles[id]);p.pop('reference',None);p['method_order']=[]
        assert sha(ROOT/p['input_path'])==p['input_sha256'];data.append(p)
    write(OUT/'development_inputs.json',dict(roles=data,phase='fleet-event qualification and development'))
    write(OUT/'protocol.json',dict(max_billed_starts=72,max_outer_seconds=80000,
        materiality=dict(time_absolute=30,time_relative=.10,UB_absolute=.001,UB_relative=.01,gap_absolute=.001,gap_relative=.10,severe_time_absolute=120,severe_time_relative=.25),
        budgets=dict(qualification=6000,isolation=14000,development=20000,confirmation_and_long=34000,reserve=6000),
        production='original ENS-C; no internal time/Work/restarts; original P no Start; dynamic user cuts only',
        hypotheses=['fleet subset/resource rank beyond pair cliques','scalable eligibility/cardinality rank for long supports'],
        planned_confirmation='After freeze, 2-3 unused design roles including nonzero V30/V50. No rejection/redraw.',
        continuation='Worthwhile qualified candidate: two groups of common 3600-7200 P/ENS/candidate long comparisons, one existing tail and one design-isolated medium/large.',
        stop='Only correctness failure or sufficiently supported finite-family negative result may preclude long-window admission; initial short negative does not suffice.',
        native=dict(version='13.0.2',Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6),
        no_cross_arm_answers=True,serial_single_thread=True))
    print('baseline, four role inputs and protocol saved; Optimize=0')
