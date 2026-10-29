"""Question-led scientific closeout from qualified frozen evidence."""
from round138_common import *
from round138_documents import table

def decide():
    assert not budget()['unclosed']
    full=read(OUT/'reports/full.json');second=read(OUT/'reports/seed1.json')
    assert full['complete'] and len(full['core_pairs'])==8 and len(second['arms'])==4
    assert all(a['performance_eligible'] and a['native_proof_qualified'] and a['H_complete'] for a in second['arms'])
    pairs={r['role']:r for r in full['core_pairs']};s={(r['role'],r['method']):r for r in second['arms']}
    k=pairs['K-20-S'];kb=s['K-20-S','BASE'];ks=s['K-20-S','STOCK']
    assert not k['base_certificate'] and k['stock_certificate'] and not kb['certificate'] and ks['certificate']
    rb=s['R-B35-S-T2','BASE'];rs=s['R-B35-S-T2','STOCK']
    def direction(new,old,upper):
        if abs(new-old)<=1e-7:return 'numerically equal'
        return 'better' if (new<old if upper else new>old) else 'worse'
    seed_discussion=(f'K20 retains the selected certificate benefit: BASE remains open at its 1200-second cap, '
        f'whereas V2 STOCK certifies in {ks["T_cert"]:.6f} seconds at U={ks["U"]:.12g}. '
        f'For RB35-T2, Seed1 STOCK U={rs["U"]:.12g} is {direction(rs["U"],rb["U"],True)} than BASE U={rb["U"]:.12g}; '
        f'STOCK L={rs["L"]:.12g} is {direction(rs["L"],rb["L"],False)} than BASE L={rb["L"]:.12g}. '
        f'The respective signed gaps are {rs["signed_gap"]:.12g} and {rb["signed_gap"]:.12g}. '
        'These observations complement the adverse primary Seed0 result rather than replacing it. '
        'STOCK uses the separately disclosed V2 repair build; all primary model scopes were exactly/native bridged '
        'with scale one. This finite conditional check does not estimate a runtime distribution or establish independent validation.')
    second['discussion']=seed_discussion;write(OUT/'reports/seed1.json',second)
    counts=(sum(r['base_certificate'] for r in pairs.values()),sum(r['stock_certificate'] for r in pairs.values()))
    discussion=(f'The primary certificate count is {counts[0]}/8 for matched GI-TBC and {counts[1]}/8 for stock RLT. '
        'K15 certifies in 33.818227 seconds versus 112.769303 seconds, a substantive difference under the declared rule; '
        'the separate contemporaneous BASE bridge takes 122.579382 seconds. RX20 certifies in 15.340479 versus '
        '20.506462 seconds, below the ten-second substantive threshold. K20 adds a certificate in 101.635385 seconds '
        'while its baseline remains open at cap1200; no baseline convergence time or capped time ratio is invented. '
        'All five n35 primary configurations remain open. RB35-T1 and RX35-T1 improve both U and L, with the '
        'RX35-T1 improvement mostly in L. K35 improves U but loses L. RB35-T2 improves L but materially worsens '
        'U and both gap measures. RX35-T2 improves L but worsens U and signed gap, even though its relative '
        'gap is slightly smaller. The component table shows that RB35-T2 worsens both true G and P_avg; '
        'RX35-T2 improves P_avg but its G increase is larger. No endpoint is hidden by a preferred gap measure. '
        'Both micro controls certify in about one second; their small time difference gives no substantive overhead conclusion.')
    interpretation=('The mathematical budget-product gap and all four real same-domain LP increments are established. '
        'Those increments sometimes yield complete proof benefits, particularly on K20 and K15, but they do not '
        'order finite-budget primal/dual endpoints on the resource-constrained n35 roles. '
        'The selected second Seed retains the K20 certificate benefit and reverses the RB35-T2 U direction. '
        'The known panel and selected second Seed support a focused research conclusion, '
        'not universal dominance, a new unseen benchmark claim, or an additive allocation of runtime benefit.')
    decision=('Keep GI-TBC+stock-RLT research-only. The continuous-block explanation, real-root improvements and '
        'repeated K20 certificate benefit justify retaining the uniform four-row mechanism for further study. '
        'The primary upper-bound regressions on two resource configurations and K35 lower-bound regression '
        'leave insufficient evidence for a default promotion. Preserve the accepted GI-TBC entry/profile/PE '
        'and expose the repaired V2 only through its separate explicit research entry. This decision does not '
        'require every role to win; it reflects the size and practical relevance of the observed opposed endpoints.')
    question=('The next informative question is whether the four inventory rows in the target MIP delay '
        'verified incumbent discovery even when their LP bounds improve. A minimal screen is one Seed0 '
        'BASE/STOCK target-MIP pair on the same saved initial RB35-T2 interval, exact objective/cutoff and '
        'physical input, with no imported Start and at most 120 seconds each. Record first own physically '
        'verified improvement and supported L. Label it a fixed-subproblem diagnostic; do not backfill it '
        'into the completed full runs. Only if that screen supports the mechanism should a separately '
        'named uniform LP-bound-only placement of stock RLT receive a small complete pilot. '
        'This directly tests a primal/dual placement question without another AM grid or broad Seed repetition.')
    write(OUT/'candidate_decision.json',dict(UTC=utc(),study_complete=True,decision='RESEARCH_ONLY',
        candidate='GI-TBC+stock-RLT',delivered_version='V2 coefficient-transport repair',
        full_results_discussion=discussion,interpretation=interpretation,decision_paragraph=decision,
        next_question=question,primary_full_SHA=sha(OUT/'reports/full.json'),Seed1_SHA=sha(OUT/'reports/seed1.json'),
        mathematical_analysis_SHA=sha(OUT/'mathematical_analysis.md'),LP_SHA=sha(OUT/'reports/LP.json'),
        primary_V1_manifest_SHA=sha(OUT/'candidate_manifest.json'),delivered_V2_manifest_SHA=sha(OUT/'candidate_repair_manifest.json'),
        original_default_preserved=True,Optimize=0))
    print('Scientific decision: RESEARCH_ONLY, complete entered comparisons retained')

