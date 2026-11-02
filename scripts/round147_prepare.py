"""Bounded identities, sealed reuse and zero-Optimize wrapper/reader qualification."""
import copy
import collections
import shutil
import round133_campaign as inherited
from round147_read import root_context
import round108_reader as parser
from round147_common import *

configure()


def initial():
    configure()
    assert not (OUT / 'start_receipt.json').exists()
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile('C:/Users/Administrator/Downloads/TailoredExact_Round147_Complete_Goal.md', OUT / 'goal.md')
    protected = Path('E:/codes/ExactEBRP')
    status = git('status', '--porcelain=v1', '--untracked-files=no', cwd=protected).decode()
    (OUT / 'protected_original_tracked_status.txt').write_text(status, encoding='utf-8')
    changed = [line[3:] for line in status.splitlines()]
    hashes = {name: sha(protected / name) for name in changed}
    old = inherited._candidate(OLD / 'candidate_manifest.json')
    manifest = {k: copy.deepcopy(old[k]) for k in ['source_commit', 'source_hashes', 'production_PE',
        'production_PE_SHA', 'research_PE', 'research_PE_SHA', 'DLL', 'DLL_SHA']}
    manifest.update(schema='round147-wrapper-reuses-round146-production-v1',
        inherited_manifest=dict(commit=SCIENCE146, path='results/unified_exact_round146/candidate_manifest.json',
                                SHA256=sha(OLD / 'candidate_manifest.json')),
        wrapping_round=147, delivery_base=BASE, production_recompiled=False,
        algorithm='GI-TBC + standalone direct state-conditioned GD', root_once=True,
        new_rows_max=2, new_columns=0, source_solves=0,
        stable_profile_SHA=sha(ROOT / 'config/gi_tbc_round137.json'),
        old_GD_entry_SHA=sha(ROOT / 'scripts/paper_s2_gd.py'),
        old_GD_profile_SHA=sha(ROOT / 'config/gi_tbc_gd_round146.json'))
    write(OUT / 'candidate_manifest.json', manifest)
    profile = read(ROOT / 'config/gi_tbc_round137.json')
    profile.update(schema='round147-standalone-GD-frozen-argv-v1',
        algorithm='GI-TBC + standalone direct state-conditioned Gini deviation rows',
        source_commit=manifest['source_commit'], research_head=manifest['source_commit'],
        default_executable=manifest['production_PE'], verified_PE_SHA256=manifest['production_PE_SHA'],
        round=147, source_manifest='results/unified_exact_round147/candidate_manifest.json',
        research_profile=True, GD=True, STOCK=False,
        parent_profile_SHA256=sha(ROOT / 'config/gi_tbc_round137.json'))
    profile['argv'] += ['--round146-gd', 'on']
    write(ROOT / 'config/gi_tbc_gd_round147.json', profile)
    active_status = git('status', '--porcelain=v1', '--untracked-files=no').decode()
    assert not active_status, active_status
    write(OUT / 'start_receipt.json', dict(UTC=utc(), branch=git('branch', '--show-current').decode().strip(),
        base=BASE, actual_main=git('ls-remote', 'origin', 'refs/heads/main').decode().split()[0],
        R146_in_main=False, PR_base='codex/round146-direct-gini-deviation',
        predecessor_PR=dict(number=208, open=True, Draft=True, head=BASE), goal_SHA=sha(OUT / 'goal.md'),
        protected_original=str(protected), protected_modified_file_hashes=hashes,
        protected_tracked_status_SHA=sha(OUT / 'protected_original_tracked_status.txt'),
        active_tree_tracked_clean_at_entry=True, preexisting_untracked_old_round_assets_retained=True,
        no_preexisting_solver_seen=True, production_recompiled=False, ceiling_seconds=18000,
        Gurobi_Seed=0, H_seed=20260626, threads=1, serial=True, affinity_mask=4,
        attachments=dict(goal=True, stage_review=False, review_evidence_zip=False),
        policy='All new assets in ExactEBRP-work; bounded current-round post-PR cleanup only'))
    print('Recorded Round147 identities; unchanged R146 PE; stable and old GD entries preserved')


