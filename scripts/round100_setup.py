"""Exclusive zero-solver baseline and finite protocol setup."""
import hashlib, json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/unified_exact_round100'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p, v):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8') as f: json.dump(v, f, indent=2, ensure_ascii=False); f.write('\n')
def main():
    OUT.mkdir(exist_ok=False)
    base = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert base == 'a11fbcdc9bbea4f5ee716c6e49df4e0fb4755dcd'
    tracked = subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines()
    write(OUT/'baseline.json', dict(base_commit=base,base_branch='codex/round99-discrete-structure-native-search',
        stacked_pr=161,branch='codex/round100-minimal-integrality-certification',
        user_edit_sha256={p:sha(ROOT/p) for p in tracked},AGENTS_found=False,active_solver_processes=0,
        historical_exact_ENS_Q=False,historical_search='R98/R99 writers, manifests, math/results; earlier R66 replacements are not identical ENS rows'))
    (OUT/'preexisting_untracked_paths.txt').write_bytes(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT))
    roles=json.loads((ROOT/'results/unified_exact_round99/development_inputs.json').read_text())['roles']
    orders=[['ENS-C','ENS-Q','M-B','P-GRB'],['M-B','P-GRB','ENS-Q','ENS-C'],['P-GRB','ENS-Q','ENS-C','M-B']]
    for p, order in zip(roles,orders):
        assert sha(ROOT/p['input_path'])==p['input_sha256'];p['method_order']=order
        p.pop('reference',None)
    write(OUT/'development_inputs.json',dict(roles=roles,phase='minimal quantity ablation',reference_billing='one_finite_batch',optimizer_calls=0))
    write(OUT/'protocol.json',dict(max_billed_starts=72,max_outer_seconds=80000,
        materiality=dict(time_absolute=30,time_relative=.10,UB_absolute=.001,UB_relative=.01,gap_absolute=.001,gap_relative=.10,
            severe_time_absolute=120,severe_time_relative=.25),
        budgets=dict(qualification=3000,development=13200,long=54000,holdout=5400,reserve=4400),
        selection='Before long/holdout: prefer ENS-Q if it preserves F2/C1 certificate protection and C2 material P benefit; select M-B if A/B matters for C2 and total evidence favors it; otherwise M-B only as certification observation, no promotion.',
        long_roles=[dict(id='R98-C2',cap=7200),dict(id='F5',cap=7200),dict(id='R99-N2',cap=3600)],
        long_order='C2, F5, then N2; all three arms own full cap; N2 common extension only preregistered before any N2 start within total allowance',
        holdout='One V20/V30 nonzero role after candidate freeze, generated once if no eligible unused dataset; skip only if long protection sufficiently rejects candidate.',
        no_tuning=True,no_cross_arm_start=True,no_implicit_extra_solver=True,performance_serial=True))
    print('baseline/input/protocol written, Optimize=0')
if __name__=='__main__':main()
