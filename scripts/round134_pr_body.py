"""Prepare an English, reviewable PR body after actual delivery checks; never publish."""
from round134_common import *
import re,collections

def main():
    assert len(sys.argv)==3
    science,metadata=sys.argv[1:]
    assert all(re.fullmatch('[0-9a-f]{40}',c) for c in (science,metadata))
    s=read(OUT/'reports/summary.json');C=read(OUT/'reports/C/arms.json');pairs=read(OUT/'reports/C/pairs.json')
    D=read(OUT/'reports/D/six_points.json');roots=read(OUT/'reports/roots.json')
    assert s['C_completed']==32 and s['D_completed']==4
    public=read(OUT/'public_restore_receipt.json');assert public['passed'] and public['commit']==science
    assert public['Optimize']==public['compile']==public['vendor_DLL_loads']==0
    qa=read(OUT/'review/pdf_visual_QA.json');assert qa['status']=='PASS' and qa['PDF_SHA']==sha(OUT/'manuscript.pdf')
    review=read(OUT/'review/final_integrated_review.json');assert review['passed']
    url='https://github.com/yifanXovo/TailoredExact/blob/'
    def link(label,path,commit=science):return f'[{label}]({url}{commit}/results/unified_exact_round134/{path})'
    counts=s['C_certificates'];den=s['C_denominators']
    text='''The original objective is nonnegative. An own complete physically feasible fleet with exact objective zero therefore proves optimality independently of a rejected native bound or search tree. This change adds the same exact-stock and complete-fleet finalizer to P, PS and S2, and keeps native rejection and dependent-domain restoration visible. Near-zero positive values retain the separate epsilon policy. Normal positive native/outer certificates remain active. The default ENS-C entry, production matrices, H, pair-only support, controller and numerical tolerances are unchanged.

This is stacked on PR #195, `codex/round133-native-reliability-and-objective-gap`, verified base `39043b15b3cceae2cab14a3fbaec39e2b16339ce`. The source/PE and all argv, input, Seed, repeat, method-order and full-clock policies were frozen before the new comparisons. No healthy native arm was repeated and no result was selected out because it was adverse or open.

### Final-version evidence and retained limits

'''
    text+=f"- All 32 fixed C positions completed: S2 {counts['S2']}/{den['S2']}, cold P {counts['P']}/{den['P']}, fully paid-start PS {counts['PS']}/{den['PS']} qualified certificates. There are 14 S2/P and 4 S2/PS matched groups. This is targeted confirmation on six known roles, not a holdout. Historical R132 counts of 17/24, 9/24 and 4/12, and the separate R133 repair/bridge evidence, keep their original versions and denominators.\n"
    for control in ('P','PS'):
        pp=[p for p in pairs if p['right']==control]
        text+=f"- S2/{control} classes: {dict(collections.Counter(p['class'] for p in pp))}; directions: {dict(collections.Counter(p['direction'] for p in pp))}. Certified-time size uses the prespecified max(10s,10% of faster time) threshold outside the micro panel. All four micro repetitions retain their absolute times; open caps are never certification times.\n"
    text+=f"- Normal positive K-15-S proofs and actual UC-B20-B splits/child-target/cache paths remain exposed. {s['independent_certificate_count']} final observations use the independent zero proof, including {len(s['rejected_native_independent_certificates'])} whose native source stays rejected. Positive-objective35-station unresolved endpoints and every P/PS advantage remain in the full tables. Hidden native numerical causes remain UNKNOWN where previously unresolved.\n"
    text+="- Both known X-35-B paid-start reversals are substantive: S2 takes 17.606/18.277s versus PS 7.251/7.196s at Seeds 0/1. All four K-35-U arms remain open; at Seed0 P has the better primal endpoint while S2 has the better lower bound, and at Seed1 S2 has both better endpoints. The six-role panel gives no evidence of a broad regression; it does not establish universal speed dominance.\n"
    text+=f"- Four new S2 weight runs plus two reused C baselines give all six prescribed points; {sum(r['certificate'] for r in D)}/6 are certified. The same lambda is checked in argv, own H, physical objective, loaded model objectives/scopes, Starts/bounds and reader. Tradeoff statements use effective rho=lambda*Omega and accepted original-objective gap errors, not feasibility tolerance. Uncertified incumbents alone do not establish exact optimal monotonicity.\n\n"
    text+='### Inventory threshold-count research\n\n'
    text+='A separate all-station inventory-budget count gives one valid aggregate Gini-numerator row, with exact threshold decisions, actual loaded ratio coefficients and downward-rounded nonnegative state coefficients. It adds no production variables or DP and is not enabled in C/D. On the complete J2/J3 tiny joint references plus old state penalty and full R88 CDF/product extensions, exact old/new witnesses pass all583 original rows and284/298 variable bounds. The LP improves by exactly3/16 to lambda_hat+3/16, closing75% of the old1/4 gap and leaving1/16 below the integer optimum. This is a result on the named references, not a dominance theorem for every historical closure.\n\n'
    text+='The two unchanged real-root domains each completed all three continuous LP layers. '
    text+=' '.join(f"{r['role']}: {r['L0']:.9f} -> {r['L_old']:.9f} -> {r['L_old_TC']:.9f}." for r in roots)
    text+=' These are recorded numerical OPTIMAL LP observations, not new rational global proofs. Neither root has a reliable TC increment after retaining the old state-penalty control; the old optimum already satisfies TC. The finite exploration stops with this negative evidence, without adding roots, Seeds or a production mechanism.\n\n'
    text+='### Manuscript, review and finite reproduction\n\n'
    text+='The paper now follows problem, shared structure, algorithm, complete-method evidence and interpretation, with maintained full model/algorithm appendices, a complete supplement, weight and count-bound figures, and scoped literature/provenance disclosures. The advisor-review judgment supports a TRE/EJOR-oriented discussion of the integrated method; it does not claim acceptance, model invention, first Gini/fairness use, universal native reliability or a substantially closed higher-OR gap. Precise external same-problem heuristic citation/data provenance and the named full-text comparison questions remain minimal author work before submission.\n\n'
    text+=f"The same independent reviewer accepts the final finite integration. Actual PDF rendering/visual QA passes for the recorded {qa['page_count']} pages within its stated inspection scope. The one owned anonymous recovery passes all36 current positions, exact tiny mathematics and current root coefficient/residual checks, with Optimize/compilation/vendor-DLL loads0 and no local raw/source fallback. Only the unchanged fixed tiny carrier and explicitly declared helpers/inputs are inherited; no old whole campaign is restored. Source-byte capsules, SHA/member indices, preserved failures and measured clocks are included.\n\n"
    account=budget();text+=f"New computation is {account['G1_seconds']:.6f}/57600 seconds at this preparation, with nested H/LP/MIP/Work not added. Actual postverification, writing/PDF and delivery/recovery are reported separately. Three original dirty-file hashes, four original native assets and the frozen current source/PE/DLL are protected. No cleanup of unique raw/failures or old worktrees is performed.\n\n"
    text+=f"Fixed science payload: `{science}`. Later metadata records actual delivery without rewriting or recursively repackaging the science snapshot.\n\n"
    text+='- '+link('Complete paper','manuscript.md')+' and '+link('PDF','manuscript.pdf')+'; '+link('full supplement','supplement.md')+'\n'
    text+='- '+link('Five scientific answers','final_report.md')+'; '+link('complete C table','reports/C/arms.csv')+'; '+link('weight points','reports/D/six_points.csv')+'\n'
    text+='- '+link('Independent zero proof','independent_proof.md')+'; '+link('TC derivation and old controls','tc_note.md')+'; '+link('finite reproduction','reproducibility.md')+'\n'
    text+='- '+link('Final integrated review','review/final_integrated_review.json',metadata)+'; '+link('actual public recovery','public_restore_receipt.json',metadata)+'\n\n'
    text+='Keep this PR Draft and unmerged. No automatic merge, force push, default-branch change, email or journal submission is authorized.\n'
    path=OUT/'delivery/pr_body.md';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
    write(OUT/'delivery/pr_create_arguments.json',dict(repository_full_name='yifanXovo/TailoredExact',
        base='codex/round133-native-reliability-and-objective-gap',head='codex/round134-paper-ready-s2-and-count-bound',
        title='Round134: paper-ready S2 certificates, final-version evidence and inventory-count bounds',body=text,draft=True))
    print(str(path))

if __name__=='__main__':main()
