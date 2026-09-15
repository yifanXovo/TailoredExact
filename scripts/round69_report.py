"""Prepare a complete-stage report from audited tables, never a partial claim."""
import csv,json
from pathlib import Path
import round69_research as run

def rows(path):return list(csv.DictReader(path.open(encoding='utf-8')))
def number(value,digits=6):return f'{float(value):.{digits}f}' if value not in [None,''] else 'unavailable'
def signed_gap(value):
    x=float(value)
    return f'{x:.3e}' if abs(x)<1e-7 else f'{x:.9f}'

def main():
    assert not (run.OUT/'active_run.lock').exists()
    resource=run.read(run.OUT/'resource_status.json');data=rows(run.OUT/'runs.csv')
    expected={('D3','VD-S')}|{(i,a) for i in ['E7','S12','N12','D6','D7'] for a in ['P-GRB','K1-R','VD-S']}
    assert len(data)==16 and {(r['id'],r['arm']) for r in data}==expected
    assert resource['performance']==16 and resource['native_micro']==0 and resource['failures']==0
    assert resource['reference_build_only_runs']==6
    assert all(r['failure']=='False' for r in data)
    starts=run.read(run.OUT/'start_checks.json');pairs=rows(run.OUT/'pairs.csv')
    repeats=run.read(run.OUT/'d3_repeat_check.json');provenance=run.read(run.OUT/'hga_witness_provenance.json')
    lines=['# Round69 — frozen VD-S validation','',
        'This stage changes no solver source, executable or algorithm parameter. It',
        'tests the completed Round68 VD-S integration on a bounded public panel.',
        'D3 is a design-point repeat; D6 is the original design-role long comparison.',
        'E7/S12/N12/D7 are historical public validation, not sealed independent data.',
        'The overall research goal remains unmet: E7/S12 startup losses persist.','',
        'Every arm uses Gurobi13.0.2, Threads1, Seed0, PresolveAuto, zero requested',
        'gaps and the original numerical standards. P-GRB is the original compact',
        'model with native defaults and no HGA, explicit external Start, added',
        'cut or imported bound. K1-R contains only the defined reliability fixes',
        'with full HGA/AM; VD-S is the unchanged one-hot/verified-Start candidate.',
        'All required work and the same whole-run deadline are charged.','',
        '## Completed evidence','',
        f"All 16 performance runs completed, with {resource['experiment_optimizer_calls']} experiment Optimize calls and",
        f"{resource['actual_wall_seconds']:.3f}s paid process wall. No correctness micros or new CTest batch were run.",
        'The identical binary inherits Round68\'s 45-test qualification; this is prior',
        f"qualification, not new cost. Six no-opt P exports took {resource['reference_build_wall_seconds']:.3f}s separately.",
        'No additional repeat, extension, replacement case or parameter change was opened.',
        'See resource_status.json for final QA pass times, which are not a cumulative',
        'account of all earlier read-only audit invocations.','',
        '| Role | Arm | Whole-run cap | Certified | Paid wall | Verified UB | Global LB | Signed absolute gap | HGA wall |',
        '|---|---|---:|---|---:|---:|---:|---:|---:|']
    order=['D3','E7','S12','N12','D6','D7'];arms=['P-GRB','K1-R','VD-S']
    for r in sorted(data,key=lambda r:(order.index(r['id']),arms.index(r['arm']))):
        lines.append(f"|{r['id']}|{r['arm']}|{r['cap']}|{r['certificate']}|{number(r['wall'],3)}|{number(r['UB'],12)}|{number(r['LB'],12)}|{signed_gap(r['signed_absolute_gap'])}|{number(r['hga_seconds'],3)}|")
    lines+=['','The underlying CSV preserves full floating-point precision, including tiny',
        'negative signed gaps within the unchanged numerical tolerance. No bound is',
        'silently clipped to manufacture a certificate or zero gap. HGA subtraction',
        'is attribution only; formal comparisons always use the complete paid run.','',
        '## Frozen practical comparisons','',
        '| Role | Reference | Classification | VD-S minus reference wall | UB delta | LB delta | Gap delta | Bound relation |',
        '|---|---|---|---:|---:|---:|---:|---|']
    for r in sorted(pairs,key=lambda r:(order.index(r['id']),r['reference'])):
        lines.append(f"|{r['id']}|{r['reference']}|{r['practical_classification']}|{number(r['wall_delta'],3)}|{number(r['UB_delta'],9)}|{number(r['LB_delta'],9)}|{number(r['signed_gap_delta'],9)}|{r['bound_tradeoff']}|")
    lines+=['','A both-open gap classification is not a claim that UB and LB individually',
        'improve. Mixed bound changes and certificate status must be read alongside',
        'the raw values. No per-point fastest-variant requirement is introduced.','',
        '## Repeat and startup scope','',
        f"D3 certifies in {repeats['new_wall']:.3f}s versus {repeats['old_wall']:.3f}s in Round68,",
        'with identical binary, initial routes, models/call sequence and final bounds.',
        'This one repeat supports reproducibility of that design-point gain, not',
        'statistical equivalence or a new independent confirmation sample.',
        'E7 and S12 remain P regressions dominated by HGA startup. N12 retains a',
        'material K1-R improvement while staying close to P. See small_validation.md.',
        'A prospective local-descent source/test draft remains isolated under ignored',
        'build/round70_draft; it was not applied, compiled or measured in this stage.','',
        '## D6 timing qualification','',
        'D6/VD-S spent about 550.595s in its HGA loop versus 323.719s for K1-R.',
        'Both report 26383 uncached decoder calls, retain identical initial routes',
        'and have the same 2071-generation best-fitness/improvement history.',
        'The complete offspring history was not retained. This large variation',
        'prevents attributing all observed long-window',
        'differences to the algorithm alone. All actual time remains charged; no',
        'counterfactual time correction, discarded run or extra repeat is used.',
        'A brief CPU sample and a read-only mixed-core topology query do not prove',
        'the cause. No affinity, priority, service or measured source was changed.',
        'See long_validation.md and run13_startup_comparison.json for the completed',
        'endpoint interpretation and the limits of this measurement. Any later',
        'common-core protocol requires newly matched controls for every arm.','',
        '## Long-window results','',
        'D6 at3600 has VD-S gap0.003975678731177851 versus P0.0064055587246548695',
        'and K1-R0.008750414113820076: reductions37.9339% and54.5658%. VD-S',
        'improves both UB and LB over P; the larger contribution is its stronger',
        'bound. The observed long-window P deficit is repaired in this run,',
        'subject to the large startup timing variation above. Its within-run600',
        'checkpoint is worse than P, so no uniform advantage across time is claimed.',
        'D7 at1200 has VD-S gap0.011763976173360113 versus P0.08003438721943765',
        'and K1-R0.017914352795947386: reductions85.3013% and34.3321%. The',
        'important K1/P advantage is retained and strengthened. VD-S and K1-R',
        'use identical initial routes and end at the same UB; their gap difference',
        'comes from the stronger VD-S lower bound. All six long runs remain open.',
        'D7 HGA wall is547.108s/560.423s for VD-S/K1-R, with matching2739',
        'generations,41479 decoder calls and full retained routes. This smaller',
        'timing difference is still paid. VD-S uses seven LP and two MIP calls',
        'versus five LP and one MIP for K1-R; all extra work is charged.',
        'See long_validation.md for original-problem terms, checkpoint limits',
        'and the complete UB/LB interpretation.','',
        '## Starts, witnesses and time provenance','',
        f"The audit covers {starts['actual_mip_decisions']} actual VD-S MIP Start decisions:",
        f"{starts['eligible']} eligible,{starts['accepted']} accepted in native logs, and",
        f"{starts['exact_vectors_observed']} full submitted vectors observed in MIPSOL.",
        f"{starts['controls_checked']} control runs were checked for absence of this explicit Start path.",
        'Submitted/readback vectors are independently checked against all exported',
        'bounds, types, rows and objective. Physical routes and complete interval',
        'coverage are checked separately; zero requested gaps do not imply a rational certificate.',
        'MIPSOL equality is evidence from the qualified C++ observer; complete',
        'native event vectors were not separately retained for a second replay.',
        f"{sum(r['linked'] for r in provenance['records'])}/{len(provenance['records'])} retained HGA initial routes have full-content event provenance.",
        'A canonical route hash and a conservative generation-completion timestamp',
        'establish historical availability; matching objective values alone do not.',
        'Intermediate P incumbents remain native telemetry because their full vectors',
        'were not retained. Synthetic final rows are excluded from earlier checkpoints.',
        'Buffered frontier callbacks receive a conservative setup/tail time correction;',
        'its recorded shifts can understate early progress. Main full-window conclusions',
        'use completed endpoints and are unaffected by this timing limitation.',
        'See within_run_checkpoints.csv and checkpoint_provenance.md.','',
        '## Scope and continuation','',
        'The integrated D6/D7 interpretation is in long_validation.md. This bounded stage cannot establish',
        'general runtime dominance, remove the documented startup regressions, or',
        'substitute for independent validation of a subsequently revised candidate.',
        'A new draft PR preserves this stage; it does not complete the sustained goal.',
        'Reproduction, frozen algorithm, source identity and raw/compact evidence',
        'locations are documented in reproduce.md, algorithm.md and build_v1.json.','']
    publication=run.OUT/'publication.json'
    if publication.exists():
        published=run.read(publication)
        lines+=['Stage complete, draft PR'+str(published['pr_number'])+': '+published['pr_url'],
            'Evidence commit '+published['evidence_commit']+'. Publication metadata and',
            'committed-tree byte checks are retained separately. Overall goal remains unmet.','']
    (run.OUT/'final_report.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Complete-stage report prepared from all16 audited runs')

if __name__=='__main__':main()