def main():
    assert not budget()['unclosed']
    full=read(OUT/'reports/full.json');seed=read(OUT/'reports/seed1.json')
    decision=read(OUT/'candidate_decision.json');cost=read(OUT/'cost_report.json')
    assert full['complete'] and decision['study_complete']
    assert all(read(OUT/name)['PASS'] for name in ['qualification/native_coefficients.json',
        'entry_check.json','math/selected_replay.json','local_semantic_check.json'])
    pairs=full['core_pairs'];assert len(pairs)==8 and len(full['new_arms'])==11
    assert len(seed['arms']) in (2,4)
    lp=read(OUT/'reports/LP.json')['rows'];by={(r['role'],r['variant']):r for r in lp}
    saved=read(OUT/'roots/saved_points.json')['cases'];candidate=read(OUT/'candidate_manifest.json');delivered=read(OUT/'candidate_repair_manifest.json')
    snapshot=OUT/'reports/cost_at_science_freeze.json'
    if snapshot.exists():cost=read(snapshot)
    b=cost['experiment'];assert not b['unclosed'] and b['G1_seconds']<=86400
    current=budget();assert not current['unclosed'] and current['G1_seconds']==b['G1_seconds'], 'Refresh accounting after the final experiment before scientific cost freeze'
    if not snapshot.exists():write(snapshot,cost)
    text='# Round138 scientific report and stage decision\n\n'
    text+='Decision: RESEARCH_ONLY. Retain the repaired uniform candidate for focused study and keep accepted GI-TBC as the stable entry.\n\n'
    text+='## 1. Missing information and what is proved\n\n'
    text+='Station VD-P mixtures share one Gini epigraph g but do not automatically preserve products of the cross-station physical budget with that g. Empty departure and loaded return imply Bminus <= tau = sum(Y) = B - sum(return load) <= B, with depot excluded. The four new slack-product rows couple the existing unscaled inventory products J = sum(Z) to this budget; no variable is added. They remain valid for a nonminimal epigraph g, unequal targets/weights/capacities, S = 0 and a collapsed interval. Cumulative pickups are never capped by vehicle capacity.\n\n'
    text+='For the continuous selected-resource set P, full station VD-P plus both products of every defining resource row gives the common-factor product hull by the two-endpoint decomposition. With only four stock rows, this statement covers only the continuous stock-budget product block. It does not claim the hull of integer inventories, routes or the original objective. The heterogeneous two-station witness satisfies lawful ratio aggregate McCormick and violates J <= Bg by 1/8; it is explicitly a product-block witness. These are applications of standard RLT/disjunctive tools. Complete proofs and verified primary references are in mathematical_analysis.md.\n\n'
    text+='## 2. TC, historical GS and AP/IND\n\n'
    text+='The complete retained J2/J3 reference has exact original binary64 lambda_hat = 5404319552844595/36028797018963968 > 1/12. Exact full-matrix witnesses and lower-bound arguments establish the four cells lambda_hat, lambda_hat, lambda_hat + 3/16, lambda_hat + 1/4 = IP optimum for base, stock, TC and both. The old zero-g point is stock-feasible and TC-infeasible; the old TC attaining point violates stock by 3/16. The TC-only cell is limited to this reference/coefficient. All noncomparison auxiliaries retain their freedom; full 583-row and 284/298-bound replay, old state penalty and declared R88 extensions are retained, including zero-inventory loaded return. No unchanged historical enumeration or new tiny Optimize was used.\n\n'
    text+='Historical independent aggregate GS was already implemented and fixed-subproblem tested. With equal targets and tight S, it can also close the same tiny TC gap. The present distinction is shared Z/q consistency in a physical stock direction, which differs from the ratio direction under heterogeneous targets. Current GS controls use safe same-domain S bounds, no reverse-H row and no old bucket architecture. R55 station MC4/VD-P and R135 AP/IND keep their original scope and mixed/negative evidence; AP remains off.\n\n'
    text+='For S bounds valid for the selected continuous stock polytope, endpoint decomposition also proves the ideal conditional inclusion: stock is contained in shared GS, which is contained in the original-variable projection of independent GS (choose its independent W equal to shared W). The present fractional-knapsack bounds satisfy that premise. The heterogeneous witness establishes reverse failure only in the pure product block. This is not a claim about arbitrary route/cutoff-tightened historical GS, strict inclusion of full BRP/TC formulations, or an exact dominance certificate for outward floating matrices.\n\n'
    text+='## 3. Saved points and same-domain original-objective LP gains\n\n'
    text+=table(['Saved role','J - Bg','True G at saved Y'],[[r,v['J_minus_Bg'],v['saved_Y_true_objective']['G']] for r,v in saved.items()])
    text+='The first three motivating points came from fixed R137 carriers; K20 is an additional known control. K35 has integer Y at all 35 stations and still has 78 fractional station selectors. Auxiliary g, true G and the full LP objective remain distinct.\n\n'
    text+=table(['Role','Fresh base L','Stock L','TC L','TC + stock L'],[[r,*[by[r,v]['L'] for v in ['base','stock','tc','tc_stock']]] for r in saved])
    text+=table(['Role','Stock delta L','TC + stock delta L','Common validated U'],[[r,by[r,'stock']['delta_new_base'],by[r,'tc_stock']['delta_new_base'],by[r,'base']['validated_U']] for r in saved])
    text+=table(['Role','Independent GS L','Shared GS L','Stock L'],[[r,*[by[r,v]['L'] for v in ['gs_independent','gs_shared','stock']]] for r in ['K-35-U','R-X20-S-T1']])
    text+='All 20 new LPs use explicit Seed0, Threads1 and the exact original input, T, binary64 lambda, supports, g interval, native cutoff and old rows. Noncomparison auxiliaries reoptimize freely. Four rows/zero columns are the stock delta. Full vectors, quality and original-matrix residual checks are preserved; the reported LP optima are numerical, not rational certificates. Equal objective values do not establish row redundancy or polytope equality.\n\n'
    text+='## 4. Complete method, finite second Seed and exploration\n\n'
    text+='There are eight physical/objective configurations on six inputs and sixteen nominal core method positions. Eight exactly matched accepted R137 baselines are reused. Eleven new Seed0 positions comprise eight uniform stock candidates, a contemporaneous frozen-PE K15 bridge, and two 90-second micro controls. Full own H and all online construction/search/proof costs are paid independently. Resource-panel rho is 1 with original exact lambda = 1/Omega; physical T and compute cap are separate. No cross-method/Seed/weight solution, bound, tree or Start is transferred.\n\n'
    text+=table(['Role','Base U','Stock U','Base L','Stock L','Base cert s','Stock cert s'],[[r['role'],r['base_U'],r['stock_U'],r['base_L'],r['stock_L'],r['base_T_cert'],r['stock_T_cert']] for r in pairs])
    text+=table(['Role','Base signed gap','Stock signed gap','Base relative gap','Stock relative gap'],[[r['role'],r['base_signed_gap'],r['stock_signed_gap'],r['base_relative_gap'],r['stock_relative_gap']] for r in pairs])
    text+='Open certificate times are null. A timeout is not a known convergence time. For both-certified pairs the substantive threshold is max(10 seconds, 10% of the smaller certificate time). Qualified T_produce/T_cert include full online production and seal; T_verify is separately retained, and T_total is also in the full arm data. Native process trace time is a separate diagnostic clock. G/P_avg/S and complete phase/effort fields are retained in reports/new_arms.csv and pairs.csv.\n\n'
    text+=decision['full_results_discussion']+'\n\n'
    controls=[a for a in full['new_arms'] if a['stage'] in ['contemporaneous-baseline-bridge','micro']]
    text+=table(['Control','Method','Certificate s','T produce s','U','L'],[[a['role'],a['method'],a['T_cert'],a['T_produce'],a['U'],a['L']] for a in controls])
    text+='The K15 bridge initially failed only the postreader lifecycle version adapter after normal sealed native completion. Its failed fee/logs remain. The reviewed strict modern adapter repair reused that sealed run and performed verification only; no native repetition or tolerance relaxation occurred. Pre-Optimize setup/parser/cutoff preflight failures likewise remain in the diagnostic carrier. The actual stored native cutoff was used after detecting that Python physical U reconstruction differed by one ULP.\n\n'
    bridge=next(a for a in controls if a['stage']=='contemporaneous-baseline-bridge')
    text+=f'The bridge recorded T_verify = {bridge["T_verify"]:.6f} seconds, an elapsed closeout interval that includes the postreader repair delay. Actual verification-process wall costs are separately metered in fees; the delay is not relabeled as native computation.\n\n'
    text+='Before any Seed1 Optimize, actual native readback found that the V1 tiny-alpha qualification file lost negative 1e-13 Y coefficients on import. Such loss can invalidate an upper row; the failure is retained and its 4.3128927000798285 seconds are charged. V2 fixes only these new rows by exact positive power-of-two scaling for nonzero slopes below 1e-12, including the already outward RHS; finite guards reject unrepresentable transport. Seven actual Native domains pass after repair. All 33 used primary STOCK calls (25 unique models) have positive interval endpoints at least 0.21232492258182034, and their original Native coefficient maps/RHS were checked exactly; the changed branch is absent. The 20 real LP domains also remain unchanged. V1 science/source/PE and the unused original Seed1 registration remain retained. The new Seed1 registration and private scaled-row reader were independently accepted after this bridge. There was no full primary rerun, retagging, tolerance change or bound backfill.\n\n'
    text+=seed['selection_rationale']+'\n\n'
    text+=table(['Selected role','Method','Seed','Certificate s','U','L'],[[a['role'],a['method'],a['seed'],a['T_cert'],a['U'],a['L']] for a in seed['arms']])
    text+=seed['discussion']+'\n\n'+decision['interpretation']+'\n\n'
    text+='Offline handling-product checks found no violation at the four saved stock LP optima. When mT/(pickup+drop) >= B, local VD-P already implies those handling products; RX20 and RX35-T2 satisfy this sufficient condition. Other nonviolations are point observations. The four GS optimum witnesses also satisfy product rows for a tighter safe lower S bound. These zero-Optimize checks did not justify a second full variant. No broad AM/Seed/ablation matrix, P/PS rerun, or unchanged tiny enumeration was performed. TC+stock remains an LP comparison rather than an untested full algorithm result.\n\n'
    text+='## 5. Adoption, preserved entry and next question\n\n'
    text+=decision['decision_paragraph']+'\n\n'+decision['next_question']+'\n\n'
    text+=f'Primary measured STOCK source is {candidate["source_commit"]}; PE SHA256 is {candidate["production_PE_SHA"]}. Delivered/Seed1 V2 source is {delivered["source_commit"]}; PE SHA256 is {delivered["production_PE_SHA"]}. The explicit candidate entry is scripts/paper_s2_stock_rlt.py with config/gi_tbc_stock_rlt_round138.json. The stable scripts/paper_s2.py, config/gi_tbc_round137.json, compatibility config/paper_s2.json and frozen R137 PE retain their bytes and identity. Production C++ defaults stock RLT off. The new entry is separately validated and marked research-only.\n\n'
    text+='## 6. Cost, validation and finite delivery\n\n'
    text+=f'At this scientific freeze, charged new outer experiment computation is {b["G1_seconds"]:.6f} seconds ({b["G1_seconds"]/3600:.6f} hours); remaining allowance is {b["remaining_G1_seconds"]:.6f} seconds out of 86400. Native complete outers contribute {b["by_category"]["native"]:.6f} seconds and diagnostics {b["by_category"]["diagnostic"]:.6f} seconds. Qualification includes the {cost["qualification_reclassification_count"]} zero-Optimize native exporter processes ({cost["qualification_reclassification_seconds"]:.6f} seconds), charged once. Reused baselines retain their original complete costs in the comparisons and incur no new fictitious computation. Nested H/LP/MIP/Work is never added twice.\n\n'
    text+=f'At the same freeze, disjoint fee-recorded ordinary work after qualification reclassification is {cost["fee_ordinary_net_seconds"]:.6f} seconds; additional disjoint analysis/document/delivery stages recorded so far are {cost["additional_disjoint_ordinary_steps_seconds"]:.6f} seconds. Final delivery cost_report.json includes subsequent recorded steps. Interactive reading/writing is not precision-metered, and offline point checks overlapping native time are not added again.\n\n'
    text+='Independent reviews cover math, implementation, LP/full admission, the postreader amendment, selected Seed1 admission and final integration. The native seven-domain coefficient/RHS readback has zero Optimize; the new entry dry check, exact tiny replay and additive local sealed-run semantic checks likewise have no Optimize or commercial DLL load. Original full postreaders retain H/Start/proof qualification; the additive local replay is not mislabeled as a new independent full semantic proof.\n\n'
    text+='Scientific artifacts include the incremental manuscript/PDF, exact tiny dependencies, necessary new source/raw/failed-attempt carriers and their per-member indices. source_publication.json and carrier_manifest.json bind actual source/input bytes. The final publication pin, open Draft PR readback, bounded anonymous new-carrier byte/member recovery and current-round preview-only cleanup are recorded separately in publication_pin.json, PR_delivery.json, public_restore_receipt.json and cleanup_receipt.json. Those late metadata records are authoritative for delivery state; they do not trigger recursive repackaging of already fixed science. Public byte readability does not imply a full public semantic replay. R137 historical recovery limitations remain unchanged. No old round is restored wholesale or deleted, and no commercial native asset or credential is published.\n'
    (OUT/'final_report.md').write_text(text,encoding='utf-8',newline='\n')
    write(OUT/'report_bindings.json',dict(UTC=utc(),report_SHA=sha(OUT/'final_report.md'),
        decision_SHA=sha(OUT/'candidate_decision.json'),full_SHA=sha(OUT/'reports/full.json'),
        LP_SHA=sha(OUT/'reports/LP.json'),Seed1_SHA=sha(OUT/'reports/seed1.json'),
        cost_snapshot_path=snapshot.relative_to(ROOT).as_posix(),cost_snapshot_SHA=sha(snapshot),Optimize=0))
    print('Six-question scientific report generated from complete qualified data')

if __name__=='__main__':globals()[sys.argv[1] if len(sys.argv)>1 else 'main']()
