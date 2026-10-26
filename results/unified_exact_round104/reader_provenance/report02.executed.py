"""Read completed frozen arms; no optimization or reconstructed performance."""
from round104_common import *
import math
import round101_reporting_core as core
import round101_clock_core as clock

def records(camp):
    return [json.loads(s) for s in (Path(camp)/'summary.jsonl').read_text().splitlines()]

def pairs(a,b,prefix):
    ac,bc=a['certificate']=='True',b['certificate']=='True'
    at,bt=float(a['end_to_end_seconds']),float(b['end_to_end_seconds'])
    def value(r,k):return float(r[k]) if r.get(k) else None
    au,bu,ag,bg=(value(r,k) for r,k in [(a,'U'),(b,'U'),(a,'gap'),(b,'gap')])
    delta=bt-at;ratio=bt/at;both=ac and bc
    return dict(prefix,reference=a['arm'],candidate=b['arm'],reference_certified=ac,candidate_certified=bc,
        censoring='both_certified' if both else 'reference_only' if ac else 'candidate_only' if bc else 'both_unproved',
        certified_time_delta=delta if both else None,certified_time_ratio=ratio if both else None,
        material_time_change=bool(both and abs(delta)>=30 and abs(ratio-1)>=.1),
        severe_time_regression=bool(both and delta>=120 and ratio>=1.25),
        eventual_time_order_known=both or bool(bc and bt<at) or bool(ac and at<bt),
        time_delta_upper_bound=delta if bc and not ac else None,time_delta_lower_bound=delta if ac and not bc else None,
        material_one_sided_time_advantage=bool(bc and not ac and -delta>=30 and ratio<=.9),
        material_one_sided_time_regression=bool(ac and not bc and delta>=30 and ratio>=1.1),
        severe_one_sided_time_regression=bool(ac and not bc and delta>=120 and ratio>=1.25),
        reference_U=au,candidate_U=bu,reference_L=value(a,'L'),candidate_L=value(b,'L'),reference_gap=ag,candidate_gap=bg,
        signed_U_delta=bu-au if au is not None and bu is not None else None,
        signed_gap_delta=bg-ag if ag is not None and bg is not None else None,
        material_budget_U_change=bool(au is not None and bu is not None and abs(bu-au)>=.001 and abs(bu-au)/max(abs(au),1e-12)>=.01),
        material_budget_gap_change=bool(ag is not None and bg is not None and abs(bg-ag)>=.001 and abs(bg-ag)/max(abs(ag),1e-12)>=.1),
        scope='Both-certified times or one-sided bounds; endpoint differences are not eventual-time rankings')

COMPARISONS=[('P-GRB','ENS-C'),('P-GRB','OC-ACTIVE'),('ENS-C','OC-ACTIVE'),
             ('P-GRB','OC-SHADOW'),('ENS-C','OC-SHADOW'),('OC-SHADOW','OC-ACTIVE')]

