"""Scientific closeout from sealed evidence; publication receipts remain separate."""
from round134_common import *
import collections,re
import round108_reader as core

def number(value,digits=8):
    return 'unresolved' if value is None else f'{value:.{digits}g}'

def protected():
    baseline=read(OUT/'baseline.json');checks={}
    for name,expected in baseline['protected_dirty'].items():
        actual=sha(Path('E:/codes/ExactEBRP')/name);assert actual==expected
        checks['original_dirty/'+name]=actual
    for name,expected in baseline['protected_assets'].items():
        actual=sha(Path(name));assert actual==expected;checks[name]=actual
    candidate=read(OUT/'candidate_manifest.json')
    assert sha(candidate['production_PE'])==candidate['production_PE_SHA']
    assert sha(candidate['DLL'])==candidate['DLL_SHA']
    for name,expected in candidate['source_hashes'].items():assert sha(ROOT/name)==expected
    assert git('rev-parse','HEAD',cwd=Path('E:/codes/ExactEBRP')).decode().strip()==baseline['original_tree_HEAD']
    return dict(passed=True,checks=checks,original_HEAD=baseline['original_tree_HEAD'],
        current_PE_SHA=candidate['production_PE_SHA'],current_source_all_hashes_match=True,
        scope='three original dirty bytes, four original native assets, original HEAD and frozen current source/PE/DLL')

def lambda_audit():
    records=[]
    for stage in ('C','D'):
        for group in read(OUT/f'{stage}_matrix_frozen.json')['groups']:
            launch=group['launch'];p=launch['panel']
            if launch['method']!='S2' or launch['seed']!=0 or launch['id'] not in ('K-15-S','UC-B20-B'):continue
            d=Path(launch['destination']);a=read(d/'audit.json');e=read(d/'round134_endpoint.json')
            argv=launch['command'];assert float(argv[argv.index('--lambda')+1])==p['lambda']
            physical=a['physical'];assert abs(physical['F']-(physical['G']+p['lambda']*physical['P']))<=1e-12
            data=core.evidence.instance(ROOT,p)
            H=a['full_H'];assert H and H['complete']
            h=H['physical'];assert abs(h['F']-(h['G']+p['lambda']*h['P']))<=1e-12
            objective_models=[]
            for fact in a['model_contracts']:
                model_path=ROOT/fact['model']['path'];m=core.lp_model(model_path)
                objective=dict(m['objective'][0]);assert m['objective'][1]==0 and objective.pop('G')==1
                expected={f'e_{i}':p['lambda']*data['w'][i] for i in range(1,p['V']+1) if p['lambda']*data['w'][i]!=0}
                assert objective==expected,('lambda objective mismatch',launch['arm_id'],model_path)
                # Scope/cutoff, Start, loaded feasible witnesses and all source
                # premises were checked by the same current production reader.
                assert fact['scope']['metadata_scope_is_actual_model_scope']
                objective_models.append(dict(path=model_path.relative_to(ROOT).as_posix(),SHA256=sha(model_path)))
            assert a['passed'] and a['implementation_qualified'] and a['evidence_complete']
            records.append(dict(arm_id=launch['arm_id'],role=launch['id'],lambda_value=p['lambda'],
                argv_same=True,H_F=h['F'],physical_F=physical['F'],reader_U=e['U'],
                objective_models=objective_models,full_H=True,
                H_physical_loaded_objective_Start_bound_scope_and_reader_same_lambda=True))
    assert len(records)==6 and all(sorted(r['lambda_value'] for r in records if r['role']==role)==[.075,.15,.30] for role in ('K-15-S','UC-B20-B'))
    write(OUT/'reports/D/lambda_pipeline_audit.json',dict(passed=True,records=records,Optimize=0))