def reuse():
    configure()
    source = OLD / 'reports/full.json'
    public = json.loads(git('show', SCIENCE146 + ':results/unified_exact_round146/reports/full.json'))
    full = read(source)
    assert full == public and len(full['new_arms']) == 7 and not full['pending']
    manifest = read(OUT / 'candidate_manifest.json')
    records = []
    for row in full['new_arms']:
        matrix_path = OLD / (row['batch'] + '_matrix.json')
        matrix = read(matrix_path)
        group = matrix['groups'][row['position'] - 1]
        camp = OLD / group['group']
        identity_path = camp / 'identity.json'
        assert sha(identity_path) == group['identity_SHA']
        identity = read(identity_path)
        launch = identity['launches'][0]
        destination = Path(launch['destination'])
        assert sha(launch['panel']['input_path']) == row['input_SHA']
        assert row['PE_SHA'] == manifest['production_PE_SHA']
        assert row['DLL_SHA'] == manifest['DLL_SHA']
        assert row['source_commit'] == manifest['source_commit']
        assert row['seed'] == 0 and row['H_complete']
        assert launch['command'][launch['command'].index('--threads') + 1] == '1'
        assert launch['command'][launch['command'].index('--mip-threads') + 1] == '1'
        stock = row['method'] != 'BASE'
        gd = row['method'] == 'STOCK_GD'
        assert ('--round138-stock-rlt' in launch['command']) == stock
        assert launch['command'][launch['command'].index('--round146-gd') + 1] == ('on' if gd else 'off')
        control = read(destination / 'round146_control_audit.json')
        assert control['PASS'] and all(m['stock_rows'] == (4 if stock else 0) and
            m['GD_rows'] == (2 if gd else 0) for m in control['models'])
        seal = read(destination / 'producer_seal.json')
        for name, digest in seal['required_SHA'].items():
            assert sha(destination / name) == digest, (row['role'], name)
        closeout = read(destination / 'verification_closeout.json')
        assert all(closeout[k] for k in ['necessary_verification_complete',
            'implementation_qualified', 'evidence_complete', 'native_proof_qualified', 'performance_eligible'])
        assert sha(destination / 'audit.json') == closeout['audit_SHA']
        receipt = read(OLD / 'fees' / f'{row["batch"]}_{row["position"]:03}' / 'receipt.json')
        records.append(dict(role=row['role'], method=row['method'], round=146, fixed_science=SCIENCE146,
            batch=row['batch'], position=row['position'], source_row=row,
            evidence_kind='same_PE_cross_round_sealed_reference', new_round147_charge_seconds=0,
            original_fee_seconds=receipt['outer_seconds'], original_start_unix=receipt['start_unix'],
            original_end_unix=receipt['end_unix'], identity_SHA=sha(identity_path),
            matrix_SHA=sha(matrix_path), producer_seal_SHA=sha(destination / 'producer_seal.json'),
            verification_closeout_SHA=sha(destination / 'verification_closeout.json'),
            control_SHA=sha(destination / 'round146_control_audit.json'),
            timing_caveat='Same PE and resource settings, across rounds/time periods; no claim of identical load',
            own_H=True, no_solution_cuts_or_state_transferred=True))
    write(OUT / 'reuse_index.json', dict(PASS=True, UTC=utc(), fixed_science=SCIENCE146,
        full_report_SHA=sha(source), old_cells=records, old_formal_cells=7,
        qualifications_reused=['qualification_exact_rows.json', 'qualification_native_writer.json',
                               'qualification_units.json'],
        historical_LP_new_Optimize=0, new_Optimize=0, Native_load=0,
        old_cost_not_recharged=True, old_production_and_stable_identity_retained=True))
    print('Verified and indexed seven sealed same-PE historical cells; zero new Optimize')


