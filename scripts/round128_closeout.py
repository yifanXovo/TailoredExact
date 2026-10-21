"""Small fee closure and English PR text; never starts an experiment."""
from round128_common import *
import csv

def account():
    assert not budget()['unclosed'],budget()
    d=OUT/'fees/read_only_administrative_allowance'
    if not d.exists():
        d.mkdir(parents=True)
        write(d/'launch.json',dict(UTC=utc(),kind='administrative_allowance',command=[],
            scope='Conservative allowance for bounded unmetered shell reads, source/metadata review and small preparation/receipt writes; not a native runtime or a claimed CPU measurement',
            no_subprocess_or_Optimize=True))
        write(d/'receipt.json',dict(exit_code=0,outer_seconds=180,start_unix=None,end_unix=None,
            conservative_upper_allowance=True,not_observed_child_elapsed=True,nested_native_seconds_added=False))
    records=[]
    for path in sorted((OUT/'fees').glob('*/launch.json')):
        launch=read(path);receipt=read(path.parent/'receipt.json')
        records.append(dict(label=path.parent.name,kind=launch['kind'],outer_seconds=receipt['outer_seconds'],exit_code=receipt['exit_code'],
            conservative_upper_allowance=receipt.get('conservative_upper_allowance',False),launch_SHA=sha(path),receipt_SHA=sha(path.parent/'receipt.json')))
    b=budget();assert b['paid_outer_seconds']<=TOTAL_LIMIT
    # Packing excludes its own live meter and all later receipts. Retain these
    # small facts directly in closeout metadata; never repack the carriers.
    late=[]
    archive=OUT/'raw_archive_manifest.json'
    if archive.exists():
        import gzip
        packed=set()
        for entry in read(archive)['archives']:
            members=json.loads(gzip.decompress((ROOT/entry['member_index']['path']).read_bytes()))
            packed.update(m['path'] for m in members)
        for row in records:
            folder=OUT/'fees'/row['label']
            if (folder/'receipt.json').relative_to(ROOT).as_posix() not in packed:
                late.append(dict(label=row['label'],launch=read(folder/'launch.json'),receipt=read(folder/'receipt.json')))
    value=dict(UTC=utc(),total_outer_limit=TOTAL_LIMIT,paid_outer_seconds=b['paid_outer_seconds'],remaining_outer_seconds=b['remaining_outer_seconds'],
        by_kind=b['by_kind'],preledger_upper_seconds=read(OUT/'initialization.json')['preledger_outer_upper_seconds'],
        actual_closed_child_lifetimes_and_separately_labelled_allowances=True,fees=records,post_archive_fee_facts=late,open_fees=[],
        formal_nominal_seconds=15600,qualification_soft=1200,qualification_limit=3000,maximum_plan=19200,
        qualification_build_actual_seconds=b['by_kind'].get('build',0)+b['by_kind'].get('qualification',0),
        H_LP_MIP_seconds_are_nested_not_added_again=True,no_formal_outcome_retry=True)
    write(OUT/'resource_accounting.json',value);print(json.dumps({k:v for k,v in value.items() if k not in ['fees']}))

