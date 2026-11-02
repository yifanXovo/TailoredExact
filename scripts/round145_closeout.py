"""Idle-only scientific closeout; no solver, commercial imports or new experiments."""
from round145_common import *

def table(headers, rows):
    def display(x):
        if x is None: return 'open'
        if isinstance(x, bool): return 'yes' if x else 'no'
        if isinstance(x, float): return format(x, '.12g')
        return str(x)
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |',
        *['| '+' | '.join(display(x) for x in row)+' |' for row in rows]])+'\n\n'

def main():
    assert not budget()['unclosed']
    full=read(OUT/'reports/full.json'); pairs=full['pairs']; bridges=full['RNP_bridges']
    role_order={r:i for i,r in enumerate(['K-20-S','K-35-U','R-X20-S-T1','R-B35-S-T2'])}
    method_order={'OFF':0,'RNJP':1,'RNP':2}
    arms=sorted(full['new_arms'],key=lambda a:(role_order[a['role']],method_order[a['method']]))
    assert len(arms)==9 and len(pairs)==4 and len(bridges)==1 and not full['pending'] and not full['failed_qualifications']
    assert all(a['performance_eligible'] and a['native_proof_qualified'] for a in arms)
    by={(a['role'],a['method']):a for a in arms}
    k=next(p for p in pairs if p['role']=='K-35-U'); rb=next(p for p in pairs if p['role']=='R-B35-S-T2'); bridge=bridges[0]
    cost=read(OUT/'cost_report.json'); b=budget(); manifest=read(OUT/'candidate_manifest.json')
    assert b['G1_seconds']<=28800
    k_u_gain=(k['off_U']-k['RNJP_U'])/k['off_U']*100
    discussion=(f"K35 RN-JP improves U by {k_u_gain:.6f}% against contemporaneous OFF, but weakens supported L by {-k['delta_L']:.12g} "
        f"and increases relative gap by {k['delta_relative_gap']*100:.6f} percentage points. "
        "K20 reaches the same U with a weaker supported L; neither method certifies. RX20 certifies the identical objective in both methods, "
        "with no material certificate/total-time benefit. "
        f"RB35 RN-JP U/L is {rb['RNJP_U']:.12g}/{rb['RNJP_L']:.12g}, against OFF {rb['off_U']:.12g}/{rb['off_L']:.12g}; "
        f"its signed changes are delta U={rb['delta_U']:.12g}, delta L={rb['delta_L']:.12g}, and delta relative gap={rb['delta_relative_gap']*100:.6f} percentage points. "
        "All adverse endpoints remain authoritative. The source is active on all four roles, so the new resource endpoint is not explained by the predecessor's no-PC prefix finding.")
    bridge_text=(f"The K35 same-PE old RN-P bridge gives U/L={bridge['RNP_U']:.12g}/{bridge['RNP_L']:.12g} and relative gap {bridge['RNP_gap']:.12g}, "
        f"against RN-JP {bridge['RNJP_U']:.12g}/{bridge['RNJP_L']:.12g} and {bridge['RNJP_gap']:.12g}. "
        f"RN-JP minus RN-P is {bridge['delta_RNJP_minus_RNP_U']:.12g} in U, {bridge['delta_RNJP_minus_RNP_L']:.12g} in supported L, "
        f"and {bridge['delta_RNJP_minus_RNP_relative_gap']*100:.6f} percentage points in relative gap. "
        "Both formal models have zero RN columns and at most one PC. This is a direct finite comparison of the two compact candidates; it is not a causal column-count experiment or a whole-tree preservation test.")
    decision_text=("Retain RN-JP as default-off research and stop this once-root joint-expression trial without stable promotion. "
        "The local theorem, stronger real joint LP, exact saved-point separation, full-block projection and near-complete root retention are retained results. "
        "They have not yielded a sufficiently convincing complete improvement over BASE across the core roles; the single K35 bridge assesses existing compact RN-P. "
        "A stronger paid source followed by one root row does not enforce full integer-objective consistency or guarantee useful descendant search. "
        "Do not automatically add more thresholds, repeated separation, floor grids, a second route-A panel, or further seeds. "
        "Optional K15/RX35 pairs and Seed/floor controls are not entered: the observed mixed/negative complete evidence already resolves adoption of this candidate, "
        "and no specific opposing result currently justifies that cost. Unused budget is not a reason to expand. "
        "This closure does not erase the earlier STOCK certificates or RN-P K35 computational gains.")
    decision=dict(UTC=utc(),study_complete=True,decision='RESEARCH_ONLY_STOP_JOINT_ONCE_ROOT_TRIAL',route='B',
        stable_promotion=False,default_off=True,full_positions=9,core_roles=4,same_PE_pairs=4,same_PE_RNP_bridges=1,
        new_standalone_LPs=11,strong_old_carrier_gain_K35=0.0052860004331529,
        compact_root_loss_K35=2.7533531010703882e-14,compact_root_loss_RX20=1.7263968032921184e-14,
        full_results_discussion=discussion,bridge_discussion=bridge_text,decision_paragraph=decision_text,
        complete_U_gains_not_erased=True,zero_new_certificate_roles=True,route_A_panel_entered=False,
        optional_boundary_seed_floor_entered=False,all_entered_results_and_fees_retained=True,
        formal_RN_columns_all_methods=0,scope='Known finite four-role Seed0 panel, not unseen validation or global dominance',
        source_commit=manifest['source_commit'],PE_SHA256=manifest['production_PE_SHA'],
        charged_experiment_seconds=b['G1_seconds'],remaining_experiment_seconds=28800-b['G1_seconds'])
    write(OUT/'candidate_decision.json',decision)

    endpoint=table(['Role','Method','U','Supported L','Signed gap','Relative gap'],
        [[a['role'],a['method'],a['U'],a['L'],a['signed_gap'],a['relative_gap']] for a in arms])
    clocks=table(['Role','Method','T produce s','T cert s','T verify s','T total s'],
        [[a['role'],a['method'],a['T_produce'],a['T_cert'],a['T_verify'],a['T_total']] for a in arms])
    source=table(['Role','Source objective','First formal LP','Observed loss','PC NZ'],
        [[a['role'],a['source_L'],a['root_L'],a['observed_source_minus_formal_first_root_L'],a['PC_nonzeros']]
         for a in arms if a['method']=='RNJP'])
    native=table(['Role','Method','Terminal Native bound','External final L','Terminal nodes','Terminal Work'],
        [[a['role'],a['method'],a['terminal_native_return_ObjBoundC'],a['external_merged_final_L'],a['terminal_nodes'],a['terminal_Work']] for a in arms])
    report=('# Round145 completed joint-expression trial\n\n'+decision_text+'\n\n'
        '## What was established\n\n'
        'The same-factor NC/TS connection is locally strict, with a remaining integer-objective epigraph gap. '
        'The matched K35 joint objective .234508197894 exceeds strong old RN+stock+TC+TC2 .229222197461 by .005286000433. '
        'O+joint matches joint numerically. RX20 and former no-PC K20 gain .006577487540 and .027659787220 over their reused RN baselines. '
        'Eleven new standalone LPs, rather than a reopened historical panel, answer the finite information/transport question. '
        'Actual C++ one-row compact reoptimization loses only 2.7534e-14/1.7264e-14 on K35/RX20. '
        'This retains essentially all measured useful root increment, not the whole source projection or all-tree behavior.\n\n'
        'Four zero-Optimize original-point NC-PC separations match the supplied signals within 2.5e-14. '
        'All four points also violate old TC2, which is why the strong-old-carrier comparison is required. '
        'RX20 standalone and complete-production saved points have distinct identities and both results remain. '
        'The all-n local family is proved algebraically; the goal-reported old finite enumeration asset was not recovered or rerun.\n\n'
        '## Complete same-PE evidence\n\n'
        f'All nine entered full positions and one short health qualification passed physical, proof, Native matrix and lifecycle verification. All {full["all_entered_observed_Native_Optimize"]} complete/qualification Native calls returned; the 11 standalone LP calls are separate. '
        'There are no failed producer qualifications. Each method pays complete own H, optional one-time source, formal search and mandatory verification. '
        'Gurobi Seed=0, H seed=20260626, Threads=1 and affinity mask=4 are explicit; all timing is serial. '
        'K20/RX20 caps are 1200 seconds and K35/RB35 caps 2400 seconds, separate from physical T. '
        'Resource lambda values remain the exact original input values. Each pair/bridge has identical input, physical T, objective, cap and PE/source, with the same own-H semantics and initial physical Start lineage. Descendant Starts may differ after search paths diverge.\n\n'
        +endpoint+discussion+'\n\n'+bridge_text+'\n\n'+clocks+
        'Open T_cert is null in machine-readable data. Signed gap is U-L; relative gap follows the accepted reader definition. '
        'K20 verification clocks differ despite similar evidence scale; its smaller total is not called a proof speedup. '
        'The tiny RX20 production/total differences are reported without a substantive acceleration claim.\n\n'
        '## Root retention and Native diagnostics\n\n'+source+
        'Every RN-JP formal model has zero persistent RN columns; its complete source contains RN plus both NC and all four TS rows. '
        'Projection and actual Native auditing consume that full explicit list. Actual production dual rows may differ from diagnostic dual rows at degenerate optima. '
        'The source is restored/discarded; its point, bound and handles are not formal control evidence. Source time is charged.\n\n'+native+
        'Native returned bounds and the external supported merged bound are separate authorities. '
        'Presolve sizes, root simplex, Native Runtime/Work, AM decisions, calls and physical objective components are in reports/new_arms.csv and full.json. '
        'Verified witness trajectories use their own declared effective producer clock; they do not replace complete T produce/T cert.\n\n'
        '## History and interpretation\n\n'
        'stage_evidence.md retains stable R137, STOCK certificate improvements, count/placement boundaries and RN-P K35 gains. '
        'The goal-supplied R144 RB35 raw audit supports an observed matching prefix truncated near the wall boundary, not its unexecuted future. '
        'Its adverse endpoint and fees remain. The roughly 21-second native drift at node 6619 is not all assigned to 2.3388-second source preparation. '
        'R144 K20 verification 286.74/61.69 seconds is not relabeled as structural acceleration. '
        'The stable manuscript, entries/profiles and prior research identities are retained.\n\n'
        '## Cost, source and delivery\n\n'
        f'New experimental outer cost is {b["G1_seconds"]:.9f} seconds ({b["G1_seconds"]/3600:.6f} hours) of 28800; '
        f'{28800-b["G1_seconds"]:.9f} seconds remain unused. Source, qualifications and mandatory postverification are included; '
        'nested H/LP/MIP/Work is not added again. Build and offline exact arithmetic are separately recorded in cost_report.json; '
        'paper export, archival and public I/O remain separate delivery costs.\n\n'
        f'Measured production source is `{manifest["source_commit"]}`; PE SHA256 is `{manifest["production_PE_SHA"]}`. '
        'candidate_manifest.json binds actual source bytes, affected compilation units and inherited objects/libraries. '
        'Independent pre-admission, writer, output and final scientific reviews are in review/. '
        'Raw, source/helper/input and manuscript carriers have explicit byte/member indices. '
        'Publication pins, anonymous public byte/member recovery, actual Draft PR readback and current-round cleanup receipts are recorded separately as delivery completes. '
        'Public byte recovery is not a new public semantic rerun. All new assets stay under ExactEBRP-work; original user contents and old rounds are protected.\n\n'
        'Read RESUME.md for entry points and final handoff. No remaining solver panel is required for this completed decision.\n')
    (OUT/'final_report.md').write_text(report,encoding='utf-8',newline='\n')

    manuscript=(OUT/'manuscript.md').read_text(encoding='utf-8-sig').split('## Complete computational evidence and adoption')[0]
    manuscript+='## Complete computational evidence and adoption\n\n'
    manuscript+=('Four core roles compare RN-JP with stable-off using the same measured executable and explicit Seed 0. '
        'Each method pays complete own H, its selected source, formal search, and verification. '
        'The physical horizons are 5400 seconds for K20, 10800 for K35, 4800 for RX20-T1 and 7200 for RB35-T2. '
        'Compute caps are respectively 1200, 2400, 1200 and 2400 seconds. K roles retain lambda .15; resource roles retain their exact original rho=1, lambda=1/Omega. '
        'Threads=1, affinity mask=4 and H seed=20260626 are fixed, and timing is serial. '
        'One admitted K35 old RN-P bridge compares compact candidates under the same PE, input, objective, H, seed and budget. '
        'This is a known finite research panel, not an independent unseen validation set.\n\n')
    manuscript+=table(['Role','Method','U','Supported L','Relative gap'],[[a['role'],a['method'],a['U'],a['L'],a['relative_gap']] for a in arms])
    manuscript+=discussion+'\n\n'+bridge_text+'\n\n'
    manuscript+=table(['Role','Method','Production s','Certificate s','Verify s','Total s'],
        [[a['role'],a['method'],a['T_produce'],a['T_cert'],a['T_verify'],a['T_total']] for a in arms])
    manuscript+=('Open certificate clocks are null in the data and displayed as open. Verification is separate from production and certification. '
        'K20 has no new certificate, so a smaller verification or total clock is not proof acceleration. '
        'The small RX20 differences are not substantive speed evidence. '
        'Native returned bounds, external merged bounds, signed gaps, physical objective components, presolve sizes, simplex iterations, AM decisions and Work remain separate fields in the full reports.\n\n')
    manuscript+=source
    manuscript+=('The table compares the paid production source with the first formal continuous LP. '
        'These numerical losses measure root retention; they do not predict root-after-cuts or full-tree bounds. '
        'All formal models contain zero RN columns.\n\n')
    for figure,label in [('K35_verified_U.png','K35, including the same-PE RN-P bridge'),('RB35_T2_verified_U.png','RB35-T2')]:
        if (OUT/'figures'/figure).exists():
            manuscript+=f'![{label}: qualified physical-incumbent trajectories on the declared effective producer clock. Complete production and certificate clocks remain in the tables.](figures/{figure})\n\n'
    manuscript+=('Predecessor RN-P evidence remains visible: its original K35 U improves 4.6086% and relative gap falls 1.9534 percentage points despite weaker L. '
        'K20 and RB35 emit no predecessor PC. The supplied raw RB35 audit finds identical formal matrices, H and Start, all 33 RN-P physical witnesses matching the first 33 OFF witnesses, '
        'and matching observed clock-free root/positive-node states; OFF alone obtains its final improvement near the wall boundary. '
        'This supports an observed same-prefix truncation, not a proof of the unexecuted continuation. '
        'At node 6619, about 21 seconds of Native drift exceeds the 2.3388-second source preparation, so the latter does not explain all drift. '
        'The adverse endpoint and all fees remain. Similar evidence sizes also do not make K20 verification-clock variation structural acceleration.\n\n')
    manuscript+='## Decision and reproducibility scope\n\n'+decision_text+'\n\n'
    manuscript+=(f'The charged new experimental cost is {b["G1_seconds"]:.6f} seconds of 28800 ({b["G1_seconds"]/3600:.6f} hours). '
        'This includes source work, qualification and necessary postverification, without adding nested H, LP, MIP or Work twice. '
        'Builds, offline exact arithmetic, paper preparation and bounded public I/O are separate. '
        'No second route-A panel, extra Seed, floor or boundary grid is entered. '
        f'All nine full positions, the short health qualification, all {full["all_entered_observed_Native_Optimize"]} returned complete/qualification Native calls, the 11 standalone LPs, actual row/readback identities and independent reviews remain in the finite evidence package. '
        'The measured source/PE identity is distinct from the final scientific and delivery commits. '
        'Anonymous public byte/member verification checks delivery integrity without claiming public solver reproduction.\n')
    (OUT/'manuscript.md').write_text(manuscript,encoding='utf-8',newline='\n')
    sources=[]
    for name,expected in manifest['source_hashes'].items():
        actual=(ROOT/name).read_bytes();assert hashlib.sha256(actual).hexdigest()==expected
        blob=subprocess.check_output(['git','show',manifest['source_commit']+':'+name],cwd=ROOT)
        assert actual.replace(b'\r\n',b'\n')==blob.replace(b'\r\n',b'\n'),name
        sources.append(dict(path=name,SHA256=expected,bytes=len(actual),Git_blob_SHA256=hashlib.sha256(blob).hexdigest(),
            measured_commit=manifest['source_commit'],actual_compiler_bytes_in_source_carrier=True,Git_semantics_equal_modulo_registered_EOL=True))
    write(OUT/'source_publication.json',dict(measured_production_commit=manifest['source_commit'],PE_SHA256=manifest['production_PE_SHA'],sources=sources,
        Git_and_actual_compiler_bytes_distinguished=True,source_carrier='artifacts/source_and_helpers.zip',binaries_not_published=True))
    print(json.dumps(dict(study_complete=True,decision=decision['decision'],positions=len(arms),G1_seconds=b['G1_seconds'],Optimize=0,Native_load=0)))

if __name__=='__main__':main()
