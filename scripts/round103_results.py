"""Completed-run reporting using the inherited scope and clock readers.

No Optimize and no reconstruction of missing evidence. Run only while idle.
Reporting is charged as a reader batch; packaging is separate engineering.
"""
import sys,json,math
from pathlib import Path
import round101_reporting_core as core
import round101_clock_core as clock
from round103_common import *
from round100_idle import ensure_idle

def records(camp):
    return [json.loads(x) for x in (Path(camp)/'summary.jsonl').read_text().splitlines()]

def main(label,campaigns):
    ensure_idle();core.OUT=clock.OUT=OUT
    core.records_view=clock.records_view=records
    core.audit_view=clock.audit_view=lambda d:read(Path(d)/'audit.json')
    original_save=clock.save
    def save_clock(path,rows):
        if Path(path).name=='discovery_certification.csv':
            for r in rows:r['scope']=r['scope'].replace('offline independent audit separately engineering',
                'recorded postexit offline audit additionally charged in Round103 whole-round ledger')
        original_save(path,rows)
    clock.save=save_clock
    shared=[]
    for name in campaigns:
        done=records(OUT/name)
        for role in {r['id'] for r in done}:
            shared.append(math.floor(min(r['completion']['end_to_end_seconds'] for r in done if r['id']==role)))
    clock.CHECKPOINTS=sorted(set(clock.CHECKPOINTS+[1500]+shared))
    core.extract(label,campaigns);clock.main(label+'_clocks',campaigns)
    target=OUT/label;native=[];whole=[]
    for name in campaigns:
        q=read(OUT/name/'identity.json')
        for r in records(OUT/name):
            d=Path(r['destination']);a=read(d/'audit.json');h=a.get('resource_hull',{})
            whole.append(dict(campaign=name,number=r['number'],role=r['id'],arm=r['arm'],
                native_Optimize_calls=a['native_calls_started'],auxiliary_Optimize_calls=h.get('auxiliary_Optimize_calls',0),
                DP_calls=h.get('DP_calls',0),postexit_audit_seconds=a.get('offline_audit_seconds',0),
                process_and_admission_seconds=r['completion']['end_to_end_seconds'],
                charged_seconds=r['completion']['end_to_end_seconds']+a.get('offline_audit_seconds',0)))
            for p in sorted((d/'external/native_logs').glob('*.round103.summary.json')):
                s=read(p);base=Path(str(p).removesuffix('.round103.summary.json'))
                native.append(dict(campaign=name,number=r['number'],role=r['id'],arm=r['arm'],
                    path=p.relative_to(ROOT).as_posix(),sha256=sha(p),**s))
    core.csv_write(target/'hull_native_calls.csv',native)
    core.csv_write(target/'whole_run_costs.csv',whole)
    # Preserve inherited comparisons and add the same-run F2 J/H attribution
    # role. Single-sided fields are bounds, never exact speed ratios.
    complete_pairs=core.csv_read(target/'pairs.csv')
    run_groups={}
    for r in core.csv_read(target/'runs.csv'):
        run_groups.setdefault((r['campaign'],r['role']),{})[r['arm']]=r
    for (camp,role),g in run_groups.items():
        if 'J-SUBMIT' not in g or 'H-SUBMIT' not in g:continue
        template=next(dict(r) for r in complete_pairs if r['campaign']==camp and
                      r['role']==role and r['candidate']=='H-SUBMIT')
        a,b=g['J-SUBMIT'],g['H-SUBMIT']
        ac,bc=a['certificate']=='True',b['certificate']=='True'
        at,bt=float(a['end_to_end_seconds']),float(b['end_to_end_seconds'])
        both=ac and bc;delta=bt-at;ratio=bt/at
        template.update(reference='J-SUBMIT',reference_certified=ac,candidate_certified=bc,
            censoring='both_certified' if both else 'reference_only' if ac else 'candidate_only' if bc else 'both_unproved',
            certified_time_delta=delta if both else None,certified_time_ratio=ratio if both else None,
            material_time_change=bool(both and abs(delta)>=30 and abs(ratio-1)>=.1),
            severe_time_regression=bool(both and delta>=120 and ratio>=1.25),
            eventual_time_order_known=both or bool(bc and bt<at) or bool(ac and at<bt),
            time_delta_upper_bound=delta if bc and not ac else None,
            time_delta_lower_bound=delta if ac and not bc else None,
            material_one_sided_time_advantage=bool(bc and not ac and -delta>=30 and ratio<=.9),
            material_one_sided_time_regression=bool(ac and not bc and delta>=30 and ratio>=1.1))
        for prefix,r in [('reference',a),('candidate',b)]:
            for k in ['U','L','gap','relative_gap']:template[prefix+'_'+k]=r[k]
        au,bu,ag,bg=(float(r[k]) if r[k] else None for r,k in [(a,'U'),(b,'U'),(a,'gap'),(b,'gap')])
        template.update(material_budget_U_change=bool(au is not None and bu is not None and
            abs(bu-au)>=.001 and abs(bu-au)/max(abs(au),1e-12)>=.01),
            material_budget_gap_change=bool(ag is not None and bg is not None and
            abs(bg-ag)>=.001 and abs(bg-ag)/max(abs(ag),1e-12)>=.1))
        complete_pairs.append(template)
    for r in complete_pairs:
        ac=str(r['reference_certified'])=='True';bc=str(r['candidate_certified'])=='True'
        g=run_groups[(r['campaign'],r['role'])]
        at=float(g[r['reference']]['end_to_end_seconds']);bt=float(g[r['candidate']]['end_to_end_seconds'])
        r['severe_one_sided_time_regression']=bool(ac and not bc and bt-at>=120 and bt/at>=1.25)
        r['scope']='Complete numerical certificate times when both certify; one-sided observed time bounds otherwise; endpoint budget differences are not eventual-time rankings'
    core.csv_write(target/'complete_pairs.csv',complete_pairs)
    groups={}
    for r in core.csv_read(OUT/(label+'_clocks')/'checkpoints.csv'):
        if r['covered']=='True':groups.setdefault((r['campaign'],r['role'],r['checkpoint_full_seconds']),{})[r['arm']]=r
    paired=[]
    for (camp,role,t),g in groups.items():
        for ref,cand in [('P-GRB','ENS-C'),('P-GRB','H-SUBMIT'),('ENS-C','H-SUBMIT'),('J-SUBMIT','H-SUBMIT')]:
            if ref not in g or cand not in g:continue
            a,b=g[ref],g[cand]
            def num(r,k):return float(r[k]) if r[k] else None
            au,bu,ag,bg=num(a,'U'),num(b,'U'),num(a,'gap'),num(b,'gap')
            paired.append(dict(campaign=camp,role=role,checkpoint_full_seconds=float(t),reference=ref,candidate=cand,
                reference_U=au,candidate_U=bu,reference_L=num(a,'L'),candidate_L=num(b,'L'),
                reference_gap=ag,candidate_gap=bg,U_delta=bu-au if au is not None and bu is not None else None,
                gap_delta=bg-ag if ag is not None and bg is not None else None,
                material_U_change=bool(au is not None and bu is not None and abs(bu-au)>=.001 and abs(bu-au)/max(abs(au),1e-12)>=.01),
                material_gap_change=bool(ag is not None and bg is not None and abs(bg-ag)>=.001 and abs(bg-ag)/max(abs(ag),1e-12)>=.1),
                scope='Same-run scope-verified covered prefixes; certificates may carry; no interpolation, borrowed certificate or eventual-time estimate'))
    core.csv_write(target/'checkpoint_pairs.csv',paired)
    # Short qualification SHADOW is intentionally not compared to a longer
    # certification run. Equal start policy alone cannot isolate cut causality.
    write(target/'reporting_identity.json',dict(Optimize_calls=0,reader_sha256=sha(core.__file__),
        clock_sha256=sha(clock.__file__),wrapper_sha256=sha(__file__),
        campaigns=campaigns,additional_shared_whole_second_checkpoints=shared,
        no_recovery_overlay=True,no_short_shadow_complete_causal_comparison=True,
        fee_scope='Whole-round ledger is generated after this reader receipt closes; campaign cost tables are subsets, never added twice'))
    print(json.dumps(dict(passed=True,runs=len(whole),Optimize_calls=0)))

if __name__=='__main__':main(sys.argv[1],sys.argv[2:])