def qualify():
    configure()
    assert not budget()['unclosed']
    from round147_campaign import admission
    import paper_s2 as baseline
    from types import SimpleNamespace
    profile = read(ROOT / 'config/gi_tbc_gd_round147.json')
    facts = []
    for group in read(OUT / 'core_matrix.json')['groups']:
        launch = group['launch']
        panel = launch['panel']
        config = copy.deepcopy(profile)
        config['argv'][-1] = 'on' if launch['R147_method'] == 'GD' else 'off'
        args = SimpleNamespace(input=Path(panel['input_path']), out_dir=Path(launch['destination']),
            T=str(panel['T_seconds']), pickup_time='60', drop_time='60',
            lambda_value=str(panel['lambda']), cap=launch['cap_seconds'], seed=launch['seed'], exe=None, run=False)
        plan = baseline.plan(args, config)
        assert baseline.normalize(launch['command'], config) == baseline.normalize(plan['command'], config)
        assert '--round138-stock-rlt' not in launch['command']
        facts.append(dict(arm=launch['arm_id'], method=launch['R147_method'],
            STOCK=False, GD=config['argv'][-1] == 'on', normalized_argv_equal=True))
    fixture = OLD / 'qualification/writer/zero_lower'
    on, off = parser.lp_model(fixture / 'on.lp'), parser.lp_model(fixture / 'off.lp')
    assert on == off
    block, support, meta = root_context(fixture, dict(total_initial=3, Q_vector=[3]), True,
        OUT / 'qualification/zero_lower/rows.json', [], fixture_model=fixture / 'on.lp')
    assert block['rows'] == [] and meta['rows'] == 0 and not meta['applicable']
    empty = OUT / 'qualification/H_no_model'
    assert root_context(empty, {}, True, empty / 'unused.json', []) == (None, None, None)
    manifest = read(OUT / 'candidate_manifest.json')
    assert sha(ROOT / 'scripts/paper_s2_gd.py') == manifest['old_GD_entry_SHA']
    assert sha(ROOT / 'config/gi_tbc_gd_round146.json') == manifest['old_GD_profile_SHA']
    write(OUT / 'qualification_wrapper_reader.json', dict(PASS=True, UTC=utc(), argv=facts,
        zero_lower_fixture=dict(source_commit=SCIENCE146, source=str(fixture),
            on_SHA=sha(fixture / 'on.lp'), off_SHA=sha(fixture / 'off.lp'),
            actual_models_equal=True, GD_rows=0, renamed_GD_file_required=False,
            actual_root_metadata_used=True, exact_arithmetic_driver_reused=True),
        H_finished_without_model=True, old_entry_profile_unchanged=True,
        no_recompile=True, no_repeated_health=True, Optimize=0, Native_load=0))
    print('PASS normalized argv, zero-row actual model, H/no-model, preserved old entry')


def charge_preflight():
    """Conservatively charge observed host-tool outer timings, without invention."""
    configure()
    assert not budget()['unclosed']
    target = OUT / 'infra/external_costs.json'
    assert not target.exists(), 'Do not count a captured probe twice'
    observations = [
        ('2a8704', 'initial sealed-reference qualification; closeout-schema KeyError', .6676746, 1),
        ('57e9e3', 'wrapper/zero-lower reader fixture qualification', .8046038, 0),
        ('d42f16', 'corrected sealed-reference qualification', 1.0260383, 0)]
    write(target, dict(UTC=utc(), accounting_reconciliation=True,
        clock='exec_command returned wall_time_seconds for the original outer processes',
        conservative_charge_includes_pure_readonly_or_arithmetic_qualification=True,
        no_reexecution=True, no_overlap_with_metered_fees=True,
        processes=[dict(tool_chunk=chunk, description=description, kind='diagnostic', outer_seconds=seconds,
            exit_code=code, Optimize=0, Native_load=0, old_experiment_not_repeated=True)
            for chunk, description, seconds, code in observations]))
    print(json.dumps(dict(charged_preflight_seconds=sum(r[2] for r in observations), budget=budget())))


def entry():
    """Exercise the new public CLI parser without --run; no model or Native load."""
    configure()
    facts = []
    import paper_s2 as baseline
    profile = read(ROOT / 'config/gi_tbc_gd_round147.json')
    for group in read(OUT / 'core_matrix.json')['groups'][:2]:
        launch = group['launch']
        panel = launch['panel']
        gd = 'on' if launch['R147_method'] == 'GD' else 'off'
        output = TEMP / ('entry_dry_' + gd)
        assert not output.exists()
        command = [PYTHON, '-B', ROOT / 'scripts/paper_s2_gd_only.py', '--input', panel['input_path'],
            '--out-dir', output, '--T', str(panel['T_seconds']), '--lambda', str(panel['lambda']),
            '--cap', str(launch['cap_seconds']), '--seed', '0', '--gd', gd, '--json']
        run = subprocess.run(list(map(str, command)), cwd=ROOT, env=environment(),
                             capture_output=True, text=True, timeout=30)
        assert run.returncode == 0, run.stderr
        plan = json.loads(run.stdout)
        assert plan['dry_run'] and plan['GD'] == (gd == 'on') and plan['STOCK'] is False
        assert plan['matches_verified_PE'] and plan['matches_verified_DLL'] and not output.exists()
        assert baseline.normalize(plan['command'], profile) == baseline.normalize(launch['command'], profile)
        facts.append(dict(method=launch['R147_method'], expanded_plan=plan, actual_CLI=True))
    write(OUT / 'entry_check.json', dict(PASS=True, UTC=utc(), entry_SHA=sha(ROOT / 'scripts/paper_s2_gd_only.py'),
        profile_SHA=sha(ROOT / 'config/gi_tbc_gd_round147.json'), facts=facts,
        no_output_directory_created=True, Optimize=0, Native_load=0, compile=0))
    print('PASS actual standalone GD on/off CLI vectors; zero Optimize or Native load')


if __name__ == '__main__':
    globals()[sys.argv[1]]()
