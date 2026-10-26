"""Freeze untouched old input roles and sequential conditional full stages.
Reads input manifests/bytes, never historical outcomes or LPs; zero Optimize.
"""
from round102_common import *
from round100_idle import ensure_idle

if __name__=='__main__':
    ensure_idle();production=read(OUT/'production_freeze.json')
    assert production['source_bindings']==bindings()
    roles=[]
    for old,tag,cap,order in [
        ('round98','C3',1800,['P-GRB','ENS-C','J-SUBMIT']),
        ('round99','N3',3600,['J-SUBMIT','P-GRB','ENS-C'])]:
        manifest=ROOT/f'results/unified_exact_{old}/confirmation_protocol01.json'
        p=dict(next(p for p in read(manifest)['roles'] if p['id']==tag))
        assert p['V']==50 and p['M']==4 and p['zero_excluded_by_stock_shortage']
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        p.update(id=f'R{old[5:]}-{tag}',cap_seconds=cap,method_order=order,
            design_isolated_in_R102=True,historical_role_not_globally_unseen=True,
            selection='The two retained larger roles C3/N3 in the prereferenced old input families; no outcomes/LPs inspected or reseed.',
            metadata_source=manifest.relative_to(ROOT).as_posix(),metadata_sha256=sha(manifest),
            question='Does the unchanged uniform original-service component generalize across new geography/heterogeneous capacities while preserving the P benchmark and certificate capability?')
        roles.append(p)
    f5=dict(next(p for p in read(OUT/'development_inputs.json')['roles'] if p['id']=='F5'))
    f5.update(cap_seconds=3600,method_order=['ENS-C','J-SUBMIT','P-GRB'],design_isolated_in_R102=False,
        question='Does the uniform component preserve existing V50 tail quality/certification and proof cost over a3600s window after worthwhile frozen confirmation?')
    stages=[]
    for name,p,phase,condition in [
        ('confirmation01',roles[0],'service confirmation','Qualified full-development/isolation increment, complete actual-row validation and independent mathematical admission'),
        ('confirmation_long01',roles[1],'service long','After completing C3, unchanged candidate remains valid; this second untouched role resolves generalization and one required design-isolated long window'),
        ('long_tail01',f5,'service long','Only if completed two-role frozen confirmation leaves continuing value; otherwise explicitly cancel this existing-tail group with evidence')]:
        protocol=dict(roles=[p],phase=phase,reference_billing='one_finite_batch',maximum_optimize_calls_per_arm=32,
            planned_once=True,uniform_candidate='exact same frozen root two-direction single-car/fleet catalog, max2 selected, no parameter changes',
            questions=p['question'],stage_admission=condition,no_fresh_extension_or_checkpoint_stitching=True)
        file=OUT/(name+'_protocol.json');write(file,protocol)
        stages.append(dict(name=name,protocol=file.relative_to(ROOT).as_posix(),sha256=sha(file),
            performance_starts=3,reference_starts=1,maximum_performance_seconds=3*p['cap_seconds'],
            maximum_reference_seconds=60,admission=condition))
    from round102_budget import account
    prior=account();assert not prior['reserved'] and not prior['incomplete']
    assert prior['completed_starts']+12<=72 and prior['completed_seconds']+27180<=80000
    write(OUT/'confirmation_freeze.json',dict(source_commit='2b65d483e',source_bindings=bindings(),
        binary_sha256=sha(BUILD/'ExactEBRP.exe'),production_freeze_sha256=sha(OUT/'production_freeze.json'),
        helper_bindings=read(OUT/'development01/identity.json')['helpers'],selected_arm='J-SUBMIT',
        unused_roles=[p['id'] for p in roles],stages=stages,
        maximum_additional_starts=12,maximum_additional_seconds=27180,Optimize=0,
        before_any_confirmation_search=True,no_old_outcomes_or_LPs_read=True,
        all_inputs_retained_no_redraw=True,no_candidate_revision=True,
        two_long_groups='N3 design-isolated and F5 existing tail, each3600s per arm; F5 may be explicitly stopped after credible negative confirmation, never recorded as executed'))
    print(json.dumps(dict(frozen=True,unused_roles=[p['id'] for p in roles],maximum_additional_seconds=27180,Optimize=0)))
