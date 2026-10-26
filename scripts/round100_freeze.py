"""Freeze one observed candidate and the finite long/holdout protocols, no solve."""
import subprocess,time
from round100_common import *
from round100_campaign import helpers
from round100_idle import ensure_idle
def main():
    ensure_idle();q=read(OUT/'development01/identity.json')
    assert q['source_hashes']==bindings() and q['helpers']==helpers()
    assert sha(BUILD/'ExactEBRP.exe')==q['candidate_binary_sha256']
    costs=read(OUT/'development_results01/summary.json');assert costs['actual_starts']==18 and not costs['failed_started_processes']
    for a in q['launches']:
        if a['arm']!='P-GRB':assert read(OUT/'qualification'/f'dev_start_{a["number"]:02d}.json')['passed']
    write(OUT/'candidate_freeze.json',dict(selected_arm='M-B',mode='m-binary',selected_unix=time.time(),
        actual_source_phase=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        stacked_base='a11fbcdc9bbea4f5ee716c6e49df4e0fb4755dcd',source_bindings=bindings(),helpers=helpers(),
        binary_sha256=q['candidate_binary_sha256'],binary_path=q['prereg']['candidate_binary'],dll_sha256=q['dll_sha256'],
        common_parameters=q['prereg']['common'],selection_evidence_sha256=sha(OUT/'development_results01/runs.csv'),
        costs_at_selection=costs,ENS_default_changed=False,algorithm_not_revised_after_selection=True,
        representation=dict(AB=True,m='B',pd='C',ENS_Q=False,extra_direction_link=False,theta=False,outer='original full ENS',
            startup='original 24+1 plus closure',VD_P=True,F0='inherited',AM=.08,depth_width='inherited',Start='same-run complete original witness',
            LP_G=False,R96_order=False,R97_feedback=False,new_branching=False,new_native_parameter_grid=False),
        decision='Plan B, certification observation only: ENS-Q improves C2 ENS UB but is materially worse than P in UB/gap; M-B materially improves P on C2. Both quantity-continuous representations lose ENS F2/C1 proof speed. A/B is material for tested C2 budget benefit; F2/C1 incremental times are not material. Existing F5 protection loss remains an explicit challenge, no promotion.'))
    c2=dict(next(p for p in read(OUT/'development_inputs.json')['roles'] if p['id']=='R98-C2'))
    f5=dict(read(ROOT/'results/unified_exact_round99/long_protocol01.json')['roles'][0])
    n2=dict(next(p for p in read(ROOT/'results/unified_exact_round99/confirmation_protocol01.json')['roles'] if p['id']=='N2'))
    n2['id']='R99-N2'
    for p,cap,order in [(c2,7200,['P-GRB','ENS-C','M-B']),(f5,7200,['ENS-C','M-B','P-GRB']),(n2,3600,['M-B','P-GRB','ENS-C'])]:
        assert sha(ROOT/p['input_path'])==p['input_sha256'];p['cap_seconds']=cap;p['method_order']=order
        p.pop('historical_initial_witness',None);p.pop('historical_initial_witness_sha256',None)
        p.pop('diagnostic_cutoff',None);p.pop('diagnostic_gamma_L',None);p.pop('diagnostic_gamma_U',None)
    assert c2['Q_vector']==[20,25,30] and f5['Q_vector']==[30]*4 and n2['Q_vector']==[16,22,28]
    write(OUT/'long_protocol.json',dict(roles=[c2,f5,n2],candidate_freeze_sha256=sha(OUT/'candidate_freeze.json'),
        maximum_formal_seconds=54000,planned_formal_starts=9,optimizer_calls=0,
        scope='observed-role extension and protection, not new independent confirmation',
        N2_extension='Only before any N2 start, if completed prior runs release enough of total80000 to fund all three7200 caps and5400 holdout; record common revision once.',
        fresh_reference_batches=[dict(children=2,child_cap=60),dict(children=1,child_cap=60)],
        all_arms_self_paid=True,no_cross_arm_start=True,no_algorithm_changes=True))
    write(OUT/'certification_CF_protocol01.json',dict(roles=[c2,f5],phase='certification extension',
        reference_billing='one_finite_batch',candidate_freeze_sha256=sha(OUT/'candidate_freeze.json'),optimizer_calls=0))
    import round96_prepare as generation
    write(OUT/'holdout_generation_recipe.json',dict(version='round100-minimal-integrality-holdout-v1',
        role=dict(id='H100',V=20,M=2,Q_vector=[13,21],geometry='anisotropic_cloud',inventory='shortage',T_seconds=5100,cap_seconds=1800),
        method_order=['P-GRB','M-B','ENS-C'],seed='SHA256(version|id|field), first8 bytes /2^64',
        landscape_source_sha256=sha(generation.__file__),writer_sha256=sha(generation.citi.__file__),
        scope='new input bytes unused in selection; inherited geometric family, one role only; not broad generalization',
        rationale='R98 and R99 confirmation inputs are already observed. Freeze a single fresh V20 shortage role with heterogeneous fleet; no pilot, reseed, redraw or difficulty adjustment.',
        retain_all_outcomes=True,no_optimizer_in_generation=True,candidate_freeze_sha256=sha(OUT/'candidate_freeze.json')))
    print('M-B frozen; C2/F5/N2 long roles and one fresh nonzero V20 recipe frozen before long outcomes; Optimize=0')
if __name__=='__main__':main()
