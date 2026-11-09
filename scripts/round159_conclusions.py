"""Compute scoped interval/physical summaries once from saved evidence."""
import csv
from fractions import Fraction as F
from round159_common import *
from round140_common import git

def run():
    analysis=read(OUT/'trajectory_analysis.json');physical=[];intervals={}
    for role,suffix in [('R-X35-S-T2','rx'),('N-B35-S','nb')]:
        r=analysis['roles'][role];source=read(OUT/'inputs_v2'/role/'source.json')
        for stage in ('baseline','joint'):
            if suffix=='rx' and stage=='baseline':continue # closed review-side C control is reused
            report=read(OUT/'review'/f'complete_{stage}_{suffix}.json')
            for v in report['result']['vehicles']:
                pure=F(v['unloaded_travel_scaled'])/2**53;travel=F(v['travel_scaled'])/2**53
                k=v['vehicle'];P=report['resource']['vehicles'][k]['P'];d=source['data']
                H=F(source['contract']['H_exact']);h=F(source['contract']['h_exact'])
                physical.append(dict(role=role,stage=stage,vehicle=k,P=P,D=report['resource']['vehicles'][k]['D'],
                    unloaded_travel=float(pure),loaded_travel=float(travel),prefix_penalty=float(travel-pure),
                    total=float(travel+120*P),T=d['T'],complete=v['complete'],
                    pure_tour_over_T=pure+120*P>F(d['T']+1e-7),
                    guarded_fixed_set_unloaded_pickup_budget=int((H-pure)//h),
                    guarded_fixed_Y_loaded_pickup_budget=int((H-travel)//h),
                    scope='unloaded budget is Y-independent only on this fixed active set; loaded budget is fixed Y/owner only'))
        best=r['chain'][-1]
        intervals[role]=dict(L_I=r['L_I'],U_I=r['U_I'],U_P_ref=r['U_P_ref'],U_P=r['U_P_ref'],U_R=best['U_R'],J_exact=best['J_exact'],
            eta_R=best['eta_R'],U_R_minus_L_I=best['U_R']-r['L_I'],resource_improvement_from_reference=r['price_reduction_from_old_ref'],
            resource_improvement_from_fixed_owner=r['price_reduction_from_fixed_owner'],fixed_owner_U_R=r['chain'][0]['U_R'],
            physical_upper_change=0,global_lower_change=0,strict_F_R_above_U_I='UNKNOWN',physical_optimum_minus_resource_optimum='UNKNOWN',
            scalar_ceiling_scope='only D_C containing the same D_R, not full routing Q with shared cuts')
    write(OUT/'final_intervals.json',intervals);write(OUT/'physical_summary.json',physical)
    with (OUT/'reports/physical.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(physical[0]));w.writeheader();w.writerows(physical)
    build=read(OUT/'build_manifest.json');current={}
    for p in list((ROOT/'scripts').glob('round159_*.py'))+list((ROOT/'src').glob('*159*'))+list((ROOT/'include').glob('*159*')):
        current[p.relative_to(ROOT).as_posix()]=sha(p)
    write(OUT/'source_manifest.json',dict(UTC=utc(),dependency_delivery=BASE,R158_science='163b1b3d0dbcc7be3a84d94108ef4a26ae9baba3',
        main=git('rev-parse','origin/main',cwd=ROOT).decode().strip(),research_build=build,
        source_bytes=current,new_online_core_language='C++',Python_roles=['offline RN export','orchestration','independent readback','reused R157 E1 oracle'],
        loaded_engine_binding_E1=read(OUT/'inputs_v2/manifest.json')['DLL'],
        delivered_new_research_PE_member='results/unified_exact_round159/runtime/Round159Research.exe',
        no_new_production_build=True,production_source='092bad58d677cd8bef934d91e11d8abff93cba83',
        source_identity_vs_delivery='Exact executed source snapshots and build manifest are authoritative; later delivery commits do not identify a newly measured binary',
        Cpp_calls='link/launch DLL path and hash plus controlled PATH; full loaded-module binding retained for common Python oracle',
        no_language_speedup_comparison=True,original_handling_contract_seconds=[60,60]))
    E=read(OUT/'deepening/free_owner_rx/result.json');assert E['classification']=='UNKNOWN'
    ablation=read(OUT/'owner_ablation.json');assert ablation['owner_freedom_needed_for_this_improvement']
    write(OUT/'final_decision.json',dict(UTC=utc(),study_complete=False,decision='RESOURCE_WITNESSES_AND_SCOPED_MECHANISM_EVIDENCE; NO COMPLETE CANDIDATE',
        new_qualified_resource_upper=True,new_physical_upper=False,new_global_lower=False,F_entered=False,
        E1=E['classification'],E2='not entered; no new generally valid structure established',E3='not entered; no new whole-level information source',
        online_self_payment='Cheap joint resource construction is observed, but no physically consumable benefit is demonstrated; one1329.6s offline free-owner query stays UNKNOWN',
        mechanism='Same-block RX owner-fixed transported lower .2945344157494531 exceeds released joint price .2922946074975457; both sources show nonzero old-owner quantity-net changes compensated by owner changes; NB also activates a station',
        physical='Complete fixed-combination DP shows tour/handling obstructions; NB also exhibits binding prefix-load costs. No all-owner exclusion follows.',
        novelty_boundary='No new handling identity, original-J model, classical DP, general owner-exchange theory or complete-method improvement is claimed',
        stop_evidence='Both resource trajectories finish their12 frozen blocks; selected combinations fail complete DP; the sole free-owner query exhausts8192 nodes without a route. Another unchanged window cannot add a demonstrated online benefit.',
        continue_only_with='New justified information coupling active-set tour and prefix feasibility to stock/owner construction, or a qualified own-state physical route benefit; no automatic parameter grid or long UNKNOWN',
        capacity_seconds=TOTAL,unused_capacity_not_reallocated_to_unknown=True,review='Final saved-evidence audit pending'))

if __name__=='__main__':run()
