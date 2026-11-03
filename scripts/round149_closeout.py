"""Solver-free final decision, syntax/identity qualification and metered closeout."""
import ast
from round149_common import *


def decide():
    full=read(OUT/'reports/full.json');assert not full['pending']
    assert len(full['formal_arms'])==6 and len(full['comparisons'])==3
    assert full['complete_Native_Optimize']==full['complete_Native_returned']==35
    assert not any(r['certificate'] for r in full['formal_arms'])
    reason=('Retain frozen penalty-product feedback as research only; do not recommend the current '
        'uniform D+PF implementation as a paper enhancement. Three same-domain product LP increments '
        'and block validity are established. K35 gives a real 2.00348% physical-U improvement and '
        '6.69155% smaller signed gap with 0.87754% lower supported L. RB35 instead loses 3.08518% '
        'in physical U, gains 2.26970% in L, and has 4.62638% larger signed gap. This is not a trigger '
        'of the inherited severe double-open reference rule, but it gives up important standalone-D '
        'incumbent value. The one final K20 proof clarification returns identical U, no certificate '
        'on either arm, and a slightly lower PF L. That supplies no proof advantage to justify the '
        'mixed hard-role tradeoffs. All six formal own-H arms use the same new PE and original '
        'matched windows. Keep the valid implementation and complete evidence; preserve stable '
        'R137 and R147\'s previously limited D candidate. This finite known-Seed0 result neither '
        'invalidates the propagation family nor establishes broader robustness. No further experiment is queued.')
    write(OUT/'stage_decision.json',dict(decision='RESEARCH_ONLY_PENALTY_PRODUCT_FEEDBACK_NO_PROMOTION',
        goal_outcome=2,reason=reason,adoption='research_only',recommend_uniform_candidate=False,
        not_a_severe_reference_rule_regression=True,important_RB35_incumbent_cost=True,
        final_K20_question_answer='NO_CERTIFICATION_ADVANTAGE',
        all_experiments_finished=True,no_further_Optimize=True,
        no_RX20_Seed_factor_dynamic_AM_rescue=True))
    print(reason)


def syntax():
    checked=[]
    for path in [*sorted((ROOT/'scripts').glob('round149*.py')),ROOT/'scripts/paper_s2_penalty_feedback.py']:
        ast.parse(path.read_text(encoding='utf-8'),filename=str(path));checked.append(dict(path=path.relative_to(ROOT).as_posix(),SHA256=sha(path)))
    write(OUT/'qualification_final_syntax.json',dict(PASS=True,files=checked,Optimize=0,Native_load=0,compile=0))
    print('PASS syntax for all final Round149 Python helpers')


def local():
    # The delivery helper requires a truly idle budget. Run in this single
    # measured outer frame rather than create a pending nested solver fee.
    import round149_delivery as delivery
    tick=time.perf_counter();syntax();delivery.local();elapsed=time.perf_counter()-tick
    p=OUT/'infra/external_costs.json';value=read(p)
    value['processes'].append(dict(kind='diagnostic',outer_seconds=elapsed,
        label='final_local_semantic_identity_seal_verification',
        basis='One measured idle solver-free validation frame; includes source/PE/DLL/protected-byte and producer-seal checks'))
    if not any(v['label']=='conservative_unmeasured_startup_serialization_allowance' for v in value['processes']):
        value['processes'].append(dict(kind='diagnostic',outer_seconds=5.0,
            label='conservative_unmeasured_startup_serialization_allowance',
            basis='Disclosed allowance for short manual stage/reviewer frame startups and final small metadata serialization; not another solve or historical charge'))
    write(p,value);print(json.dumps(dict(local_seconds=elapsed,budget=budget())))