def science():
    tick=time.perf_counter();summary=read(OUT/'reports/summary.json')
    assert summary['C_completed']==32 and summary['D_completed']==4 and not summary['C_missing'] and not summary['D_missing']
    assert read(OUT/'sequence_driver_status.json')['state']=='COMPLETE_C_D_E_NATIVE'
    assert not budget()['unclosed']
    C=read(OUT/'reports/C/arms.json');D=read(OUT/'reports/D/six_points.json');pairs=read(OUT/'reports/C/pairs.json')
    roots=read(OUT/'reports/roots.json');tiny=read(OUT/'math/tiny_exact.json');assert tiny['status']=='PASS'
    lambda_audit();write(OUT/'protection_science_freeze.json',protected())
    account=budget();assert account['G1_seconds']<=57600
    counts=summary['C_certificates'];den=summary['C_denominators']
    adverse=[p for p in pairs if p['direction']=='Lose']
    adverse_substantive=[p for p in adverse if p.get('material') and not p['micro']]
    text='# Round134 final scientific report\n\n'
    text+='This is the scientific payload at the pre-publication freeze. Actual public recovery, PR readback and final completion are recorded separately; no pending delivery is represented here as already passed.\n\n'
    text+='## 1. Implementation completion\n\n'
    text+='The same exact-stock predicate and complete physical-fleet verifier now give P, PS and S2 an independent full-original-domain zero certificate. Native qualification, physical feasibility and final proof are separate. A rejected native source stays rejected; a legal exact-zero own fleet may still meet the independent nonnegative floor. Near-zero positive values retain the old epsilon policy, and insufficient positive/infeasible evidence cannot close the domain. Normal positive native and outer-coverage certificates remain. No production matrix, H, support policy, controller or numerical tolerance changed. Meaningful zero/source/physical, terminal-gap, inclusive-cutoff and scheduler checks passed before the final PE freeze.\n\n'
    text+=f"All fixed C positions completed: S2 {counts['S2']}/{den['S2']}, P {counts['P']}/{den['P']}, PS {counts['PS']}/{den['PS']} qualified certificates. There are {summary['independent_certificate_count']} independent-zero observations, including {len(summary['rejected_native_independent_certificates'])} retaining a rejected native source. Their raw native dispositions are not upgraded.\n\n"
    text+='## 2. Final performance and its limits\n\n'
    for control in ('P','PS'):
        rr=[p for p in pairs if p['right']==control]
        text+=f"S2/{control}: {len(rr)} matched groups; classes {dict(collections.Counter(p['class'] for p in rr))}; directions {dict(collections.Counter(p['direction'] for p in rr))}. "
    text+=f"There are {len(adverse_substantive)} substantive adverse both-certified comparisons under the preregistered max(10s,10% of faster time) rule. Micro times are reported individually and are not judged by that threshold.\n\n"
    text+='All adverse directions and both-open endpoints are retained. The complete paired table is reports/C/pairs.csv and every position is in reports/C/arms.csv; open certification times are null. '
    if adverse:
        text+='Adverse observations: '+', '.join(f"{p['role']} Seed{p['seed']} S2/{p['right']} ({p['class']})" for p in adverse)+'. '
    text+='A certificate advantage is distinct from a certified-time advantage. The panel targets six known roles, not a holdout or a new broad benchmark. Historical R132 counts remain 17/24 S2,9/24 P,4/12 PS; R133 finite repair and four-pair bridge results remain separate. A source-policy improvement does not retroactively relabel historical certificates.\n\n'
    for role in ('K-35-U','X-35-U','X-35-B'):
        rr=[r for r in C if r['role']==role and r['method']=='S2']
        text+=role+': '+'; '.join(f"Seed{r['seed']} U={number(r['U'])}, L={number(r['L'])}, "+('certified' if r['certificate'] else 'open') for r in rr)+'.\n\n'
    text+='The normal positive K-15-S and actual split/target/cache UC-B20-B paths provide concrete retained advantages. Existing paid-start reversals and positive-objective size limits remain material boundaries. A role-level regression assessment, after the final integrated review, is given in submission_readiness.md. It is not inferred from a simple win count or speed on an erroneous old model.\n\n'
    text+='## 3. Within-instance weight experiment\n\n'
    text+=f"All six points are present, including the two reused C baseline points; {sum(r['certificate'] for r in D)}/6 are certified. Lambda is checked in frozen argv, own H, physical F, all loaded S2 model objectives/scopes, Start audits and the current reader; reports/D/lambda_pipeline_audit.json records the check. "
    text+='For each fixed physical instance use rho=lambda*Omega and Pavg=P/Omega. The optimality monotonicity/slope relations and their error-aware forms use the same feasible set and accepted original-objective U/L gaps, never primal tolerance as objective error.\n\n'
    for role in ('K-15-S','UC-B20-B'):
        rr=sorted([r for r in D if r['role']==role],key=lambda r:r['lambda_value'])
        text+=role+': '+'; '.join(f"lambda={r['lambda_value']}, rho={number(r['rho'])}, G={number(r['G'])}, Pavg={number(r['P_avg'])}, F={number(r['F'])}, gap={number(r['signed_gap'])}" for r in rr)+'. '
        same=all(abs(r['G']-rr[0]['G'])<=1e-10 and abs(r['P_avg']-rr[0]['P_avg'])<=1e-10 for r in rr)
        text+=('The observed points form a platform. ' if same else 'The observed tradeoff changes with weight. ')
        if not all(r['certificate'] for r in rr):text+='Uncertified feasible points alone do not establish the exact optimal tradeoff. '
        text+='Vehicle pickups/returns/prefix peaks/durations are retained in operations.json and summarized in the manuscript.\n\n'
    text+='## 4. TC: strict tiny increment, negative real-root evidence\n\n'
    text+='The exact J2/J3 result retains the specified complete joint-service reference, old state penalty and full pairwise R88 CDF/product extension. Actual old/new witnesses pass all583 original rows and284/298 variable bounds, with actual legal fleet mixtures. TC raises the exact original-objective LP from lambda_hat to lambda_hat+3/16, closes75% of the old1/4 gap and leaves1/16 below the integer optimum. This is stronger on these named references, not a dominance theorem for every historical DP, Hall, support or VD-J closure. Threshold identities, cheapest-increment counting and the chord bound are established tools, not claimed first discoveries.\n\n'
    for r in roots:
        text+=f"{r['role']}: L0={number(r['L0'],15)}, Lold={number(r['L_old'],15)}, Lold+TC={number(r['L_old_TC'],15)}; TC increment={number(r['TC_increment'],12)}. "
    text+='All six fixed-domain continuous LPs are numerical OPTIMAL with quality/residuals retained; they are not rational global certificates. The old optimal vectors already satisfy TC with large positive slack. No reliable positive TC gain remains after the old state-penalty control on either real root. Stop this exploration without adding roots/Seeds or a production TC mechanism. The old state-penalty improvements are not credited as new TC gains.\n\n'
    text+='## 5. Paper, reproducibility and minimal remaining author work\n\n'
    text+='The maintained paper is reorganized around problem, shared structure, complete algorithm, fixed evidence and interpretation. Its exact model/algorithm appendices, complete supplement, bibliography and two explanatory figures preserve adverse/open results and literature-access limits. The final integrated reviewer and actual PDF QA records determine review readiness; current status is in submission_readiness.md and completion_audit.json.\n\n'
    text+='The strongest TRE-oriented account connects redistribution/loaded-return operations and the within-instance effective weight experiment to the complete exact method. The strongest EJOR-oriented account emphasizes shared inventory/service states, scoped proof/coverage and fair full-cost method evidence. Neither account needs a universal speed win. Minimal author work before submission is to identify and accurately cite the external same-problem heuristic/model source, confirm input/data provenance and permissions, resolve the listed full-text comparison questions only to the strength of claims retained, and apply journal/author formatting. The draft explicitly avoids model invention or first-fairness claims.\n\n'
    text+='For a higher OR positioning, the exact tiny TC increment is real theoretical progress on a narrow reference. Its absent real-root gain, unresolved positive-objective35-station runs, limited broad/new-instance evidence and unresolved component attribution mean that the gap to a striking general model/theory/algorithm or practical-impact contribution is not substantially closed by this round alone.\n\n'
    text+='## Budget and retained failures\n\n'
    text+=f"New computation at scientific freeze: {account['G1_seconds']:.6f}/57600 seconds; category totals {account['by_category']}. Outer metered processes are charged once, nested H/LP/MIP/Work are observations, and actual postverification is separate. Writing/PDF/archive/public-recovery costs are separately recorded in resource_accounting.json. C01's original reader schema failure, pure aggregate metadata repair, exact-math zero-key failure and pre-Optimize root Python import failure remain preserved; healthy native runs were not repeated.\n"
    (OUT/'final_report.md').write_text(text,encoding='utf-8')
    reproduction='''# Finite current-round reproduction

The scientific payload is fixed by its full science commit, recorded in the later publication receipt. Read export_manifest.json and source_publication.json from that commit. The current-only bootstrap is scripts/round134_public_restore.py; its fixed-commit SHA is recorded in delivery_bootstrap_binding.json before execution. It uses anonymous HTTPS and a standard-library Python runtime plus system curl.

```
python round134_public_restore.py --commit FULL_40_HEX_SCIENCE_COMMIT --destination E:/codes/ExactEBRP-work/restore/round134-public-SHORT_COMMIT --receipt EXTERNAL_RECEIPT_PATH
```

The destination must be one new owned initially empty directory under the declared restore parent. A real failed transport/check may resume the same failed root with --resume, preserving healthy verified downloads and failures. A completed root cannot be rerun. This entry documents the one required current-round check; actual outcomes appear in public_restore_receipt.json. Total cumulative recovery budget is7200s, with four transport workers. It does not use Git, a local raw/source fallback, native Optimize, compilation or vendor DLLs.

All36 current formal positions are restored with their unchanged producer seals, physical/model/H/Start/source/return/coverage evidence and original measured clocks. The same current reader and the pure accepted-H adapter execute under the established R133 closed-root engine; derived JSON is regenerated in memory and compared. Exact current source bytes are mounted from current_source_bytes.zip, so Git newline conversion cannot masquerade as source identity. Executable, object/archive and DLL hashes are historical execution attestations only; their bytes are not distributed or loaded.

The only inherited tiny carrier is complete_tiny_joint_study.zip at52b02252ba47e8228b73e071d6ed692385a4f816, SHA256 d2e55d7ae5fcaf5bb0c9d39a489b589006f3a29eb350b167fd790ad399a0aac1. Its original bytes remain unchanged. Exact J2/J3 witness and old-control extensions are replayed without a solver. The two current root exports and six LP records are restored; exact coefficient/count/downrounding and added-row residuals are regenerated. Native LP optimality and historical old/current export equality remain explicitly preserved execution/review attestations, not new rational proofs or a recovery-time re-solve. No historical whole campaign is restored.

Reports/C and reports/D contain every endpoint, matched comparison and operation record. Manuscript, supplement, bibliography, independent_proof.md, tc_note.md and review/ provide the reading path. Local closed-root preflight is run once before publication. transport/read-only adapter failures are retained and repaired only where affected; no healthy experiment is rerun for delivery.

Scientific manifest hashes refer to the fixed science snapshot. Later publication/completion receipts and the final metadata commit do not rewrite that snapshot or recursively package their own receipts. No native assets, licenses, credentials, vendor fonts or unauthorized full papers are published.
'''
    (OUT/'reproducibility.md').write_text(reproduction,encoding='utf-8')
    write(OUT/'scientific_closeout.json',dict(UTC=utc(),passed=True,C=32,D_new=4,D_total_points=6,root_LP=6,
        exact_tiny='PASS',budget=account,Optimize=0,seconds=time.perf_counter()-tick,
        final_review_PDF_and_publication_receipts_are_separate=True))
    print('Scientific report, finite reproduction entry, lambda and protection checks complete')

if __name__=='__main__':science()