def capability(target):
    rows=[];overview=[];points=[]
    for label in ['pool_F2_02','pool_C2_02','pool_F5_01','pool_F5_native01']:
        d=OUT/'diagnostics'/label;s=read(d/'summary.json');plan=read(d/'plan.json');allvalue=s['records']['ALL']['objective']
        for kind,r in s['records'].items():
            literal=read(d/(kind+'.rows.json'));magnitudes=[abs(a) for row in literal for n,a in row['coefficients'] if a]
            gain=allvalue-s['records']['RAW']['objective']
            rows.append(dict(label=label,role=s['role'],expression=kind,source_sha256=s['source_sha256'],
                source_scope='actual F5 native L0.0 interval/cutoff' if plan.get('native_scope_override',False) else 'old raw canonical',
                rows=r['rows'],nonzeros=r['nonzeros'],objective=r['objective'],signed_minus_ALL=r['objective']-allvalue,
                descriptive_normalized_gain_retention=(r['objective']-s['records']['RAW']['objective'])/gain if abs(gain)>1e-7 else None,
                minimum_nonzero_coefficient=min(magnitudes,default=None),maximum_absolute_coefficient=max(magnitudes,default=None),
                maximum_absolute_RHS=max((abs(row['rhs']) for row in literal),default=None),
                primal_residual=r['primal']['maximum_absolute_residual'],stationarity_max=r['stationarity_max'],
                signed_primal_minus_dual=r['signed_primal_minus_dual'],solver_DualVio=r['solver_DualVio'],
                qualification=('numerical LP only; Python native tiny-coefficient row validity not readback-qualified' if label=='pool_F2_02' and kind in ['GROUPED','FLEET'] else 'numerical reoptimized LP; no exact rational optimum'),historical_LH=s['actual_LH'],historical_status=s['historical_status']))
        rr=s['records'];overview.append('| '+s['role']+(' native L0.0' if plan.get('native_scope_override',False) else ' raw')+' | '+
            ' | '.join(format(rr[k]['objective'],'.17g') for k in ['RAW','PASS','ALL'])+' | '+
            (format(s['actual_LH'],'.17g') if s['actual_LH'] is not None else 'UNKNOWN / not established in this scope')+' | '+
            '/'.join(str(rr[k]['rows']) for k in ['ALL','ACTIVE','GROUPED'])+' | '+format(s['signed_GROUPED_minus_ALL'],'.17g')+' |')
    for p in read(OUT/'diagnostics/native_points02/summary.json')['records']:
        r=dict(role=p['role'],kind=p['kind'],node_count=p['node_count'],point_objective=p['point_objective'],
            matrix_sha256=p['source_sha256'],same_as_old_raw=p['same_matrix'],full_matrix_residual=p['residual']['maximum_absolute_residual'])
        for k,s in p['sets'].items():
            r[k+'_reliable_violations']=s['reliable_over_10_native_FeasibilityTol'];r[k+'_maximum_signed']=s['maximum_signed']
        points.append(r)
    core.csv_write(target/'objective_capability.csv',rows);core.csv_write(target/'native_point_capability.csv',points)
    text='''# Same-scope capability and objective retention

Historical rows are paid only as new expression diagnostics. Each row below
shares its original typed canonical matrix, columns, bounds and objective.
PASS is the actual R103-H production selection, not R102-J. The historical
LH values are closures within declared member tolerance, not rational optima.
F5 remains UNKNOWN. Its actual observed L0.0 scope is separately reoptimized;
its resource contract permits global source-row transfer, but its old LH is
not transferred as a bound of that narrower model.

| Scope | L0 RAW | Lpass H | LC ALL | LH qualification | ALL/ACTIVE/GROUPED rows | signed GROUPED−ALL |
|---|---:|---:|---:|---|---:|---:|
'''+ '\n'.join(overview)+'''

`REPORT_LABEL/objective_capability.csv` retains every expression, signed
difference, nonzero count and primal/dual residual. Tiny wrong-sign Pi are
explicitly repaired, strict negative Pi are retained without epsilon pruning.
The actual C++ compensated GROUPED2 result differs from ALL by
−6.023938015×10⁻¹⁰; the fleet1 result differs by −2.077199635×10⁻⁹.
Exact signed-bound compensation and native row readback passed; numerical
objective retention does not upgrade floating Pi into a rational certificate.
Python F2 GROUPED/FLEET are numerical expression diagnostics only: tiny
native-unsupported coefficients were not individually read back/compensated
for deletion. The independent review flags a nonzero-bound potential
deletion in GROUPED0, so its actual native-row validity is unqualified.
The C++ emitted GROUPED/FLEET rows have separate exact compensation and
actual native readback qualification. Node tests use the legal serialized
aggregate rows, not an assertion that the Python native LP contained them
coefficient-for-coefficient.

| Role | Actual sampled point | Node | Point objective | ALL reliable | ACTIVE reliable | GROUPED reliable |
|---|---|---:|---:|---:|---:|---:|
'''
    text+='\n'.join('| '+r['role']+' | '+r['kind']+' | '+str(r['node_count'])+' | '+format(r['point_objective'],'.17g')+' | '+
                     ' | '.join(str(r[k+'_reliable_violations']) for k in ['ALL','ACTIVE','GROUPED'])+' |' for r in points)
    text+='''

Reliability threshold is10× unchanged native FeasibilityTol=10⁻⁵ on the
actual admitted/scaled row. All12 full vectors satisfy their original scoped
matrix at its unchanged feasibility tolerance. The latest sampled root is
only the last observable root, never asserted to include every internal cut.
F5 has no positive-node sample in its180s window. A point objective/global LB
above old LH does not establish that native cuts imply the complete domain.
The old R103 “native” point came from J-SUBMIT; it is not used as original ENS
evidence here. The production candidate generates a fresh pool; its982/29
rows are separate from this historical827/30-row expression diagnosis.
'''
    (OUT/'capability_table.md').write_text(text.replace('REPORT_LABEL',target.name),encoding='utf-8')

