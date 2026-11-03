"""Generate paper-ready prose and evidence tables from closed qualified endpoints."""
from round151_common import *
def fmt(v,d=12):return 'open' if v is None else f'{v:.{d}f}'
def build():
    full=read(OUT/'reports/full.json');lp=read(OUT/'reports/LP.json');cost=read(OUT/'cost_report.json');decision=read(OUT/'candidate_decision.json')
    assert not full['pending'] and decision['study_complete']
    lines=['# Round151: standalone resource-penalty propagation on stable GI-TBC','',
        '**Conclusion:** '+decision['decision']+'. '+decision['reason'],'',
        'Stable R137 GI-TBC remains the paper baseline. The sole complete candidate is C, with GD off; '
        'it was frozen before any complete result. B and C use the same new executable, original physical inputs '
        'and lambda=.15, Seed0/Threads1, complete independent own H with seed20260626, M-B/VD-P, '
        'pair-only AM=.08/depth8/minimum width1e-4, and AP/STOCK/Shared-S/GD off. '
        'The exposed configurations are finite tests, not blind samples or multi-seed robustness evidence.','',
        '## Four levels of evidence','',
        'Integer/completion validity and local inclusion are proved in mathematical_analysis.md. '
        'Saved-point separation and fully free same-domain LP results are recorded separately in LP_report.md. '
        'The complete finite algorithm comparison below pays own H, construction, every solve and necessary verification.','',
        '| Pure-B N-B35 root | B | P | C | P−B | C−P | C−B |','|---|---:|---:|---:|---:|---:|---:|',
        '| LP objective | '+' | '.join(fmt(lp[k]) for k in ['B','P','C','P_minus_B','C_minus_P','C_minus_B'])+' |','',
        'There are exactly two new LP optimizations; no old B or N-C20 baseline is reoptimized. '
        'C and P each add 537 rows and 1074 nonzeros, with no new columns and all variables free. '
        'N-C20 has 470 effective caps but its old qualified optimal point satisfies them all, so that root is not repurchased. '
        'All LP optima and primal-dual diagnostics have floating numerical qualification rather than rational certificates.','',
        '## New complete own-H results','',
        '| Role | Arm | Physical U | Supported L | U−L | Gap % | T_cert (s) | T_total (s) |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    for r in full['formal_arms']:
        lines.append(f"| {r['role']} | {r['method']} | {fmt(r['U'])} | {fmt(r['L'])} | {fmt(r['signed_gap'])} | {100*r['relative_gap']:.6f} | {fmt(r['T_cert'],6)} | {r['T_total']:.6f} |")
    lines+=['','U is recomputed from the original physical fleet. L is qualified external proof-cover support, '
        'which is distinct from the initial LP, the Native root after cuts and a raw terminal Native bound. '
        'Open T_cert values are null. Small qualified gaps are retained as reported. '
        'Cap-adjacent total differences are not called convergence speedups. Different final U values do not '
        'make first-arrival times a common-target speed comparison.','',
        '| Role / arm | Initial LP | Printed Native root after cuts | Native Work | Simplex iterations | Terminal nodes | Split count | Calls / returned | Caps / NZ |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in full['formal_arms']:
        lines.append(f"| {r['role']} / {r['method']} | {fmt(r['initial_root_L'])} | approx. {r['printed_root_after_cuts_bound']:.5f} | {r['Native_total_Work']:.6f} | {r['Native_total_simplex_iterations']:.0f} | {r['terminal_nodes']:.0f} | {r['actual_split_count']} | {r['declared_calls']} / {r['returned_calls']} | {r['cap_rows']} / {r['cap_nonzeros']} |")
    for c in full['comparisons']:
        lines+=['',f"{c['role']}: C changes U by {c['delta_U']:+.12f}, supported L by {c['delta_L']:+.12f}, "
            f"signed gap by {c['delta_signed_gap']:+.12f}, and relative gap by {100*c['delta_relative_gap']:+.6f} percentage points. "
            f"Physical-U improvement is {c['U_improvement_percent']:+.6f}%. The severe double-open reference is "
            f"{c['serious_double_open_regression']}; that reference alone does not decide adoption."]
    lines+=['','Unentered planned positions: '+', '.join(f"{r['position']}:{r['role']}/{r['method']}" for r in full['unentered'])+'.',
        decision['stopping_reason'],'',
        '## Research stage and paper claims','',
        'R137 already supplies a complete algorithm, role comparisons, resource/weight variation and mechanism/parameter evidence. '
        'R138–142 preserve real inventory/shared-factor proof gains, Native placement attribution and count conditioning. '
        'R143–145 preserve RN representation compression and strong local K35 results. '
        'R146–150 preserve cheap standalone GD and PF/CPF product-expression findings, including selected hard-role incumbent gains. '
        'The negative and historical identity/transport limits stay visible: K20 STOCK/Stock+GD certifies in roughly94.261/74.916s; '
        'R140 TC+STOCK has K35 U/L≈.650438712/.5682885263 and RB35≈.3190804927/.2339272621; '
        'R145 RN-P K35≈.660923637174/.550645816146. These have different source/PE/context identities and are not free matched controls.','',
        'R150 GD raised the N-C20 initial LP from .048357676071 to .129907632277 while increasing certificate time43.73%; '
        'on N-B35 it raised the initial LP from .327833772177 to .346856963718 while worsening final U2.24% '
        'and improving supported L only .16%. That concrete boundary and the current same-PE outcomes separate root expression '
        'strength from complete finite search value. Preserved AM geometry does not fix the Native search path; '
        'the observed changes are not uniquely attributed to a single cut or branch.','',
        'The R133 integer objective epigraph and full route/loading/time coupling gaps remain unresolved; '
        'a fixed denominator does not remove the former. R52 retains the corrected three severe false-retains and '
        'the correct negative anchor: parent Work≈843.456 certifies whereas forced midpoint≈2651.321 stays capped. '
        'No rescue, iterative cutoff, per-state oracle, GD/STOCK/Shared-S combination, extra seed or automatic implementation chain is started.','',
        '## Cost, identities and delivery','',
        f"Charged experimental outer cost is {cost['charged_new_experiment_seconds']:.6f}s /14400s; "
        f"build cost is separately {cost['build_seconds']:.6f}s. All new own H, arithmetic, construction, solves, "
        'qualification failures and necessary verification are charged once. Nested Runtime/Work and historical fees are not added. '
        'A conservative30s allowance discloses incomplete exact timing of short qualification probes. '
        'Pure authoring and public I/O are separate; independent audit frames are charged explicitly.','',
        f"Complete Native calls/returned: {full['complete_Native_Optimize']}/{full['complete_Native_returned']}; "
        f"production-qualification calls/returned: {full['qualification_Native_Optimize']}/{full['qualification_Native_returned']}; "
        'standalone LP calls/returned:2/2. Unique raw, failures, seals, witnesses, Work and target/split paths are retained. '
        'The exact executed LP helper and failed fixture versions are preserved. The fixed science/delivery identities '
        'and public byte/member recovery are in carrier_manifest.json and RESUME.md. Stable and older research entry bytes '
        'and protected original user files are unchanged.','']
    (OUT/'final_report.md').write_text('\n'.join(lines),encoding='utf-8')
    paper=['\\subsection{Resource penalty propagation without GD}',
        'GI-TBC is the stable complete method. For actual objective weights, define '
        '$h_i(y)=\\omega_i|c_i y-1|$. One fixed resource dual yields '
        '$d=\\mu B^- -\\nu B+\\sum_i m_i$ and '
        '$d_{iy}=\\mu B^- -\\nu B+\\sum_{j\\ne i}m_j+h_i(y)+(\\nu-\\mu)y$. '
        'Weak duality gives conditional penalty lower bounds without any GD or STOCK assumption. '
        'Outward evaluation and the arm\'s own cutoff produce upper caps '
        '$t_{iy}\\le\\beta_{iy}s_{iy}$ directly in the existing state products. '
        'One row per state covers the uniform information as well; no duplicate PF layer or new column is needed.',
        'The same monotone upward coefficient transport is used for uniform and conditional caps, '
        'preserving the actual relaxation inclusion $Q_C\\subseteq Q_P\\subseteq Q_B$. '
        'A zero global penalty floor can coexist with nonzero conditional information. '
        'Caps are frozen at the first own root and inherited only by compatible subdomains; '
        'they do not change the physical objective, root proof interval or AM scheduling rules.',
        'On the same saved pure-B N-B35 root, fully free LP values are '
        f"$L_B={lp['B']:.12f}$, $L_P={lp['P']:.12f}$ and $L_C={lp['C']:.12f}$. "
        'These numerically qualified LP increments motivate a finite complete test rather than establish its outcome. '
        'The N-C20 saved optimum already satisfies the new rows and is not reoptimized.',
        '\\begin{center}\\begin{tabular}{llrrrr}\\hline Role & Arm & $U$ & $L$ & Gap (\\%) & $T_{total}$ \\\\ \\hline']
    paper.insert(2,
        'The resource relaxation retains the root boxes and $B^-\\le\\sum_iY_i\\le B$. '
        'Here $m_i=\\min_{\\ell_i\\le z\\le u_i}\\{h_i(z)+(\\nu-\\mu)z\\}$, '
        'with fixed $\\mu,\\nu\\ge0$. Define conservative floors '
        '$p_0=\\max\\{0,\\operatorname{down}(d)\\}$ and '
        '$p_{iy}=\\max\\{p_0,0,\\operatorname{down}(d_{iy})\\}$. '
        'Uniform and conditional caps are '
        '$\\beta_0=\\min\\{\\gamma_U^0,\\operatorname{up}(U_0-p_0)\\}$ and '
        '$\\beta_{iy}=\\min\\{\\beta_0,\\operatorname{up}(U_0-p_{iy})\\}$. '
        'For an integer selected state, $Y_i=y$ and $t_{iy}=g$; '
        '$g+P_e\\le U_0$ and $P_e\\ge p_{iy}$ establish the cap even for a nonminimal epigraph completion. '
        'Prefix/suffix lower sums avoid subtracting independently rounded bounds. '
        'The fixed-multiplier propagation pass is linear in stations plus supported states; '
        'the inherited multiplier selection also sorts station slopes.')
    for r in full['formal_arms']:
        paper.append(f"{r['role']} & {r['method']} & {r['U']:.9f} & {r['L']:.9f} & {100*r['relative_gap']:.5f} & {r['T_total']:.3f} \\\\")
    paper+=['\\hline\\end{tabular}\\end{center}',decision['paper_conclusion'],
        'Initial LP, Native root cuts and terminal supported bounds remain distinct. '
        'R150 GD already demonstrated a stronger root with worse full outcomes. '
        'R138--150 inventory proof gains, Native-placement evidence, RN compression and selected GD incumbent gains '
        'remain part of the evidence, while the R133 integer-objective and joint routing--loading--time gaps are still open. '
        'The local state-interval hull here does not solve those joint integer problems.']
    (OUT/'manuscript.tex').write_text('\n\n'.join(paper)+'\n',encoding='utf-8')
    print('Wrote final report and paper section from qualified closed results')
if __name__=='__main__':build()