def pr_body():
    s=read(OUT/'stratified_summary.json');decision=read(OUT/'scientific_decision.json');identity=read(OUT/'E2_frozen.json')
    lines=['Round128 replaces the blocked inclusive-root research specification with **MD-R v1**, a legal own-U0 root control. The old no-improver shortcut can exclude an equal-cutoff physical witness; MD-R omits only that semantically marked pseudo-infeasibility row, retaining valid domains and strengthening. Frozen M-B / GI-TBC remains the sole proposed algorithm. Ordinary MB, MS2 and cold P retain their original implementation paths.',
        'This Draft PR is stacked on `codex/round127-integrated-diagnostics` at measured parent `'+BASE+'`. R127 remains **PARTIAL**, with all three original MD arms unstarted. No historical result is rewritten as a completed MD observation.',
        '**Execution: '+s['execution']+'. Scientific judgment: `'+decision['tag']+'`.** '+decision['rationale'],
        'The fixed same-E2 panel contains **16 arms, 17 typed shared-arm comparisons and three distinct known inputs**: Seed0 P/MB/MD-R/MS2 on all three roles, plus only MB/MS2 at Seed1 on K1/K2. Every MB-type arm independently pays complete H; P is independently paid original cold compact, without H/Start/cutoff. Full production clocks, separate verification/total clocks, null uncertified T_cert, raw signed gaps and all open/adverse outcomes are retained. There is no tuning, additional evaluation input, expanded Seed panel, cap extension or performance-driven retry. Artificial boundary fixtures remain separately identified qualification work.',
        '| Core Seed0 comparison | Typed statuses | Directions |','| --- | --- | --- |']
    for k,v in s['core_by_comparison'].items():lines.append('| '+k+' | '+str(v['classes'])+' | '+str(v['directions'])+' |')
    lines.extend(['', 'The two additional Seed1 support comparisons remain a separate layer: '+str(s['additional_support_Seed1']['classes'])+'; directions '+str(s['additional_support_Seed1']['directions'])+'. Each Seed has one matched observation per role; shared arms and repeated inputs are not independent trials.',
        'MD-R uses its own fixed inclusive root, full actual own-Start validation before LP, one complete LP and one complete root MIP, with no child/target/rebuild. Numerical relevance cannot waive that paid chain, and a TIME_LIMIT/INTERRUPTED return cannot become native optimality. The valid regional floor is min(L_a,c) by actual-domain/cutoff-complement coverage, not a clamp hiding a contradictory witness. Equality and the 1e-9 numerical band are stated separately.',
        'Qualification includes shared/fallback sentinel-only differences, an equal-cutoff physical fleet, shared endpoints and loaded return, actual tiny-positive-U0 calls, a real time-limited open root, full small/medium E1/E2 model/VType/bound/objective/settings/H bridges, and an independent source/Start/physical/return review. A preliminary qualification Start-counter serialization failure and its full paid producer remain rejected and preserved. None of the nine saved R127 core MB matrices contains the sentinel; this is a finite impact check, not universal historical revalidation.',
        'MS2 deletes only triple support rows, retaining pairs, ordered supply, enumeration order and the original shared cap. Actual same-H/root differences and controller exposure are checked after formal execution. Absence of actual splits restricts any D interpretation to probing, target handoff and scheduling. All certification risk and K3 endpoints remain visible; no per-instance winner is adopted.',
        'The maintained manuscript/PDF retains the R125 model/cuts derivations and all R127 Seed/tiny/PT findings, including PT 0/3 versus default P 1/3 on its separate held-out E1 roles. This round does not demonstrate superiority to the strongest possible Gurobi tuning. '+decision['next_priority'],
        'All formal arms use E2 PE SHA256 `'+identity['PE_SHA']+'` and unchanged Gurobi 13.0.2 DLL SHA256 `'+identity['DLL_SHA']+'`. No executable, DLL, license, credential, font file or external full paper is published. Current-round finite raw carriers, failed evidence, full source bindings and the recovery manifest are included.'])
    recovery=OUT/'public_restore_receipt.json'
    if recovery.exists() and read(recovery)['status']=='PASS':
        r=read(recovery);lines.append('One anonymous empty-root recovery passed from science commit `'+r['science_commit']+'`, with '+str(r['files'])+' declared files and zero Optimize/native starts/compilation. Its exact finite scope and retained failures are in `public_restore_receipt.json`.')
    else:lines.append('The single anonymous empty-root recovery is performed only after this science commit is remotely readable; the actual receipt will be added as closeout metadata without rerunning the panel.')
    lines.append('Evidence entry point: `results/unified_exact_round128/final_report.md`; complete arms/pairs, support two-Seed table, component costs/differences, source seal, review actions and maintained reading PDF are beside it.')
    if (OUT/'review/final_independent_review.md').is_file():
        lines.append('A separate final executor recomputed all 17 directions and denominators from original receipts and checked the actual MD-R root/own Start, boundary sentinel difference, MS2 deletion, nonempty physical fleet, matched H/root scope and observed controller exposure. The exact finite scope and limitations are retained in `review/final_independent_review.md`; no full rational-matrix proof or external replication is claimed.')
    body='\n\n'.join(lines).replace(' |\n\n| ',' |\n| ')
    (OUT/'pr_body.md').write_text(body+'\n',encoding='utf-8');print('English stacked Draft PR body written')

if __name__=='__main__':{'account':account,'pr-body':pr_body}[sys.argv[1]]()