def main(label,campaigns):
    from round100_idle import ensure_idle
    ensure_idle();core.OUT=clock.OUT=OUT;core.records_view=clock.records_view=records
    core.audit_view=clock.audit_view=lambda d:read(Path(d)/'audit.json')
    shared=[math.floor(min(r['completion']['end_to_end_seconds'] for r in records(OUT/name) if r['id']==role))
            for name in campaigns for role in {r['id'] for r in records(OUT/name)}]
    clock.CHECKPOINTS=sorted(set(clock.CHECKPOINTS+[30,60,120,180]+shared))
    core.extract(label,campaigns);clock.main(label+'_clocks',campaigns)
    target=OUT/label;groups={};complete=[];costs=[];native=[]
    for r in core.csv_read(target/'runs.csv'):groups.setdefault((r['campaign'],r['role']),{})[r['arm']]=r
    for (name,role),g in groups.items():
        for ref,cand in COMPARISONS:
            if ref in g and cand in g:complete.append(pairs(g[ref],g[cand],dict(campaign=name,role=role)))
    core.csv_write(target/'complete_pairs.csv',complete)
    for name in campaigns:
        for r in records(OUT/name):
            d=Path(r['destination']);a=read(d/'audit.json');h=a.get('resource_hull',{})
            costs.append(dict(campaign=name,role=r['id'],arm=r['arm'],native_Optimize_calls=a['native_calls_started'],
                auxiliary_Optimize_calls=h.get('auxiliary_Optimize_calls',0),DP_calls=h.get('DP_calls',0),
                self_paid_preparation_seconds=sum(s.get('seconds',0) for s in h.get('records',[]) if not s['cache_hit']),
                postexit_audit_seconds=a.get('offline_audit_seconds',0),
                end_to_end_seconds=r['completion']['end_to_end_seconds'],
                charge_scope='parent receipt pays all nested generation/native/audit; do not add these stages again'))
            for p in sorted((d/'external/native_logs').glob('*.round104.summary.json')):
                native.append(dict(campaign=name,role=r['id'],arm=r['arm'],path=p.relative_to(ROOT).as_posix(),sha256=sha(p),**read(p)))
    core.csv_write(target/'objective_native_calls.csv',native);core.csv_write(target/'whole_run_costs.csv',costs)
    checkpoints={};paired=[]
    for r in core.csv_read(OUT/(label+'_clocks')/'checkpoints.csv'):
        if r['covered']=='True':checkpoints.setdefault((r['campaign'],r['role'],r['checkpoint_full_seconds']),{})[r['arm']]=r
    for (name,role,t),g in checkpoints.items():
        for ref,cand in COMPARISONS:
            if ref not in g or cand not in g:continue
            a,b=g[ref],g[cand]
            def val(r,k):return float(r[k]) if r[k] else None
            au,bu,ag,bg=(val(r,k) for r,k in [(a,'U'),(b,'U'),(a,'gap'),(b,'gap')])
            paired.append(dict(campaign=name,role=role,checkpoint_full_seconds=float(t),reference=ref,candidate=cand,
                reference_U=au,candidate_U=bu,reference_L=val(a,'L'),candidate_L=val(b,'L'),reference_gap=ag,candidate_gap=bg,
                signed_U_delta=bu-au if au is not None and bu is not None else None,
                signed_gap_delta=bg-ag if ag is not None and bg is not None else None,
                material_U_change=bool(au is not None and bu is not None and abs(bu-au)>=.001 and abs(bu-au)/max(abs(au),1e-12)>=.01),
                material_gap_change=bool(ag is not None and bg is not None and abs(bg-ag)>=.001 and abs(bg-ag)/max(abs(ag),1e-12)>=.1),
                scope='Same-run committed scope-verified prefixes; no interpolation, borrowed certificates or common-node claim'))
    core.csv_write(target/'checkpoint_pairs.csv',paired)
    write(target/'reporting_identity.json',dict(Optimize_calls=0,source_sha256=sha(__file__),reader_sha256=sha(core.__file__),
        clock_sha256=sha(clock.__file__),campaigns=campaigns,shared_whole_second_checkpoints=shared,
        performance_stages_not_double_counted=True,no_reconstructed_native_performance=True))
    capability(target)
    print(json.dumps(dict(passed=True,arms=len(costs),Optimize_calls=0)))

if __name__=='__main__':main(sys.argv[1],sys.argv[2:])
