"""Write the negative stage decision only from a completed raw-backed panel."""
from round107_common import *
import csv

def rows(path):
    with Path(path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def finish(report):
    from round100_idle import ensure_idle
    ensure_idle();folder=OUT/report;s=read(folder/'summary.json');gate=read(folder/'confirmation_gate.json')
    a=rows(folder/'arm_results.csv');assert len(a)==8 and s['formal_arms']==8
    assert not gate['admit_confirmation'] and not gate['A'] and not gate['B']
    assert all(q['audit_passed']=='True' for q in a) and len({q['PE_sha256'] for q in a})==1
    b=budget();assert not b['unclosed'] and b['paid_starts']==s['paid_process_starts']
    assert abs(b['paid_outer_seconds']-s['paid_outer_seconds'])<1e-9
    p=read(OUT/'confirmation_protocol.json');cancelled=[]
    for role in p['roles']:
        assert sha(ROOT/role['input_path'])==role['input_sha256']
        cancelled.append(dict(role,methods=['P-GRB','ENS-C','FRONTIER-STRUCT'],
            actual_native_processes=0,actual_Optimize_calls=0,status='NOT_STARTED_CANCELLED',
            reason='Completed same-PE eight-arm development fails both frozen A/B gates; no F2 certificate recovery and C2 route quality remains far behind contemporary P.'))
    decision=dict(stage='STOP_TESTED_CONFIGURATION',final_development_campaign='development03',
        authoritative_reports=report,completed_confirmation_campaigns=[],formal_arms_completed=8,
        production_PE_SHA=s['production_PE_SHA'],DLL_SHA=a[0]['DLL_sha256'],measured_source_commit=a[0]['source_commit'],
        performance_admission_SHA=sha(OUT/'review/performance_admission.json'),
        development_protocol_SHA=sha(OUT/'development_protocol.json'),confirmation_protocol_SHA=sha(OUT/'confirmation_protocol.json'),
        confirmation_gate=gate,confirmation_groups=cancelled,confirmation_arms_started=0,confirmation_arms_cancelled=9,
        substantive_revision=dict(used=False,reason='No new evidence identifies a qualified frontier/event interface defect. Actual original AM, native target, requeue, same-epoch child cache and terminal paths are exposed. Changing cut families, route fallback, AM or runtime rules is outside this round.'),
        scope_of_stop='The tested original ENS full-cover/AM plus existing assignment/STRUCT combination; no universal rejection of decomposition, physical cuts, or tailored exact methods.',
        paid_starts=s['paid_process_starts'],paid_outer_seconds=s['paid_outer_seconds'],
        no_default_algorithm_change=True,ADVANCE_CANDIDATE=False,
        final_independent_review_required=True,actual_public_only_restore_required=True)
    write(OUT/'admission_decision.json',decision)
    write(OUT/'confirmation_cancellation.json',dict(groups=cancelled,nominal_seconds_not_started=35100,paid_starts_not_added=10,Optimize_calls=0,IIS_calls=0))
    table=['| Role | Method | Own UB | Qualified global LB | Absolute gap | Certified | Fully observed seconds |',
           '|---|---|---:|---:|---:|:---:|---:|']
    for q in a:
        table.append('| '+ ' | '.join([q['id'],q['arm'],f"{float(q['U']):.10f}",f"{float(q['L']):.10f}",f"{float(q['gap']):.10g}",'yes' if q['certificate']=='True' else 'no',f"{float(q['observed_end_to_end_seconds']):.3f}"])+' |')
    mechanisms=['| Role | Event method | Events | Different Y | Different fleets | New physical UB | FULL lazy | A lazy | B exact / threshold | Master exclusive s | FULL oracle s | Separation s |',
                '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for q in a:
        if q['arm'] not in ['GLOBAL-STRUCT','FRONTIER-STRUCT']:continue
        values=[q['id'],q['arm'],q['events'],q['distinct_event_Y'],q['distinct_event_fleets'],q['new_physical_UBs'],q['FULL_lazy_calls'],q['A_lazy_calls'],q['B_EXACT_lazy_calls']+' / '+q['B_THRESHOLD_lazy_calls']]+[f"{float(q[k]):.3f}" for k in ['master_exclusive_seconds','oracle_seconds','separation_seconds']]
        mechanisms.append('| '+' | '.join(values)+' |')
    text='''# Round107 final performance report

## Stage and question

`STOP_TESTED_CONFIGURATION`. The qualified candidate retains the complete original ENS-C interval/AM/coverage framework, but it does not recover F2 certification and it retains C2's large route-quality deficit. The completed same-PE panel gives an informative negative result for this particular combination. No substantive revision is justified by a newly observed interface defect. Frozen confirmation gates A and B both fail; all three sealed confirmation groups (nine arms, 35100 nominal seconds) are cancelled before any launch. No ADVANCE claim is made.

GLOBAL-STRUCT is the newly measured unchanged R106 STRUCT interface with its global assignment master. FRONTIER-STRUCT uses that event family through original ENS integer requests. Their comparison measures the net effect of the complete outer framework and its resulting domains/lifecycles. ENS-C versus FRONTIER-STRUCT measures the net effect of replacing route integrality within the same outer framework. This is not a complete 2 x 2 design and does not identify a hidden native search strategy or an individual AM parameter.

## Complete comparable eight-arm results

'''+ '\n'.join(table)+'''

F2/C2 nominal caps are 1200/1800 seconds, including the original 30-second shutdown reserve; physical T is 3600/7200 and is unrelated to the experiment cap. Every arm completed normally and passed its native/domain/physical audit. The one certificate is ENS-C/F2 at 539.500 fully observed seconds. All other rows are censored. No final proof-time ranking, censored acceleration ratio, clipping of contradictions, or statistical-significance claim is made. Physical UB here is independently reconstructed from routes; binary floating arithmetic can differ from the raw evaluator in the last displayed digit.

FRONTIER/P at C2 has own UB ratio 1.891331 and absolute-gap ratio 15.939608. Relative to ENS, its own UB ratio is1.730020 and absolute-gap ratio6.860580. Both event methods finish with the same C2 physical objective and global bound. At F2 their physical objectives are equal; FRONTIER's qualified LB is slightly lower than GLOBAL's at the fixed cap. Restoring the framework supplies no observed compensation for the lost ENS certificate or C2 quality deficit.

The frozen F2 B guard passes, but neither candidate role certifies (A fails), and C2 meets neither the route-quality nor the proof-progress B condition. The gates remain prospective experiment-admission thresholds, not production rules or claims of general superiority.

## Mechanism and cost

'''+ '\n'.join(mechanisms)+'''

Each FRONTIER arm naturally exposes exactly 3 original canonical LP calls,1 partial-target MIP and1 terminal MIP. Qualified native targets reach 0.6058893256>=0.5296185500 at F2 and 0.1887368019>=0.1620035253 at C2. The controller requeues the open parent, reuses its same-epoch complete child LP pair, then chooses terminal under unchanged AM rules. Its full-cover trace remains open at final deadline. There is no manual candidate restart; each of the two original integer requests owns one fresh Optimize. Separate environments are used for the waiting outer master and serial FULL oracles.

F2 terminal request 5/event 2 produces B_EXACT and B_THRESHOLD from the same six-order physical conflict; those rows are two emissions, not two independent conflicts. Event 3 then continues in that same Optimize and produces the newly improved full physical fleet. Natural C2 A/FULL conflicts and same-Optimize continuation are retained alongside every candidate raw vector and lazy activity. Explicit selected independent event chains are indexed in the final review.

The candidate C2 terminal produces 10 FEAS events and 4 new UB files from 2465 terminal events (the separate partial request contributes the initial FEAS event). GLOBAL produces 10 FEAS events and 4 new UB files from 2521 events. These are within-run mechanism counts, not independent problem replications. The much larger master-exclusive cost remains dominant; speeding up arithmetic separation cannot account for the observed quality deficit. Physical UB, submission attempt/API0/deferred, exact later vector observation and final native acceptance are separate tables.

GLOBAL total/initial-mode cache hits are 36/2 at F2 and 425/143 at C2, reconstructed from physical startup operations and exact event-specific oracle returns. FRONTIER records 38/4 and 408/146 directly in its raw hit CSV. Repeated initial-mode hits do not represent additional proofs; cache counts and provenance are separate from first physical verification.

Formal cross-request noninitial physical-cache hits and row remaps are 0: `NOT_EXPOSED`. Qualified native FULL reuse and an independent threshold-selector absent-to-present remapping fixture establish functionality separately. Formal leaf INF, high local LB pruning, domain-outside FEAS/feedback skips and terminal OPT closure are `NOT_EXPOSED`; their qualified fixtures and pure/proof tests are not advertised as performance gains. Native actual deadline qualifications cover both inner UNKNOWN and outer open stop. UNKNOWN never supplies INF, a target requeue, or a certificate.

Request bounds are local even where retained raw event fields use the inherited name `native_global_bound`. The global result is reconstructed from the complete original cover. Likewise, retained `stop_whole_run` metadata is not alone used to infer controller termination: the reader derives scoped obligations and target/requeue classes. No raw bytes are rewritten to improve these labels.

`time_partitions.csv` gives nonoverlapping startup-before-exact, original LP native inclusive, master native inclusive and controller/setup/write residual. Event master inclusive time is partitioned into exclusive, oracle, separation, audit/mapping and callback-other time. HGA is an overlapping startup diagnostic. AM math has no separate timer and is honestly included in the controller residual; unchanged controls have no separate callback partition. Native inclusive times are not added to outer fees.

## Contracts and qualification

The default-off flag is `--round107-frontier-struct true`. Canonical objectives, rows, domains and all Y/state/assignment/operation integer declarations are retained; only x/load integer declarations are relaxed. A/B and fixed-car-order FULL are inherited unchanged. IIS/core is off. There is no new net-return row, necessary-cut family, route-integer fallback, AM/time/size rule, heuristic, imported UB, history cut or cross-arm cache.

The proof chain, including domain embedding, high epigraph/real G outside the leaf, no-domain-Start, empty improvement domain, local INF, bound dominance and full-cover closure, is in `mathematical_algorithm.md` and `scope_contract.md`. Original LP requests stay continuous and receive no learned pool rows or extra Optimize. Incumbent epochs, child identities, cache invalidation and one-time milestone semantics remain the original controller rules; `master_retention_table.md` records retained and changed contracts. Conditional finite progress uses those contracts and never claims every finite-cap run certifies.

The selected native fixture evidence keeps its actual older fixture PE identities. Reuse after the production repair is by independently verified unchanged State/MIP/Scope/controller/oracle function bodies, not by an assertion that all source/PE bytes match. Production cli02 on the final PE independently exposes actual target -> requeue -> terminal with the original 24+1 startup. The independent repaired performance admission binds the final PE, source, DLL, protocol, qualification and eight-arm identity before formal release.

Two development correctness failures remain: development02 reached three old-PE F2 controls before the candidate failed the preset guard; cli01 entered actual startup and an original LP before a post-LP metadata string-order check failed. Repairs restore inherited R68 preset equality and compare finite semantic coefficient maps after unchanged original LP solving. Complete development03 contemporary controls and both candidate roles replace the partial old panel in all final comparisons. Failed runs, superseded identities and fees remain public. The recovered cli01 actual LP cannot be erased by its emergency Optimize counter0. Reader-only historical LP format repairs and all failed engineering reads are also retained.

## Inheritance and limits

R106 PR168/base delivery0350dbcc60d1c68e5c499d2e9880ecc1deaf031c was audited by an actual zero-solver public restore, exact old reader/field comparisons and independent selected physics/proofs. Its original F2 ENS certificate at 577.344 seconds and GLOBAL censoring at 1170.344 seconds, C2 quality deficit, event/mode counts and master-dominated timing remain inherited evidence, not this round's new measurements. Related R41/42/59,52/53/54,64/66,97 through 106 precedents are mapped in the inheritance review. Earlier stopped families are not reopened.

The independent complete R106 candidate net-return audit identifies exactly 9 C2 FULL/car0 events above Q20, including event 341 pickup 44/drop 21/net 23; no STRUCT event has that violation. Nonnegative net return is explicit while its upper bound depends on route integrality. It is a future strengthening clue, related to R66, and is not added in any Round107 formal or revised measurement.

Stopping this tested configuration does not reject every decomposition, physical cut, or tailored exact method. The remaining research question is whether a different justified route-feasibility interface can improve physical conversion while retaining the qualified scoped contract. This round does not start another tuning campaign, fixed-Y retry, or unbudgeted long confirmation.

## Identity, resources and delivery

'''+f"Measured source commit `{a[0]['source_commit']}`; production PE SHA `{s['production_PE_SHA']}`; Gurobi 13.0.2 DLL SHA `{a[0]['DLL_sha256']}`. F2 input SHA `ebdf99e77dc9dcc57946970fa6d7e1cdf2defdcd277562a454d4889c716b645e`; C2 input SHA `07d0964c87b534254e6bf2957911859a6a2bd73e377211728b7e65f44294fc76`. Threads1/Seed0/PresolveAuto, original numeric tolerances and zero MIP gaps are read back. Actual cold P canonical SHA/fingerprint/rows/columns and independent once-per-arm startup are in the raw records and published tables.\n\n"+f"Total current-round conservative paid starts `{s['paid_process_starts']}/72`; complete outer fee `{s['paid_outer_seconds']:.9f}/80000` seconds. Actual Optimize `{s['all_Optimize_starts']}`, IIS `{s['all_IIS_starts']}`, missing-after `{s['native_missing_after']}`. These actual native calls differ from conservative process-start charging. Enclosing wrapper pause, qualification, eight children, callbacks/writes and shutdown are charged once; inner native timings are not charged again. Engineering build/read/pack/restore/review receipts have 0 paid starts and 0 solver calls. The native_final01 intermediate-child correction is retained separately.\n\n"+f"Authoritative raw-backed reports: `{report}/`. `admission_decision.json` and `confirmation_cancellation.json` list the 9 wholly unstarted cancelled confirmation arms. Public carrier dependencies and actual fresh restore, all-field comparison and final independent delivery receipts are described in `reproduce.md` and the separately committed restoration/review records. This is evidence/mathematical reconstruction, not a new independent-engine performance rerun. No PE, DLL, license or credentials are distributed.\n"
    (OUT/'final_report.md').write_text(text,encoding='utf-8',newline='\n')
    print(json.dumps(dict(stage=decision['stage'],reports=report,cancelled_arms=9,starts=s['paid_process_starts'],outer_seconds=s['paid_outer_seconds'],Optimize_calls=0,IIS_calls=0)))

if __name__=='__main__':finish(sys.argv[1])
