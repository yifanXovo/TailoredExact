"""Write the finite result/review/PR narrative after the actual final checks."""
from round130_common import *
from collections import Counter


def table(headers, rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join(
        '| '+' | '.join(map(str, row))+' |\n' for row in rows)


def fmt(value):
    return 'null' if value is None else f'{value:.6f}'


def run():
    o = read(OUT/'observations.json')
    s = read(OUT/'stratified_summary.json')
    d = read(OUT/'scientific_decision.json')
    independent = read(OUT/'review/final_independent_evidence.json')
    pdf = read(OUT/'review/pdf_visual_review.json')
    assert s['execution'] == 'COMPLETE' and len(o['arms']) == 24 and len(o['pairs']) == 30
    assert independent['status'] == 'PASS' and pdf['status'] == 'PASS'
    assert pdf['PDF_SHA'] == sha(OUT/'manuscript.pdf')
    assert (OUT/'review/final_independent_review.md').is_file()
    methods = ['P', 'PS', 'S2', 'S2R']
    counts = {m: sum(a['certificate'] for a in o['arms'] if a['method'] == m) for m in methods}
    negative = [dict(id=a['id'],seed=a['seed'],method=a['method'],U=a['U'],L=a['L'],
        signed_U_minus_L=a['U']-a['L'],tiny_negative_gap_within_original_tolerance=a.get('tiny_negative_gap_within_original_tolerance'),
        raw_claimed_U=a.get('raw_claimed_U'),raw_claimed_L=a.get('raw_claimed_L'),
        raw_claimed_strict_certificate=a.get('raw_claimed_strict_certificate'),
        certificate=a['certificate'],certificate_qualified=a['certificate_qualified'])
        for a in o['arms'] if a['U'] < a['L']]
    write(OUT/'numeric_policy_impacts.json',dict(scope='All24 qualified endpoint signed gaps; detailed raw native return/call gaps remain in each sealed journal',
        original_nonzero_certificate_window=[-1e-7,1e-7],negative_endpoints=negative,
        L_clipped=False,new_tolerance_introduced=False,
        same_input_physical_bound_consistency=read(OUT/'cross_arm_bound_consistency.json')['status'],
        no_global_rational_or_accumulated_rounding_error_claim=True))
    clocks = table(['Known role', 'Seed', 'Method', 'Certified', 'T_produce', 'T_verify', 'T_total', 'T_cert', 'U', 'L', 'signed U-L'],
        [[a['id'], a['seed'], a['method'], a['certificate'], fmt(a['T_produce']), fmt(a['T_verify']),
          fmt(a['T_total']), fmt(a['T_cert']), f"{a['U']:.15g}", f"{a['L']:.15g}", f"{a['U']-a['L']:.15g}"] for a in o['arms']])
    directions = table(['Known role', 'Seed', 'Comparison', 'Class', 'Direction', 'Left minus right seconds', 'Materiality'],
        [[q['id'], q['seed'], q['left']+'/'+q['right'], q['classification'], q['direction'],
          fmt(q['left_minus_right_seconds']), q['materiality'] or 'N/A'] for q in o['pairs']])
    type_rows = []
    for left, right in read(OUT/'experiment_manifest.json')['pairs']:
        rows = [q for q in o['pairs'] if q['left'] == left and q['right'] == right]
        assert len(rows) == 6
        type_rows.append([left+'/'+right, 6, dict(Counter(q['classification'] for q in rows)),
                          dict(Counter(q['direction'] for q in rows)),
                          sum(q['classification'] == 'BOTH_CERTIFIED' for q in rows)])
    typed = table(['Type', 'Shared matched groups', 'Certification classes', 'Directions', 'Both-certified ratio denominator'], type_rows)
    exposure = table(['Known role', 'Seed', 'S2 splits', 'S2 partial target calls', 'S2R splits', 'S2R native calls', 'Same effective root'],
        [[x['id'], x['seed'], x['S2_splits'],
          next(c['partial_target_calls'] for c in o['costs'] if c['group'] == x['group'] and c['method'] == 'S2'),
          x['S2R_splits'], next(c['actual_native_calls'] for c in o['costs'] if c['group'] == x['group'] and c['method'] == 'S2R'),
          x['pure_outer_package_attribution_eligible']] for x in o['differences']])
    source_commit = read(OUT/'preformal_source_provenance.json')['source_commit']
    frozen = read(OUT/'E3_frozen.json')
    text = f'''# Round130 final report

Execution: **COMPLETE** — 24 independently paid formal arms, six matched groups, three already-known inputs and all 30 prespecified typed comparisons. Scientific label: **`{d['tag']}`**.

{d['claim_scope_assessment']['reason']}

## One adopted version and finite questions

The sole proposed paper method is GI-TBC (uniform pair-support implementation, MS2), short ID S2. This is the already selected E2 `--round127-mode ms2` algorithm, preserved by E3. R129's five passed conditions are a settled starting point. This round neither repeats candidate selection nor promotes PS or S2R. The repository ENS-C default is unchanged. Historical full three-station M-B and ENS observations retain their original labels; evidence_migration.csv records their separate roles and actual identities.

P is the primary cold original-compact benchmark. PS independently pays complete H, maps/checks every original-compact Start column and submits/reads back its own full vector before the original MIP. S2/PS measures the remaining complete backend/representation/control increment. S2R keeps the pair-only strengthened inclusive root and pays its own full pre-LP Start validation, one root LP and one root MIP. S2/S2R measures the exposed outer package when actual H, domain, settings and effective roots agree. S2R/PS also changes representation, LP preprocessing and cutoff domain. No comparison identifies one isolated cut or split formula.

The roles are UC-B20-B, UC-C20-U and UC-B30-S, original R129 bytes, Q vectors and physical T=7200. They deliberately cover a known splitting role, another nonzero-certified risk and an open shortage risk. They are not unseen validation problems. Two Seeds are finite path observations, not extra problem instances. All four methods use the frozen E3, original Gurobi 13.0.2 DLL, lambda=.15, pickup/drop60, H_seed20260626, one native thread, original affinity and defaults, zero requested MIP gaps, unchanged tolerances and complete 1200-second caps. The 30-second shutdown reserve and 6/2-second native/hard-stop offsets remain. No H, witness, bound, Start, basis, tree or cache is borrowed across arms. No normal result was retried.

## Complete comparison accounting

Certification counts across six role/Seed observations are {counts}. The five types each have the same six matched groups and three distinct input denominator. Entries share observations; they do not form 30 independent trials. Ratios and their conditional summaries use only the explicit both-certified intersection. Unknown T_cert remains null. Open U/L/gap is supplementary and never a certification Win.

{typed}
Strict Win/Lose uses full-precision T_cert, or the only qualified certificate. Materiality is a separate symmetric description: slower minus faster >= max(10 seconds, .10*faster). A strict small timing loss can therefore be TIME_CLOSE. No cap imputation, best-of-Seed choice, remaining-time prediction or population claim is made.

## Actual startup, root and control exposure

All complete H/action/inventory/capacity-assigned fleet comparisons agree: **{s['all_actual_same_H']}**. All S2/S2R effective-root comparisons qualify: **{s['all_actual_same_effective_root']}**. The source facts and full-matrix differences retain objective, column order/type/bounds, duplicate rows, initial interval, cutoff and actual native settings. P/PS use the identical original compact with no project cutoff or S2 strengthening. PS's native Start incumbent adoption is separate from feasibility and attribute readback.

{exposure}
The recorded H witness attains B20's eventual objective 0.5773330699702928 before proof. That fact is not an optimality certificate. R129_B20_coverage_example.md gives the old arm's three natural splits and actual closure sources, with the semantic-row domains and binary64 analytic premises. That historical example was never supplied to a formal producer. New S2 observations are reported on their own evidence; natural split counts alone cannot establish net runtime gain.

mechanism_costs.csv keeps actual H completion, model and mapping phases, native LP/MIP time/Work/nodes, call kinds, submitted Starts, root scope, pair/triple rows, split/target exposure and first retained own final-U witness availability. Missing subclocks stay unknown. Existing native Work is explanatory, not a new budget. closure_sources.csv binds each semantic proof-closure row to its actual interval, cutoff and analytic regional floor. It is not read as inclusive physical infeasibility. Signed negative gaps and their qualified impacts are retained.

numeric_policy_impacts.json records {len(negative)} actual negative qualified endpoint gaps. In this panel, C20 Seed1 S2 and S2R each retain U-L=-1.4988010832439613e-15 with their original L unchanged. They satisfy the original signed window; no new tolerance, LB clipping or rational-exactness claim is introduced. The original raw top-level claims remain separate from these qualified source/return/coverage endpoints. All same-input cross-arm physical-bound consistency checks pass without transferring a solution, U or certificate.

## Qualification and source identity

Frozen source commit: `{source_commit}`. E3 PE SHA256: `{frozen['PE_SHA']}`. Original E2 SHA256: `{E2_SHA}`. Original DLL SHA256: `{DLL_SHA}`. E3 is a distinct binary and E2 retains its original bytes.

The only production changes are the default-off unique `s2-root` mode predicates (pair-only plus inclusive-root semantics) and PS-only actual MIPFocus/Cuts/NumStart readback evidence. P, ordinary S2, full M-B and full MD-R source behavior are preserved. Qualification compares complete small/medium E2/E3 models, columns/types/bounds/objective/settings/H and a same-byte renamed file. It checks shared/fallback S2R differences, the equal-cutoff fixture, complete original-compact P/PS identity and actual independently paid PS and nonzero S2R native chains. Existing heterogeneous-capacity, empty-vehicle and loaded-return Start witnesses plus ten rejection fixtures and R128 zero/tiny-positive/open-return contracts are reused within their stated scopes. No historical full campaign or tuning was repeated.

The initial input-serialization assertion, sparse setup failure and postseal PS Seed1 reader failures are preserved. The reader repair restores the original raw PS strict-certificate equality and distinguishes Seed0-hardcoded journal metadata from actual Seed1/computed source-return-cover evidence. Eight derived files from the failed postseal check were moved with a guarded receipt; native sealed bytes were not rewritten and PS was not rerun. Qualification read-only resumption and the originally unstarted S2R chain are recorded separately. These are not formal retries.

Final independent review 01 found a descriptive support-row count error: the frozen qualification helper's shape classifier also counted cross-vehicle unique-service rows for M=2. Complete duplicate-preserving model equality was already correct. The post-formal summary now uses the inherited R129 single-vehicle classifier: B20/C20 have 380 actual pair rows, B30 has 1305. Original summaries, the failed review and unchanged qualification report are retained with review/support_count_correction/addendum.json and .md; the S12 qualification descriptive pair-cover count changes from 12 to 0, with 132 conditional rows unchanged. One correction attempt stopped at the inherited exclusive-create CSV writer; its failure and fee remain, and a hash-guarded derived-summary recreation succeeds. No raw, native run, algorithm, parameter, certificate or scientific decision changes. A new independent review performs the complete checks after this correction.

## Retained historical positives and negatives

R129 remains 30 arms/10 groups/30 shared comparisons: four new inputs at selection time plus a separate protection input. Per Seed new-problem P/MB/MS2 certification counts are 1/2/2, also 1/2/2 when requiring both Seeds. C20 MS2 saves 147.147 and 151.415 seconds against full MB; both protection certificates remain. B20's MB/MS2 H already has the eventual objective and each naturally splits three times. C15 and B30 are open for all three methods and both Seeds. B30 Seed1 MS2 U/gap is worse than MB, with the opposite Seed0 direction; C15 Seed1 is slightly worse in U as recorded.

R128 full three-station MD-R/MB differs by less than a second on two certified roles, has no split in the three roles, and retains its timing reversal and open K3. It is historical control evidence, not final S2's answer. R127 legally selects q2 P-tuned, then certifies 0/3 held-out roles versus default P 1/3; no retuning or per-instance default/tuned choice follows. Its C_G/C_R evidence is for the three-station predecessor, not a final-S2 single-component runtime theorem. R112–R115 already establish independently paid same-H compact controls with mixed outcomes; this round does not claim to invent that control. Historical V35/V50/V60 observations do not validate final S2 at those sizes.

## Actual independent and document review

A separate internal executor reviewed the frozen PS/S2R qualification and admission before performance. After all 24 arms, that executor independently recomputed every one of the 30 directions/materiality labels and five six-group denominators, checked the actual evidence within its recorded physical/model/Start/source-return-cover scope, and issued review/final_independent_review.md plus evidence. It also replayed actual nonempty fleet evidence. The precise samples/full checks are enumerated there. This is finite internal review, not external replication or a global rational certificate.

The maintained full manuscript and R125 mathematical/H/controller appendices now identify S2 as the sole method, uniformly pair-only. Historical tables keep original identities and numerical authorities. The current abstract, introduction, method/entry, evidence gateway, R129 chronology, new Section6.10, contribution matrix, discussion/conclusion and appendix version notes are updated. The actual PDF was exported through the existing pipeline and affected pages were rendered and visually inspected; review/pdf_visual_review.json binds that inspection to the delivered PDF. Old unaffected historical pages were not all revalidated.

## Finite delivery and stop

Source and result tables, exact argv/input and E3 bindings, qualifications/failures, all current raw/model/Start/bound evidence, claim decision, version migration and the complete manuscript/PDF are delivered as a bounded set. Current carriers are lossless and exclude native software, licenses, credentials, fonts and external full papers. The sole historical raw dependency is one labelled B20 coverage arm. One science-commit anonymous empty-root recovery and guarded owned duplicate cleanup will be appended only after their actual receipts; no further experiment is authorized.

All substantial children use nonoverlapping outer meters under39600 seconds, with build/incremental qualification under3600 and explicit setup/final metadata allowances. Nested H/LP/MIP seconds are not added again. Author preparation concurrent with a formal outer window is not billed as another wall interval; interactive waiting is not claimed as CPU. Final closure is in resource_accounting.json. The study ends with accurate finite positive, close, reverse and open results; no extra Seed, role, tuning, long window or component selection is authorized.

## Every formal arm

{clocks}
## Every typed comparison

{directions}
'''
    (OUT/'final_report.md').write_text(text, encoding='utf-8')
    actions = '''# Round130 review actions

The method adoption is settled by the user's instruction after R129 passed. This review changes paper attribution scope, not candidate identity or repository defaults.

| Review obligation | Actual evidence |
| --- | --- |
| Independent preformal mode/Start/root/source/budget admission | review/preformal_independent_review.md; review/performance_admission.json |
| Small/medium full E2/E3 bridge, renamed same-byte file | qualification/zero_qualification.json; qualification/filename_identity_addendum.json |
| Shared/fallback pair-only inclusive-root differences and equal-cutoff fixture | qualification/zero_qualification.json; qualification/native_qualification.json |
| Original-compact full Start and heterogeneous/empty/loaded contracts | qualification/native_qualification.json; qualification/inherited_contracts.json |
| Retained failed reader facts and no native PS repeat | qualification/reader_failure01; closed qualification fee receipts |
| All 24 independent formal endpoints and all 30 shared typed comparisons | campaign/group01..06; arms.csv; pairs.csv; stratified_summary.json |
| Actual same-H/full-root/Start/exposure/cost | same_H.csv; actual_method_differences.json; mechanism_costs.csv; closure_sources.csv |
| Independent final arithmetic, evidence chains and nonempty fleet replay | review/final_independent_review.md; review/final_independent_evidence.json |
| Disclosed descriptive support-count correction, preserved failure and unchanged native evidence | review/support_count_correction/addendum.json; review/support_count_correction/before/ |
| Single adopted version with predecessor/selection/protection/diagnostic layers | paper_version_manifest.json; evidence_migration.csv; paper_method_config.json |
| Full maintained source and actual affected-page PDF inspection | manuscript_lineage.json; pdf_export.json; review/pdf_visual_review.json |

The source predicates, numerical policies and full performance plan were frozen before formal outcomes. The author repairs only explicit reader/reporting/serialization issues and preserves original failures and sealed bytes. Normal open, Lose and no-split observations do not trigger recovery. All scope restrictions in claim_decision.md are carried into the abstract and contribution discussion.

Publication scan, one anonymous science-commit recovery, guarded duplicate cleanup and final normal stacked Draft-PR readback are recorded after those operations actually occur. No historical campaign restoration or subsequent experimental follow-up is authorized.
'''
    (OUT/'review_actions.md').write_text(actions, encoding='utf-8')
    body = f'''The paper now has one proposed method: GI-TBC's uniformly fixed pair-support MS2 implementation (S2), adopted after R129 passed. This PR preserves that algorithm, adds the default-off `s2-root` control and PS-only parameter evidence, and completes the fixed 24-arm same-start/outer-control panel. It is stacked on `codex/round129-uniform-pair-support-confirmation` at `{BASE}`.

The scientific outcome is `{d['tag']}`. {d['claim_scope_assessment']['reason']}

- Three already-known R129 inputs, two Seeds, four independently paid workflows and all 30 prespecified typed comparisons; no tuning, regenerated inputs, extra Seed or formal retry. Qualified certification counts across six observations: {counts}.
- P stays the primary cold compact benchmark. PS uses its own paid complete H and full original-compact Start. S2R uses a pair-only inclusive root, own pre-LP Start validation and one LP plus one MIP. Actual same-H and effective-root facts, split/target exposure, Start adoption and full costs are retained.
- E2 is unchanged. Every formal arm uses frozen E3 `{frozen['PE_SHA']}` and the original DLL. Full small/medium and renamed-file bridges, shared/fallback root differences and native qualification precede the serial panel.
- Two separate internal reviews, all 30 independently recomputed directions/denominators and actual physical/Start/source-return-cover checks pass. This is finite internal review, not external replication or a global rational proof.
- The full manuscript/PDF adopts S2, preserves R125 derivations and labels historical full-MB/ENS evidence accurately. R129 open/reverse endpoints, R128 timing/no-split limits, adverse P-tuned holdout and earlier mixed same-H outcomes remain visible. Affected PDF pages were actually inspected.

One science-commit anonymous empty-root recovery and guarded owned duplicate cleanup will be appended only after their actual receipts; no further experiment is authorized.

Review entry points: `results/unified_exact_round130/claim_decision.md`, `final_report.md`, `paper_version_manifest.json`, `arms.csv`, `pairs.csv`, `actual_method_differences.json`, `mechanism_costs.csv`, `review/final_independent_review.md` and `manuscript.pdf`. Historical full-MB numbers are not relabelled as S2 and repository defaults remain unchanged. This is a Draft research PR; no merge or force push.
'''
    (OUT/'PR_BODY.md').write_text(body, encoding='utf-8')
    print(json.dumps(dict(report_written=True, execution=s['execution'], tag=d['tag'], counts=counts)))


if __name__ == '__main__':
    run()