def resume():
    configure();assert not budget()['unclosed']
    full=read(OUT/'reports/full.json');manifest=read(OUT/'candidate_manifest.json')
    choice=read(OUT/'candidate_decision.json');b=budget()
    previous=OUT/'engineering/continuation_before_scientific_closeout.md'
    if not previous.exists():previous.write_bytes((OUT/'RESUME.md').read_bytes())
    lines=['# Round149 scientific closeout and delivery record','',
        'Scientific work is complete. Decision: **'+choice['decision']+'** (goal outcome2). No further Optimize is queued or authorized for this round. Publication, Draft PR, public recovery and bounded cleanup are recorded below as they complete.','',
        choice['reason'],'',
        '## Actual evidence','',
        'Three saved R146 base-D PF LPs plus one redundant scalar-only control; no baseline reoptimization. Six formal same-new-PE own-H arms on K35/RB35/K20, and one short K20 cap90 health producer. All35 complete/qualification Native calls returned. Four standalone diagnostic LP calls are separate. All6 formal arms remain open with null T_cert. No RX20 full arm, extra seed, cap extension, Shared-S/STOCK/RN/AM or dynamic rescue.','',
        '| Role | D U/L | PF U/L | Interpretation |','|---|---|---|---|']
    by={c['role']:c for c in full['comparisons']}
    for role,interpretation in [('K-35-U','U improves2.00348%, L drops.87754%, signed gap improves6.69%'),
        ('R-B35-S-T2','U worsens3.08518%, L improves2.26970%, signed gap worsens4.626%; severe reference-rule flag false'),
        ('K-20-S','Equal U, neither proves, PF L slightly lower; final proof question answered adversely')]:
        c=by[role];lines.append(f"| {role} | {c['D_U']:.12f}/{c['D_L']:.12f} | {c['PF_U']:.12f}/{c['PF_L']:.12f} | {interpretation} |")
    lines+=['',f"Charged new outer: **{b['G1_seconds']:.9f}s / 18000s**. Necessary build: **{b['separately_reported_seconds']:.9f}s separately**. All own H, arithmetic/construction, solves, qualification failures, analysis and necessary verification are counted once. Nested Runtime/Work and historical fees are not added again. Independent-review/manual-frame/startup allowances are disclosed in infra/external_costs.json. K20 necessary verification extends totals beyond its nominal production cap and is fully paid. Offline authoring and pure publication I/O are separate.",'',
        '## Frozen identities and mechanism','',
        f"Production source: `{manifest['source_commit']}`. PE: `{manifest['production_PE']}`; SHA256 `{manifest['production_PE_SHA']}`. DLL SHA256 `{manifest['DLL_SHA']}`. Executed campaign wrapper is commit840292079 (full hash in identity_index.json); later analysis/publication helpers are separately hashed. Fixed science and delivery identities are in publication_pin.json and actual PR readback; they are not the production source.",'',
        'Bare --round149-penalty-feedback defaults off. The separate research entry/profile are scripts/paper_s2_penalty_feedback.py and config/gi_tbc_penalty_feedback_round149.json; --pf off chooses same-new-PE D. The own-H weighted continuous resource dual floor and upward beta are computed once and appended into all existing state-product upper facets before the first formal solve. No source solve, new column or added root LP; original logical root, AM and proof cover remain. Compatible children inherit the frozen beta; dominated/tiny groups are omitted safely.','',
        'K35 floating LP primal-dual diagnostics are disclosed, not exact rational LP proofs. Exact Fraction diagnostics certify the resource relaxation and production bound direction. Two no-Optimize nonminimal-Start fixture corrections and a mistaken old zero-GD assumption are preserved. Old C++ failure helper versions and executed LP helper bytes were recovered against their original SHA without rebuilding or solving. Current zero-GD matrix evidence explicitly labels its synthetic call wrapper.','',
        'Independent static, pre-full, conditional admissions and final reviews are under review/. Accepted raw producer seals/closeouts are immutable and have not been reentered. final_report.md, mathematical_analysis.md, LP_report.md, manuscript.tex, reports/full.json and verified_U_trajectories.csv supply the scientific record.','',
        '## Workspace and publication','',
        'Use E:/codes/ExactEBRP-work/worktrees/paper-current; all new build/raw/temp/restore assets stay under E:/codes/ExactEBRP-work. Protect E:/codes/ExactEBRP, its preexisting user edits, old untracked data and old history. WORKSPACE_POLICY applies to this and future project prompts. Stable R137 and old entry/profile bytes remain; R147 D keeps its prior limited candidate status.','',
        'The complete preexisting untracked path inventory remains local only. Public protection evidence uses its count/SHA, not two million old path names. New carriers contain necessary incremental evidence, failures, stage decisions and exact source versions; fixed R146 commit/member references avoid copying old large history. No executable, commercial DLL, license or credential is published.','',
        'Verified main has not absorbed R148; use temporary PR base codex/round148-shared-denominator-gd. Do not wait for merge, merge automatically, force push or delete old branches. Next: package/push fixed science, create/read back the English Draft PR, perform one bounded anonymous byte/member recovery with no Native/Optimize/compile, then bounded current-round metadata screening/cleanup. Zero deletion is acceptable; preserve unique raw/failures, necessary PE/DLL, active tree and old history.','']
    (OUT/'RESUME.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Updated scientific RESUME; delivery remains pending')


def run(action):
    configure();assert action in ['syntax','decide']
    assert metered('closeout_'+action,'diagnostic',[PYTHON,'-B',__file__,action],60,120)==0


if __name__=='__main__':
    if sys.argv[1]=='run':run(sys.argv[2])
    else:globals()[sys.argv[1]]()
