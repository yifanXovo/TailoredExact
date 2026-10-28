"""Promote/check the retained GI-TBC entry after the complete frozen study.

Promotion is guarded and reversible. Verification expands actual CLI vectors
without --run; it reads local PE/DLL hashes but never loads or executes them.
"""
from round137_common import *
import argparse, importlib.util

PROFILE=ROOT/'config/gi_tbc_round137.json'
LEGACY=ROOT/'config/paper_s2.json'


def load_launcher():
    spec=importlib.util.spec_from_file_location('round137_paper_launcher',ROOT/'scripts/paper_s2.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def defaults():
    matrix=read(OUT/'matrix_frozen.json')
    rows=[g for g in matrix['groups'] if g['launch']['method']=='S2']
    assert len(rows)==28 and all(g['stage'] in ['B1','B2','B3','D2-main'] for g in rows)
    return matrix,rows


def promote():
    tick=time.perf_counter()
    from round137_analyze import analysis_preflight
    analysis_preflight()
    assert read(OUT/'reports/summary.json')['completed']==120
    decision=read(OUT/'candidate_decision.json')
    assert decision['study_complete'] and decision['decision']=='RETAIN_ACCEPTED_GI_TBC'
    assert decision['default_AM']==.08 and not decision['AP'] and decision['pair_only']
    receipt=OUT/'entry_promotion.json';assert not receipt.exists(),'preserve the actual promotion receipt'
    candidate=read(OUT/'candidate_manifest.json');legacy_SHA=sha(LEGACY)
    assert legacy_SHA==candidate['config_SHA']
    matrix,rows=defaults();config=read(PROFILE);launcher=load_launcher()
    for group in rows:assert launcher.normalize(group['launch']['command'],config)==config['argv']
    historical=config.get('historical_argv_provenance',config['authority'])
    config.update(algorithm='GI-TBC - Gini-interval tailored branch-and-cut',round=137,
        historical_alias='S2',implementation='ms2',source_commit=candidate['source_commit'],
        research_head=candidate['source_commit'],default_executable=candidate['production_PE'],
        verified_PE_SHA256=candidate['production_PE_SHA'],verified_DLL=candidate['DLL'],verified_DLL_SHA256=candidate['DLL_SHA'],
        AP=False,default_AM=.08,maximum_depth=8,minimum_width=1e-4,pair_only=True,H_seed=20260626,
        compatibility_CLI_default='ENS-C',compatibility_config_SHA=legacy_SHA,
        historical_argv_provenance=historical,
        authority=dict(schema='round137-source-and-frozen-matrix-v1',
            candidate_manifest='results/unified_exact_round137/candidate_manifest.json',candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),
            matrix='results/unified_exact_round137/matrix_frozen.json',matrix_SHA=sha(OUT/'matrix_frozen.json'),
            normalized_default_launches_compared=len(rows),scope='Complete normalized token vectors; actual CLI dry runs have their own receipt'))
    write(PROFILE,config)
    path=ROOT/'scripts/paper_s2.py';before=sha(path);text=path.read_text(encoding='utf-8-sig')
    old="CONFIG = ROOT / 'config/paper_s2.json'";new="CONFIG = ROOT / 'config/gi_tbc_round137.json'"
    assert text.count(old)==1 or text.count(new)==1
    text=text.replace(old,new)
    text=text.replace('Expand the complete frozen R135 S2 argv; run only with --run.',
        'Expand the complete frozen Round137 GI-TBC argv (historical S2); run only with --run.')
    text=text.replace('local R135-compatible executable; default uses verified R135 PE',
        'local GI-TBC-compatible executable; default uses verified Round137 PE')
    text=text.replace('verified R135 PE','verified Round137 PE').replace('verified R135 DLL','verified Round137 DLL')
    text=text.replace('frozen S2 vector','frozen GI-TBC vector')
    path.write_text(text,encoding='utf-8',newline='\n')
    verifier=ROOT/'scripts/verify_paper_s2.py';verifier_before=sha(verifier)
    wrapper='\n'.join(['"""Bounded zero-native check of the current GI-TBC entry and frozen vectors."""',
        'from round137_entry import verify_cli','',"if __name__=='__main__':",'    raise SystemExit(verify_cli())',''])
    verifier.write_text(wrapper,encoding='utf-8',newline='\n')
    assert sha(LEGACY)==legacy_SHA
    value=dict(UTC=utc(),method='GI-TBC',implementation='ms2',historical_alias='S2',source_commit=candidate['source_commit'],
        PE_SHA=candidate['production_PE_SHA'],config_SHA=sha(PROFILE),legacy_config_SHA=legacy_SHA,
        legacy_config_bytes_unchanged=True,normalized_default_vectors_checked=len(rows),
        paper_entry_before_SHA=before,paper_entry_after_SHA=sha(path),verifier_before_SHA=verifier_before,verifier_after_SHA=sha(verifier),
        decision_SHA=sha(OUT/'candidate_decision.json'),actual_CLI_check_still_required=True,
        minimal_change='Config pointer and human-facing labels; parser/execution logic retained',
        default_off_controls=True,per_instance_dispatch=False,Optimize=0,compile=0,
        separate_entry_promotion_seconds=time.perf_counter()-tick)
    write(receipt,value);print(json.dumps(value))
    return value


