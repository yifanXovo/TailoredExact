from round102_common import *
from round100_idle import ensure_idle
if __name__=='__main__':
    ensure_idle()
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert head=='6a505855dc539f0d35a983c13ab22258480b79de'
    edits=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines()
    write(OUT/'baseline.json',dict(head=head,base_branch='codex/round101-fleet-event-cuts',PR=163,
        remote_verified_head=head,AGENTS_found=False,other_active_local_tasks=False,
        protected_files={p:sha(ROOT/p) for p in edits},inherited_measured_source='8d6a497aa47d475436626b20bc573188d96e9e99',
        inherited_unmeasured_fault_fix='c811a06a5423faaa7b909500bb8c1491f6d28da3'))
    roles=read(ROOT/'results/unified_exact_round101/development_inputs.json')['roles']
    for p in roles:assert sha(ROOT/p['input_path'])==p['input_sha256']
    write(OUT/'development_inputs.json',dict(roles=roles))
    write(OUT/'protocol.json',dict(max_starts=72,max_outer_seconds=80000,
        stages=dict(structure=8000,prototype=14000,development=18000,confirmation_long=34000,reserve=6000),
        hypotheses=['S: positive-part service projection of qualified event ranks has a common-coordinate increment',
                    'J: integer single-car quantity/direction/visit DP adds useful support beyond linear budgets'],
        admission='qualified actual-model validity and reliable common-coordinate separation with objective or concrete integer-search relevance and cost qualification',
        stop='proved class redundancy or sufficiently supported finite-family weakness/cost/performance rejection; never merely a short zero-hit run',
        development_roles=['F2','R98-C2','R99-N2','F5'],
        planned_confirmation='freeze 2-3 previously unused roles, including nonzero V30/V50; retain all draws',
        long='only admitted worthwhile candidate: two common 3600-7200 second three-arm groups',
        native=dict(version='13.0.2',Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6),
        materiality=dict(time_absolute=30,time_relative=.10,UB_absolute=.001,UB_relative=.01,gap_absolute=.001,gap_relative=.10,severe_time_absolute=120,severe_time_relative=.25),
        production='original ENS-C24+1/VD-P/F0/AM.08; R101 OFF, M-B OFF; P unchanged/no Start; no instance/time/Work gates',
        diagnostics='historical matrices and vectors are retrospective only; native vectors must pass complete old LP residual before nonredundancy claim',
        costs='serial one-thread native solves; independent solves and failures billed; batch internal calls separately counted; engineering separate'))
    print('Round102 baseline/protocol saved; Optimize=0')
