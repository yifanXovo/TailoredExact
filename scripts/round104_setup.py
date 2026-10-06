from round104_common import *
import csv
if __name__=='__main__':
    from round100_idle import ensure_idle
    ensure_idle()
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert head=='7b60d3c1b07429ee96dbf371b4796e635499cb80'
    prior=read(PRIOR/'production_freeze.json')
    assert all(sha(ROOT/p)==v for p,v in prior['source_bindings'].items())
    assert sha(ROOT/'build/research/round103-hull-v1/ExactEBRP.exe')==prior['PE_sha256']=='836b2ee3f7e373c8be0a1f2bdf5b6e06ac67a95ea7ef65374972288acdc862ea'
    edits=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines()
    tracked=subprocess.check_output(['git','ls-files','*AGENTS.md'],cwd=ROOT,text=True).strip()
    assert not tracked
    # Parse every final report in full; large trajectories are read without copying.
    reports={}
    for p in (PRIOR/'reports_final01').iterdir():
        if p.suffix=='.csv':
            with p.open(encoding='utf-8-sig',newline='') as f:
                records=list(csv.DictReader(f))
            reports[p.name]=dict(sha256=sha(p),rows=len(records),fields=list(records[0]) if records else [])
        elif p.is_file(): reports[p.name]=dict(sha256=sha(p),bytes=p.stat().st_size)
    write(OUT/'baseline.json',dict(head=head,base_branch='codex/round103-resource-hull-separation',PR=165,
        remote_verified_head=head,branch='codex/round104-objective-certificate-compression',
        AGENTS_found=False,active_solvers=False,protected_files={p:sha(ROOT/p) for p in edits},
        inherited_measured_source=prior['source_head'],inherited_PE=prior['PE_sha256'],
        DLL=prior['DLL_sha256'],reports=reports))
    write(OUT/'protocol.json',dict(max_starts=72,max_outer_seconds=80000,protected_default='ENS-C',
        principal_benchmark='P-GRB',not_promoted=['M-B','R101','R102-J','R103-H'],
        diagnostic_roles=['F2','R98-C2','F5'],representation=['ALL','ACTIVE','GROUPED','FLEET'],
        history_reuse='SHA-bound finite pools for expression diagnosis only; no free replay algorithm performance',
        native_observation='original ENS; first and last observable root, available positive nodes; full matrix residuals',
        numerical_qualification='Gurobi primal/dual numerical optimum; no rational optimality claim',
        production_limits='only whole-algorithm deadline; no component time/Work limits or stall gates',
        native=dict(version='13.0.2',Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6),
        materiality=dict(time_absolute=30,time_relative=.10,UB_absolute=.001,UB_relative=.01,gap_absolute=.001,gap_relative=.10,severe_time_absolute=120,severe_time_relative=.25),
        expansion='independent mathematical/information review first; worthwhile candidate needs complete self-paid P/ENS/candidate/SHADOW and frozen long confirmation',
        stop='finite pool objective preserved but insufficient medium-large native information or disproportionate generation cost permits explicit structural stop; one finite control if causality unresolved'))
    print('R104 baseline/PE/protected files/full report parse verified; Optimize=0')