def verify():
    tick=time.perf_counter()
    candidate=read(OUT/'candidate_manifest.json');matrix,rows=defaults();config=read(PROFILE)
    assert read(OUT/'candidate_decision.json')['study_complete']
    assert sha(LEGACY)==candidate['config_SHA']==config['compatibility_config_SHA']
    authority=config['authority']
    assert config['historical_argv_provenance']==read(LEGACY)['authority']
    assert authority['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
    assert authority['matrix_SHA']==sha(OUT/'matrix_frozen.json')
    assert config['source_commit']==candidate['source_commit'] and config['verified_PE_SHA256']==candidate['production_PE_SHA']
    assert config['default_AM']==.08 and not config['AP'] and config['pair_only']
    launcher=load_launcher();assert launcher.CONFIG==PROFILE
    promotion=read(OUT/'entry_promotion.json')
    assert promotion['config_SHA']==sha(PROFILE) and promotion['legacy_config_SHA']==sha(LEGACY)
    assert promotion['paper_entry_after_SHA']==sha(ROOT/'scripts/paper_s2.py')
    assert promotion['verifier_after_SHA']==sha(ROOT/'scripts/verify_paper_s2.py')
    checks=[];dry_root=WORK/'temp/round137/entry-argv-only'
    for group in rows:
        launch=group['launch'];panel=launch['panel'];output=dry_root/launch['arm_id'];assert not output.exists()
        assert launcher.normalize(launch['command'],config)==config['argv']
        args=[str(PYTHON),'-B',str(ROOT/'scripts/paper_s2.py'),'--input',str(ROOT/panel['input_path']),
            '--out-dir',str(output),'--T',str(panel['T_seconds']),'--pickup-time',str(panel['pickup_seconds']),
            '--drop-time',str(panel['drop_seconds']),'--lambda',str(panel['lambda']),
            '--cap',str(launch['cap_seconds']),'--seed',str(launch['seed']),'--json']
        assert '--run' not in args
        actual=json.loads(subprocess.check_output(args,cwd=ROOT))
        assert actual['dry_run'] and not output.exists() and actual['matches_verified_PE'] and actual['matches_verified_DLL']
        assert actual['config_SHA256']==sha(PROFILE) and actual['source_commit']==candidate['source_commit']
        assert launcher.normalize(actual['command'],config)==config['argv']
        def fixed(argv,flag):return argv[argv.index(flag)+1]
        for flag in ['--T','--pickup-time','--drop-time','--lambda','--time-limit','--process-wall-time-limit','--gurobi-seed']:
            assert float(fixed(actual['command'],flag))==float(fixed(launch['command'],flag))
        assert actual['input_SHA256']==panel['input_sha256']
        assert all(flag not in actual['command'] for flag in ['--round135-aggregate-penalty','--round137-delete-ab','--round137-delete-cr','--round137-delete-cg'])
        checks.append(dict(position=group['position'],arm=launch['arm_id'],stage=group['stage'],seed=launch['seed'],
            tokens=len(actual['command']),whole_vector_equal_after_allowed_normalization=True,
            physical_experiment_values_equal=True,input_SHA256=actual['input_SHA256'],no_output_created=True))
    first=rows[0]['launch']['panel']
    example=[str(PYTHON),'-B',str(ROOT/'scripts/paper_s2.py'),'--input',str(ROOT/first['input_path']),
        '--out-dir',str(dry_root/'refusal'),'--T',str(first['T_seconds']),'--cap','600','--seed','0']
    refusals=[]
    for name,extra in [('existing_output',['--out-dir',str(ROOT)]),('insufficient_cap',['--cap','36']),
        ('negative_seed',['--seed','-1']),('nonfinite_weight',['--lambda','nan']),
        ('algorithm_override',['--round137-delete-ab']),('AP_override',['--round135-aggregate-penalty'])]:
        checked=subprocess.run([*example,*extra],cwd=ROOT,capture_output=True)
        assert checked.returncode!=0 and not (dry_root/'refusal').exists()
        refusals.append(dict(case=name,rejected=True,no_output_created=True))
    sources={name:sha(ROOT/name)==digest for name,digest in candidate['source_hashes'].items()}
    helpers={name:sha(ROOT/name)==digest for name,digest in matrix['helpers'].items()}
    assert all(sources.values()) and all(helpers.values())
    return dict(status='PASS_BOUNDED_ZERO_NATIVE_ENTRY_CHECK',UTC=utc(),round=137,method='GI-TBC',
        all_S2_launches=checks,all_default_GI_launches=len(checks),refusal_checks=refusals,
        source_commit=candidate['source_commit'],production_sources_checked=len(sources),execution_helpers_checked=len(helpers),
        production_sources_match_actual_frozen_R137=True,config_SHA=sha(PROFILE),legacy_config_SHA=sha(LEGACY),
        entry_script_SHA=sha(ROOT/'scripts/paper_s2.py'),verifier_script_SHA=sha(ROOT/'scripts/verify_paper_s2.py'),
        entry_helper_SHA=sha(ROOT/'scripts/round137_entry.py'),matrix_SHA=sha(OUT/'matrix_frozen.json'),
        candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),promotion_receipt_SHA=sha(OUT/'entry_promotion.json'),
        historical_argv_provenance_matches_immutable_legacy_authority=True,
        legacy_R135_config_unchanged=True,current_authority='Round137 candidate/matrix hashes; historical16-vector R135 provenance remains separate',
        asset_hash_reads='Local PE/DLL byte hashes only; no library loading/execution',new_native_seconds=0,new_Optimize=0,
        vendor_DLL_loads=0,recompile=0,formal_performance_samples_added=0,
        separate_entry_verification_seconds=time.perf_counter()-tick,
        scope='Complete actual CLI vectors, parameters and source/binary identities; not a campaign or another native reproduction')


def verify_cli():
    parser=argparse.ArgumentParser(description=verify.__doc__)
    parser.add_argument('receipt',type=Path,nargs='?');args=parser.parse_args()
    value=verify()
    if args.receipt:
        args.receipt.parent.mkdir(parents=True,exist_ok=True)
        with args.receipt.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=value['status'],GI_launches=value['all_default_GI_launches'],
        sources=value['production_sources_checked'],helpers=value['execution_helpers_checked'],native_seconds=0)))
    return 0


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['promote','verify']);args=parser.parse_args()
    if args.action=='promote':promote()
    else:print(json.dumps(verify()))
