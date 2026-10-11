"""One offline organization pass over already recorded R113/R112 authority."""
import csv,difflib,json,time
from pathlib import Path
import round108_reader as core
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/unified_exact_round113'
csv.field_size_limit(64*1024*1024)
read,write,sha=core.read,core.write,core.sha
def rows(name):
    with (OUT/'reports_final'/f'{name}.csv').open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def doc(name,text):
    p=OUT/name
    with p.open('x',encoding='utf-8',newline='\n') as f:f.write(text.strip()+'\n')

def main():
    tick=time.perf_counter();s=read(OUT/'reports_final/summary.json');assert s['stage']=='BLOCKED'
    identity=read(OUT/'campaign/identity.json');launches=identity['launches'];p=launches[0]['panel']
    instance=core.evidence.instance(ROOT,p);physics=[]
    for r in rows('fleets'):
        if r['campaign']!='campaign':continue
        Y=json.loads(r['Y']);fleet=json.loads(r['routes']);route_loads=[]
        for route in fleet:
            load=0;prefix=[0]
            for op in route['operations']:
                load+=op['pickup']-op['drop'];prefix.append(load)
            assert all(0<=v<=p['Q_vector'][route['vehicle']] for v in prefix)
            route_loads.append(dict(vehicle=route['vehicle'],Q=p['Q_vector'][route['vehicle']],nodes=route['nodes'],operations=route['operations'],prefix_loads=prefix,return_load=load))
        differences=[dict(station=i,Y=Y[i],D=instance['D'][i],deviation=Y[i]-instance['D'][i]) for i in range(1,p['V']+1) if Y[i]!=instance['D'][i]]
        physics.append(dict(arm=r['arm'],F=float(r['F']),G=float(r['G']),P=float(r['P']),Y=Y,D=instance['D'],inventory_differences=differences,
            absolute_inventory_deviation=sum(abs(v['deviation']) for v in differences),routes=route_loads,maximum_duration=float(r['maximum_duration']),T=p['T_seconds'],physical_recompute_source='reports_final/fleets.csv; explicit original input',Optimize=0))
    mb=next(r for r in physics if r['arm']=='M-B');route=next(r for r in mb['routes'] if r['vehicle']==1)
    assert route['operations'][0]==dict(station=20,pickup=4,drop=0)
    modified=[dict(op) for op in route['operations']];modified[0]['pickup']=3;load=0;bad=[]
    for op in modified:
        load+=op['pickup']-op['drop']
        if load<0 or load>route['Q']:bad.append(dict(station=op['station'],load=load))
    assert bad[0]==dict(station=47,load=-1)
    write(OUT/'physical_completion.json',dict(arms=physics,deterministic_single_change=dict(arm='M-B',vehicle=1,station=20,change='pickup 4 to 3',first_invalid_prefix=bad[0],is_search=False,hidden_MIP_cause_identified=False),Optimize=0))
    cold=core.portable(ROOT,launches[3]['destination']);cold_result=read(cold/'result.json');cold_audit=read(cold/'audit.json')
    ens=core.portable(ROOT,launches[1]['destination']);events=read(cold/'observations.json')
    bounds=[r['payload'] for r in events if r['payload']['kind']=='bound' and r['payload']['global_available']]
    L=cold_audit['endpoint']['L'];assert L>1e-7 and next(r for r in physics if r['arm']=='ENS-C')['F']==0
    assert cold_result['gurobi_optimize_count']==1 and read(cold/'completion.json')['returncode']==0
    assert not (cold/'whole_arm_receipt.json').exists()
    incident=dict(status='BLOCKED',kind='CURRENT_ORIGINAL_COLD_BOUND_VS_INDEPENDENT_OWN_ZERO',
        cold_child_normal_return=True,actual_Optimize=1,returned=1,failed_stage='postexit cross-arm consistency before metrics/whole',
        rejected_cold_claim=cold_audit['endpoint'],qualified_zero_arm='ENS-C',qualified_zero_U=0.0,original_consistency_tolerance=1e-7,
        excess_over_zero=L,first_global_positive_bound_sequence=min(b['sequence'] for b in bounds if b['global_bound']>1e-7),
        returned_sequence=next(r['payload']['sequence'] for r in events if r['payload']['kind']=='returned'),
        current_call_model_SHA=next(r['payload']['model_sha256'] for r in events if r['payload']['kind']=='call'),
        evidence={q.relative_to(ROOT).as_posix():sha(q) for q in [cold/'audit.json',cold/'completion.json',cold/'result.json',cold/'observations.json',ens/'audit.json',ens/'whole_arm_receipt.json',OUT/'fees/main01/failure.txt',ROOT/'scripts/round113_campaign.py']},
        cold_formal_endpoint=False,whole_seconds=None,no_clock_synthesized=True,root_cause='unknown; requires original model/numeric-bound qualification investigation',
        unstarted_numbers=[5,6,7,8],no_automatic_retry=True,PE_or_performance_helpers_changed=False)
    write(OUT/'blocking_incident.json',incident)
    old=OUT/'engineering/admitted_reader/read_round113.py';new=ROOT/'scripts/read_round113.py'
    delta=''.join(difflib.unified_diff(old.read_text(encoding='utf-8').splitlines(True),new.read_text(encoding='utf-8').splitlines(True),fromfile='admitted/read_round113.py',tofile='offline/read_round113.py'))
    (OUT/'engineering/offline_reader_delta.patch').write_text(delta,encoding='utf-8')
    doc('reader_delta.md',f'''# Offline reader delta

Admitted reader SHA {sha(old)}; current offline reader SHA {sha(new)}.
Exact old source and unified diff are in engineering/admitted_reader and engineering/offline_reader_delta.patch.
Production, 206 source bindings, 42 performance helpers, all argv, numerical policy, pair thresholds and original clocks remain frozen.

The reader now distinguishes normal child return followed by POSTEXIT_VALIDATION_BLOCKED from interrupted execution. Joint committed journal, native log, full-original model SHA and result Optimize count establish one actual returned cold MIP; they grant no formal endpoint or replacement whole clock. Missing G100 positions explicitly retain the authority-stop reason. Totals distinguish nine qualified formal calls, one unqualified returned formal call and twelve qualification calls. A missing returned event still cannot imply cancellation.

All incomplete formal U/L/gap/certificate/whole fields remain null. This is an allowed offline classification/count clarification using original raw, not a performance change or numerical exemption. Independent postformal review and final restoration review bind the current reader. No native restart follows this change.
''')
    doc('blocking_incident.md',f'''# Current bound consistency barrier

G50 cold P returned normally (rc0), with one declared, actual and returned full-original MIP. Its necessary arm-local audit claimed U={cold_audit['endpoint']['U']:.17g}, L={L:.17g}, gap={cold_audit['endpoint']['gap']:.17g}. That audit did not establish cross-arm consistency. ENS-C independently produced a physically legal own integer zero fleet, Y=D, and independent global floor0.

The unchanged current-call guard at scripts/round113_campaign.py:127 rejected {L:.17g} > 0+1e-7. The guard ran after required postexit audit and before audit_execution_metrics.json/whole_arm_receipt.json; those two files do not exist for cold P. The native process was not killed by display publication. No complete arm clock can be manufactured from its native completion or the enclosing group fee. Its endpoint is withheld, and all three new comparisons against cold P are UNEVALUABLE.

This is a conflict between a recorded native bound claim and independent original-domain evidence. It does not identify a unique solver, scaling, model or mapping root cause. Current model SHA, original parameters and returned-bound records remain available for independent audit. No tolerance adjustment or historical exemption is applied. G100 arms5–8 were not started under the required authority barrier; ordinary negative results in earlier arms did not stop the run. Fixed arms are never rerun.
''')
    doc('geographic_bottleneck_assessment.md',"# Geographic observations\n\nG50-C1 uses the original integer inventory input, V50/M4/Q30 each/T7200. Positive lambda and weights imply F=0 exactly when Y=D. The current full physical fleet, quantities, vehicle assignments and every load prefix are in physical_completion.json. ENS-C has exact Y=D at all 50 stations, G=P=F=0, maximum route duration7197.188309052213<=7200, and zero return loads. Its earliest verified committed zero witness is sequence13; conservative complete-wrapper availability upper322.2456690000836 seconds, complete certification322.5586690000491 seconds. The native true first discovery is unknown.\n\nM-B and P-S both retain one bike of deficit at station20 (Y20=8,D20=9); all other inventories match. G=.0021826280623608025, P=.040000000000000015, F=.008182628062360805. Both have own positive complete H and actual backend exposure, no own zero witness. M-B maximum duration7149.075539656113; P-S7180.990933955269, both legal. Loads start empty, remain in assigned Q30, and one vehicle legally returns carrying one bike and pays unloading time. Cumulative pickups are not Q. Inventory is constrained to[0,C], with no min_ratio floor.\n\nThe 25-seed H semantic traces, accepted actions, complete capacity-assigned fleets and inventory agree for P-S/ENS-C/M-B, with initial F=.0325201793721973. Both M-B and P-S improve their own positive H to .008182628062360805 through actual search; they do not merely retain the initial H. ENS-C therefore shows an integer-completion increment over P-S in this window: WIN by sole complete certificate. M-B/P-S is TIE; M-B/ENS-C is severe LOSS by only the control certified. Whole times are1777.2817804088118,322.5586690000491,1771.3991304999217 seconds respectively. This directly exposes a real M-B completion cost without making P-S an adoption gate.\n\nA single deterministic check of the final M-B fleet reduces vehicle1's pickup at station20 from4 to3. It fixes that inventory but makes the following load at station47 equal-1. This proves only that specified change infeasible; it neither searches quantities nor explains the hidden MIP failure. The equal initial H, actual call domains and final quantities support the observed completion difference, not a unique AM or solver-tree cause.\n\nBoth tree arms executed3 LP+1 MIP, all returned; P-S executed1 full-original MIP after a complete13326-column Start and API readback. Recorded H/LP/MIP/residual seconds are in time_partitions.csv. Start, native adoption messages, root/end bounds, nodes/Work/cuts, original numeric model and true-G/cutoff scopes/cover are preserved in the corresponding CSVs and raw. These inclusive accounting differences cannot be subtracted as causal gains. Only committed atomic parent replacement events count as splits; hidden branching causes remain unknown. Checkpoints contain observed committed evidence plus conservative wrapper residual, actual endpoints and certificate continuation only.\n\nCold P's physical incumbent remains diagnostic raw, but its positive LB conflicts with the independently legal zero, so no new primary cold-P comparison is qualified. This is an authority barrier, not an algorithmic LOSS. See blocking_incident.md.\n\n|Actual G50 MIP|Rows/columns|Nodes|Work|Native MIP seconds|Root bound|Atomic splits|\n|---|---|---:|---:|---:|---:|---:|\n|M-B|102843/23953|2030|3911.76|1735.77|0|0|\n|ENS-C|102743/23953|190|663.81|284.57|0|0|\n|P-S|35567/13326|12345|2993.88|1758.35|0|0|\n\nAll three logs report loading their own initial Start with objective.0325202. Final verified own witnesses improve it; native log loading is not a new-incumbent timestamp. Full cut counts are in native_calls.csv. None of these node/Work/model-row differences identifies a single hidden causal mechanism.\n\nG100-R2 uses V100/M8/Q30 each/T18000 and the original input SHA. All four fixed arms remained unstarted after the G50 authority barrier. Its zero optimum is unknown in this round. No new feasible fleet, certified positive target, LB or whole time exists. All six G100 pairs and all dU/dL/dGap are null/UNEVALUABLE; no UB/LB contribution or completion mechanism can be attributed.\n")
    conclusions=s['backend_conclusions'];vector='\n'.join('|'+v['id']+'|'+conclusions['ENS-C']['five_role_vector'][k]['classification']+'|'+conclusions['M-B']['five_role_vector'][k]['classification']+'|'+str(v['origin_round'])+'|' for k,v in enumerate(conclusions['ENS-C']['five_role_vector']))
    doc('contribution_evidence_map.md',f'''# Fixed five-role contribution map

Each entry is backend X against independently paid P-S, same round/input/cap/complete H, actual backend exposed. The first three roles retain signed R112 identity and original clocks; the last two retain R113 identity. All thresholds are inherited.

|Role|ENS-C/P-S|M-B/P-S|Origin round|
|---|---|---|---|
{vector}

Both are INCOMPLETE_ATTRIBUTION, eligible4/5; G100 has no H or backend evidence after authority stop. Existing W/W/L evidence is retained. G50 adds an ENS integer-completion WIN and M-B TIE. It cannot upgrade either vector to MIXED_INCREMENT_OBSERVED because the fifth item remains absent.

The layer R112_COMPLETE12_PLUS_R113_GEO8 has20 fixed arm positions:12 qualified old measurements,3 qualified new,1 normal-return postexit-blocked new,4 unstarted. Thirty fixed pair positions comprise18 inherited evaluable and12 new (3 evaluable/9 UNEVALUABLE), giving21/30. Origin/identity/original-clock paths are explicit in arms.csv and pairs.csv. This is not20 measurements under the new wrapper.

Primary benchmark remains cold P. Old M-B/P wins on F2,R98-C2,R108-L48 remain; old ENS/P wins F2,L48 but severely loses C2. F2 relative to cold P retains a positive-objective certification increment; direct ENS/M-B versus P-S also contains a primal difference (.8659435203229896 versus .8699780578179), so it does not isolate proof alone. New G50 primary comparisons are withheld and G100 absent. The R111 CONFIRMATION_SUPPORT/R110_MAIN_36_PLUS_R111_SEED_6 statement is preserved; R110 arm42 cap violation and R112 partial13 remain unqualified. No role-specific winners are combined into an algorithm.
''')
    doc('next_research_decision.md','''# One next research priority

Choose branch3: finite insufficiency. Resolve the qualification conflict between the current G50 cold full-original returned positive lower-bound claim and the independently verified original-domain integer zero fleet, including its numeric/model/bound semantics. The falsifiable question is whether that specific native bound can be qualified under the unchanged original-domain and1e-7 policy when a legal zero fleet exists; current evidence says it cannot be accepted. The precise root cause and a justified production change are unknown.

The old three-role M-B primary wins and R111 support remain valid; new ENS integer-completion gain and severe M-B/ENS completion cost remain public. Neither missing primary comparisons nor control P-S's strength alone creates a new acceptance veto or proves the old M-B rationale false. A G100 backend/primary comparison is also still absent. These limits prevent a complete geographic attribution or independent-coverage conclusion in this stage.

This priority authorizes no new work here. Do not rerun fixed arms, add Seeds/windows, expand qualification, launch20 arms, devise a new mechanism or promote a candidate. Keep default ENS-C, leave prior PR conclusions intact, finish recoverable BLOCKED delivery and stop.
''')
    doc('numerical_policy.md','''# Inherited numerical and physical policy

Keep original input normalization, integer quantities, assigned vehicle Q, physical time T, lambda=.15, pickup/drop60/60, strict zero relative/absolute native gap parameters, FeasibilityTol/OptimalityTol1e-6, IntFeasTol1e-5 and complete certification tolerance1e-7. Keep signed floating gaps, null/error and current-call original-domain restrictions. The inherited L48 P-S gap-9.43689570931383e-16 is retained. Numeric certificates are not rational optimality proofs. Independent LP lower bounds and global nonnegative floor0 remain distinct.

Any current bound conflicting with a separately verified feasible original-domain witness is rejected under the unchanged guard; no historical case name/sidecar exemption, arbitrary raised floor or enlarged tolerance. Necessary arm-local audit alone does not supersede cross-arm consistency or complete whole-clock qualification. Incomplete endpoints and times remain null.

The P-S normal zero-Optimize audit distinguishes declaration, actual Optimize, returned and explicit not_started with source-supported phases/log/results. Three supported zero-call lifecycle branches are finite synthetic source-derived coverage; none occurred in the actual H100 or formal P-S execution. A pending actual call with missing return is not canceled. Actual mapped Start/API checks remain required if they happened, while native search/adoption/LB/OPTIMAL credit requires actual exposure.
''')
    doc('final_report.md',f'''# Round113 final scientific report

Execution BLOCKED. After finite qualification and independent ACCEPT, four fixed G50 native children ran once. Three have qualified complete clocks. Cold P returned normally but failed the frozen postexit current-bound consistency guard and has no whole receipt. G100's four fixed children were not started. No native retries or algorithm changes follow the barrier.

|G50 method|Qualified U|Qualified L|Certificate|Whole seconds|
|---|---:|---:|---|---:|
|M-B|.008182628062360805|0|open|1777.2817804088118|
|ENS-C|0|0|own zero + independent floor|322.5586690000491|
|P-S|.008182628062360805|0|open|1771.3991304999217|
|cold P|null|rejected claim|unqualified|null|

The cold rejected claim L={L:.17g} conflicts with ENS-C's legal own zero, exceeding the unchanged1e-7 consistency tolerance. Original narrow audit claimed U=.2601945154521041 and gap=.2601922348237802; those remain diagnostic raw only. Missing audit metrics/whole are not reconstructed. The stopped group fee covers real wrapper exit.

G50's complete same-H/25-seed semantic and capacity-assigned fleet check passes. ENS/P-S WIN, M-B/P-S TIE, M-B/ENS severe LOSS. First own verified zero availability upper322.2456690000836 seconds and complete certificate322.5586690000491. M-B/P-S remain one bike short at station20. G100 zero optimum remains unknown and all comparisons/deltas unavailable. Full fleets, integer operations, load prefixes, scope/cover, Start, native calls/stats and checkpoints are preserved in reports_final plus raw. See geographic_bottleneck_assessment.md for the physical interpretation and its limits.

Both five-role backend conclusions are INCOMPLETE_ATTRIBUTION (eligible4/5): ENS W/W/L/W/UNEVALUABLE; M-B W/W/L/T/UNEVALUABLE. Twenty arm positions layer12 original R112 qualified measurements with3 new qualified/1 new postexit blocked/4 unstarted. Thirty pair positions retain18 inherited plus12 new;21 evaluable/9 UNEVALUABLE. Old12 original identity/clock/physical/scope authority is inherited from signed audits and finite compatibility, not full LP re-auditing. Limited146-file original authority manifest is provided; no complete older carrier is copied. R112 remains BLOCKED and its old partial13 is never a formal endpoint. R111 support and R110 arm42 exclusion remain unchanged.

Cold P is still the primary benchmark. Old M-B/P wins all three old roles; old ENS/P loses severely on C2. F2 relative to cold P retains a positive-objective certification increment; direct ENS/M-B versus P-S also contains a primal difference (.8659435203229896 versus .8699780578179), so it does not isolate proof alone. New geographic primary comparisons are unqualified. Public costs include F2 M-B/ENS certification716.2761 vs540.2279 seconds (LOSS), L48 ENS/P-S1552.9688 vs1285.0358 and M-B/P-S1585.4304 vs1285.0358 (nonsevere LOSS), and G50 M-B/ENS severe completion LOSS. Old C2 P-S/P severe LOSS is retained. No P-S hidden adoption gate, moving benchmark or role-wise hybrid is introduced.

Two narrow helper changes are progress publication isolation and normal unstarted-Optimize audit support. A real Win32 deny-DELETE-sharing holder caused WinError5 at the actual active H100 P-S display target; one failure disabled only that arm's optional publication, necessary cadence/resource/deadline paths continued, the child completed normally, and following arms resumed publication. This establishes the failure category, not the unique historical R112 holder. Source-extracted finite supervisor mocks and three legal/illegal lifecycle fixtures cover their stated boundaries, not native canceled-Optimize executions. Four actual H100 CLI arms passed. The inherited PE SHA a8356b6a… and DLL9b5fccef…/206 source/42 helper binding and frozen H/model/parameters/8 argv remain unchanged after admission. The only postformal reader change clarifies failure classification and observed counts; admitted bytes/diff are retained.

All fees are finally closed after observed process exit:15 conservative starts,6112.501114845276 outer upper seconds. Qualification10/470.4929027557373; formal5/5642.008212089539. Failed finite/post slots and exit-observation delays are charged; nested seconds not added. Actual Optimize counts:qualification12, new qualified9, new unqualified returned1, total22. Remaining budget is unused after authority stop. Old R11239/18061.3559 belongs to its separate ledger. Offline arithmetic/reviews/pack/export/restore/publication are engineering work, recorded separately, with no Optimize.

Next priority is branch3 finite insufficiency: qualify the current original-model/native-bound conflict with the independent zero witness. No speculative mechanism, Seed/window, full20 rerun or default promotion follows. Scientific payload ends here; later actual public export/empty restore/fieldwise comparison and remote receipts are committed separately and never claim to validate future commits. PE/DLL/license/credentials are excluded; public reconstruction is evidence-only and cannot rerun the solver.
''')
    resume=OUT/'RESUME.md';text=resume.read_text(encoding='utf-8').replace('`nIndependent','\nIndependent')
    text+='\n\nTerminal scientific status BLOCKED: G50 n1–3 qualified; n4 normal child return, positive native LB vs independent own zero, frozen postexit guard failed before whole. n5–8 not started. All fees closed15 starts/6112.501114845276 outward upper seconds. No native restart, qualification loop or group2. Final root reader3 new qualified/1 blocked/4 unstarted,12 retained old,21 evaluable of30 pairs. Proceed only with offline independent review, evidence-only fresh export/restore, field comparison, stacked Draft PR and remote checks; then stop.\n'
    resume.write_text(text,encoding='utf-8',newline='\n')
    write(OUT/'engineering/organization_receipt.json',dict(seconds=time.perf_counter()-tick,engineering=True,Optimize=0,
        one_off_inventory_print_error='initial admin CSV print used default field limit and stopped on same_H_fleets; no scientific mutation; all actual readers use64MiB',
        script_SHA=sha(__file__),summary_SHA=sha(OUT/'reports_final/summary.json')))
    print(json.dumps(dict(status=s['stage'],physical_arms=len(physics),Optimize=0)))

if __name__=='__main__':main()
