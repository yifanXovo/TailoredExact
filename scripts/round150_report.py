"""Assemble the finite two-task report from closed evidence, without Native."""
from round150_common import *


def fmt(value,digits=12):
    return '—' if value is None else f'{value:.{digits}f}'


def build():
    full = read(OUT/'reports/full.json')
    decision = read(OUT/'candidate_decision.json')
    cost = read(OUT/'cost_report.json')
    assert not full['pending'] and len(full['formal_arms'])==4
    assert full['complete_Native_Optimize']==full['complete_Native_returned']
    assert decision['study_complete']
    arms, pairs = full['formal_arms'], full['comparisons']
    lines = ['# Round150: GD confirmation and conditional penalty feedback','',
        '**D positioning:** '+decision['D']['decision']+'. '+decision['D']['reason'],'',
        '**CPF qualification:** '+decision['CPF']['decision']+'. '+decision['CPF']['reason'],'',
        'The two tasks have independent stopping criteria. R137 GI-TBC remains the stable complete method. '
        'No production C++, executable, old entry or profile was changed; no new build, extra seed, '
        'clarification pair, baseline reoptimization or complete CPF run was entered.','',
        '## New complete B/D evidence','',
        'Both inputs were tested in R137 and are known/exposed. Neither was used to select GD. '
        'This is a finite confirmation outside the method-selection roles, not a blind validation set '
        'or evidence for an unobserved data distribution. N-B35-S and R-B35-S-T2 are different '
        'physical inputs and objectives. Both new roles keep their original lambda=.15.','',
        '| Role | Arm | Physical U | Supported L | U−L | Gap % | Certified | T_produce | T_cert | T_verify | T_total |',
        '|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|']
    for r in arms:
        lines.append(f"| {r['role']} | {r['method']} | {fmt(r['U'])} | {fmt(r['L'])} | {fmt(r['signed_gap'])} | "
            f"{100*r['relative_gap']:.6f} | {r['certificate']} | {r['T_produce']:.6f} | {fmt(r['T_cert'],6)} | "
            f"{r['T_verify']:.6f} | {r['T_total']:.6f} |")
    lines += ['', 'U is recomputed from the actual fleet under the original physical objective. '
        'L is the qualified external proof-cover support, rather than a raw terminal Native bound. '
        'T_cert is the same accepted producer qualification on both arms; open entries are null. '
        'T_total includes necessary verification. Metered outer fees also include the small wrapper overhead. '
        'Local floating tolerances and solver OPTIMAL status are not exact rational optimality proofs.','']
    for c in pairs:
        text = (f"For {c['role']}, D changes physical U by {c['delta_U']:+.12f}, supported L by "
                f"{c['delta_L']:+.12f}, signed gap by {c['delta_signed_gap']:+.12f} and relative gap by "
                f"{100*c['delta_relative_gap']:+.6f} percentage points. U improvement is "
                f"{c['U_improvement_percent']:+.6f}%; L improvement is {c['L_improvement_percent']:+.6f}%. ")
        if c['certificate_speedup_percent'] is not None:
            text += (f"Both certify; same-qualification T_cert changes from {c['B_T_cert']:.6f}s to "
                     f"{c['D_T_cert']:.6f}s ({-c['certificate_speedup_percent']:+.6f}% time change), while "
                     f"complete T_total changes from {c['B_T_total']:.6f}s to {c['D_T_total']:.6f}s. ")
        else:
            text += 'No capped time is substituted for a certificate time or used to claim speedup. '
        text += f"Severe double-open reference flag: {c['serious_double_open_regression']}."
        lines += [text,'']
    lines += ['| Role | Arm | Initial LP L | Final-U first availability (s) | Total Native Work | Terminal nodes | Calls / returned | GD rows / NZ |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    for r in arms:
        lines.append(f"| {r['role']} | {r['method']} | {fmt(r['initial_root_L'])} | {r['first_final_U_seconds']:.6f} | "
            f"{r['Native_total_Work']:.6f} | {r['terminal_nodes']:.0f} | {r['declared_calls']} / {r['returned_calls']} | "
            f"{r['GD_rows']} / {r['GD_nonzeros']} |")
    lines += ['', 'The verified witness trajectories and per-call target/Work records are retained. '
        'Initial LP, printed root-after-cuts and final external support are distinct levels. '
        'The final-U availability is incumbent evidence, not proof time. '
        'N-B35-S final U differs between arms, so earlier arrival at each arm\'s own final U '
        'is not a common-target speed comparison. Retaining AM geometry '
        'does not fix the Native search path, so these observations do not uniquely identify a '
        'single branch, cut or target as a causal mechanism. The severe reference rule is a '
        'clear warning criterion, not a necessary or sufficient adoption rule.','',
        '## Matched CPF LP screen','',
        'See [mathematical_analysis.md](mathematical_analysis.md) for fixed-dual conditioning, '
        'leave-one-out arithmetic, integer completion validity, local hull and AP separation. '
        '[LP_report.md](LP_report.md) records all three free reoptimizations and numerical boundaries.','',
        '| Domain | D | PF | CPF | PF−D | CPF−PF |', '|---|---:|---:|---:|---:|---:|']
    for r in read(OUT/'reports/LP.json')['domains']:
        lines.append(f"| {r['role']} | {fmt(r['old_D_L'])} | {fmt(r['old_PF_L'])} | {fmt(r['L'])} | "
                     f"{fmt(r['PF_minus_D'])} | {fmt(r['CPF_minus_PF'])} |")
    lines += ['', 'The old PF points are cut in15/34/8 states, but the reported increments come from '
        'complete LP reoptimization with all variables free. Added rows/NZ are451/902,539/1078,143/286. '
        'The same actual binary64 dual is reused once; no conditional LP or dynamic update is paid. '
        'The old K35 PF primal-dual diagnostic gap is about.000619046 and DualVio about8.92e-7. '
        'The new K35 dual is numerically above the old saved feasible primal; new primal-dual gaps '
        'are below1.2e-15. Positive finite numerical increments are supported without claiming exact '
        'rational LP optimality or repurchasing the old baseline. No extra quality Optimize is needed.','',
        '## Inherited evidence and historical limits','',
        'R147 selected D on four already known Seed0 roles. Those finite same-R146-PE results '
        'remain their own identity: hard-role incumbent gains were accompanied by weaker K35 L, '
        'and K20 stayed open. The two new configurations extend the observed role scope, while '
        'keeping all parameters uniform. No instance-name patch, size switch, timed algorithm '
        'switch or selection among reruns is introduced.','',
        'Specifically, the inherited R147 B-to-D physical-U improvements are3.12830% on K35 '
        'and2.54148% on RB35-T2. K35 supported L changes from.564290795837 to.552835648924; '
        'RB35-T2 L changes from.218985949603 to.219475150151. K20 keeps the same U and '
        'remains open with slightly weaker D L. RX20 retains its certificate with T_cert '
        '22.324898s for B versus24.666144s for D. These selected-role results use the old '
        'R146 PE and are archived as reports/R147_selection.json; they are not new R149-PE '
        'matched controls and do not establish broad robustness.','',
        'R149 PF is valid and all three matched LP increments are positive. K35 U improves '
        '2.00348% and signed gap6.69156% despite lower L; its better final U is available at583.047s. '
        'K20 reaches the common final incumbent at131.172s versus394.906s for D, but neither '
        'certifies and PF final L is slightly lower. RB35 U loses3.08518% while L gains2.26970%; '
        'the signed gap worsens without triggering the original severe double-open rule. '
        'All six formal arms are open with null T_cert. These real positive and adverse facts '
        'support research-only retention, not a claim of theoretical failure or no benefit. '
        'R149 costs12060.885540600s plus56.177043s build separately; its35 producer calls and4 '
        'diagnostic LPs and public10-package/133255-member recovery are closed historical evidence. '
        'They are not charged or purchased again.','',
        'Shared-S has genuine expression and positive matched LP evidence, while the measured '
        'complete implementation stays research only. Prior K20 STOCK/STOCK+GD certificates '
        'around94.261/74.916s, R140 TC+STOCK Seed0 K35 U/L≈.650438712/.5682885263 and '
        'RB35≈.3190804927/.2339272621, and R145 RN-P K35≈.660923637174/.550645816146 '
        'remain stronger historical local endpoints. They carry their own scopes, negative results '
        'and source/PE differences, and are not free controls for this round. R140 Seed1 also '
        'changes source/PE/transport; it is not a pure seed-causal intervention.','',
        'R47–52 already studied AM mechanisms and rescue. R52 has three severe false-retains, '
        'and a genuine correct-retain negative anchor: parent Work≈843.456 certifies while forced '
        'midpoint Work≈2651.321 remains capped. R119 dynamic incumbent rebuilding, R120–122 '
        'conditional/subdomain propagation, R130/R137 root-only, R131 budget-to-domain and '
        'R135 AP/IND expression relations retain their identities. R133 integer-objective '
        'difficulty is not solved by this continuous propagation. Standard weak duality and '
        'local disjunction theory underpin the project-specific construction, rather than a '
        'new general convexification theorem.','',
        '## Cost, identity and delivery','',
        f"New experimental outer cost is **{cost['charged_new_experiment_seconds']:.9f}s / 14400s**, "
        'including own H, construction, solves, necessary qualifications and validation once. '
        'There is no new build. Nested Runtime/Work and old costs are not added. '
        'Disclosed conservative manual/startup allowances avoid false timing precision. '
        'Pure theory/authoring and public I/O are separate. No unused clarification capacity '
        'is booked as expenditure.','',
        f"All{full['complete_Native_Optimize']} actual complete-arm Native calls returned, plus three "
        'separate CPF LP calls. Neither call count nor GD row count was assumed. The reader '
        'uses the actual first-call model SHA and accepts mathematically omitted GD and own-H '
        'completion before model construction. Every entered run, call, failure if any, producer '
        'seal and necessary raw record is preserved.','',
        'Production source is380a85f866bffb914036190f8ee2700ce8b55978; PE SHA is '
        '373efa9a596aaf02fb332685515fcfe88df1b169cbe53b295ab6027140620295. '
        'The R150 wrapper, fixed design, science commit and delivery head are separate in '
        'execution_identity.json, identity_index.json and publication_pin.json. The original '
        'stable/research entries and configs retain their bytes. New assets remain under '
        'ExactEBRP-work and the original user tree and old evidence are protected.','',
        'The paper section is manuscript.tex; its evidence relationship table connects the '
        'validity, point-separation, LP and complete-method layers. Independent nonimplementer '
        'review, carrier/member hashes, finite public recovery and bounded current-round cleanup '
        'are recorded separately. Delivery targets an English Draft PR with no automatic merge; '
        'actual creation and state are recorded in PR_readback.json after that step.','']
    (OUT/'final_report.md').write_text('\n'.join(lines),encoding='utf-8')
    fragment = OUT/'manuscript.tex'
    marker = '% ROUND150 COMPLETE RESULTS are appended from the accepted endpoints.'
    base = fragment.read_text(encoding='utf-8').split(marker)[0]
    tail = [marker,r'\paragraph{Additional complete comparisons.}',
        'Both R137 configurations are known/exposed and were outside GD selection. Both retain '
        'lambda=.15, original physical inputs/horizons and independent complete own H. '
        'The four frozen arms share the R149 executable, Seed0/Threads1 and matched caps.',
        r'\begin{center}\small\begin{tabular}{llrrrr}',
        r'Role & Arm & $U$ & Supported $L$ & Gap (\%) & $T_{\rm total}$ (s) \\',r'\hline']
    for r in arms:
        tail.append(f"{r['role']} & {r['method']} & {r['U']:.9f} & {r['L']:.9f} & "
                    f"{100*r['relative_gap']:.4f} & {r['T_total']:.3f} "+r'\\')
    tail += [r'\end{tabular}\end{center}', decision['D']['paper_conclusion'],
        'R149 PF also improved K35 incumbent U and reached the common K20 final U earlier, '
        'while losing RB35 U and gaining no certificate. No-promotion does not invalidate '
        'these positive expression and incumbent facts.',
        f"New experimental outer cost is {cost['charged_new_experiment_seconds']:.6f}s of14400s. "
        'Every own heuristic, construction, solve and necessary verification is charged once; '
        'nested Runtime/Work and historical costs are not added. No new build or complete CPF run is entered.']
    fragment.write_text(base+'\n'.join(tail)+'\n',encoding='utf-8')
    identity = read(OUT/'execution_identity.json')
    write(OUT/'identity_index.json',dict(identity,production_source=SOURCE,
        methods=read(OUT/'candidate_manifest.json')['method_definition_science'],
        wrapper_helpers=read(OUT/'confirmation_matrix.json')['helpers'],
        postprocessing_helpers={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'scripts').glob('round150*')},
        science_commit='publication_pin.json after fixed science commit',
        delivery_head='Actual PR readback; not production source',new_build=False))
    print(json.dumps(dict(report=True,arms=4,D=decision['D']['decision'],CPF=decision['CPF']['decision'])))


if __name__=='__main__':
    build()
