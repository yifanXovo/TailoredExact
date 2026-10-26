"""Bounded publication comparison after this execution's independent raw audit.

No primary mathematics, native model parser, optimizer or original-root fallback
is imported here. The inputs are the already independently reconstructed arms
and explicit-root primary tables. Large models are not read a second time.
"""
from collections import Counter
import csv, io, json, math
from round110_independent_final_core import VIOLATION


def scalar(value):
    if value == '':
        return None
    if value in ('True', 'False'):
        return value == 'True'
    if value.startswith(('[', '{')):
        return json.loads(value)
    try:
        return float(value)
    except ValueError:
        return value


def key(row):
    return row['campaign'], row['id'], int(row['seed']), row['arm']


def compare(a, value, reports, document_paths):
    tables = {}

    def table(name, optional=False):
        if name not in tables:
            path = reports/(name+'.csv')
            a.require(path.is_relative_to(a.root), 'publication table stays inside explicit root')
            if not path.exists() and optional:
                tables[name] = []
            else:
                tables[name] = list(csv.DictReader(io.StringIO(a.txt(path))))
        return tables[name]

    def require_equal(actual, expected, label, tolerance=1e-7):
        if expected is None:
            valid = actual is None
        elif isinstance(expected, bool):
            valid = actual is expected
        elif isinstance(expected, (int, float)):
            valid = isinstance(actual, (int, float)) and math.isfinite(actual) and abs(actual-expected) <= tolerance
        else:
            valid = actual == expected
        a.require(valid, 'independent publication '+label+': '+repr(actual)+' / '+repr(expected))

    def one(name, ownkey, **extra):
        rows = [r for r in table(name) if key(r) == ownkey and all(r[n] == str(v) for n, v in extra.items())]
        a.require(len(rows) == 1, 'exact unique publication '+name+' '+repr(ownkey)+' '+repr(extra))
        return rows[0]

    arms = value['own_actual_arms']
    qualification = value['qualification']['functional_arms']
    combined = [('qualification/cli01', arm) for arm in qualification]+[('campaign', arm) for arm in arms]
    published = table('arms')
    pqualification = table('qualification_arms')
    selection = a.obj(reports/'selection_decision.json')
    summary = a.obj(reports/'summary.json')
    a.require(len(published) == len(arms) == 42 and len(pqualification) == len(qualification) == 5,
              'all42 independently reconstructed formal attempts and five qualification endpoints published')
    endpoints, mechanisms, qualification_clocks, call_total, returned_total, missing_total = [], [], [], 0, 0, 0
    native_table = table('native_calls')
    model_table = table('models')
    start_table = table('starts', optional=True)
    physical_table = table('physical_UBs')
    actual_native_keys, actual_model_keys, actual_start_keys = set(), [], set()
    for campaign, arm in combined:
        ownkey = (campaign, arm['id'], arm['seed'], arm['arm'])
        b = one('arms' if campaign == 'campaign' else 'qualification_arms', ownkey)
        for field in ('U', 'L', 'gap', 'relative_gap', 'certificate', 'PE_SHA', 'DLL_SHA'):
            require_equal(scalar(b[field]), arm.get(field), repr(ownkey)+' '+field)
        directory = a.local(next(l['destination'] for l in a.obj(a.out/(campaign+'/identity.json'))['launches']
                                 if (l['id'], l['seed'], l['arm']) == (arm['id'], arm['seed'], arm['arm'])))
        if campaign != 'campaign':
            whole = a.obj(directory/'whole_arm_receipt.json')
            a.require(whole['completion_SHA'] == a.sha(directory/'completion.json') and whole['audit_SHA'] == a.sha(directory/'audit.json') and
                      whole['includes_admission_identity_checks_startup_native_calls_callbacks_raw_writes_postexit_audit_crosscheck'],
                      'actual qualification whole receipt binds complete original work')
            require_equal(scalar(b['complete_seconds']), whole['complete_seconds'], repr(ownkey)+' actual qualification whole clock', 1e-9)
            qualification_clocks.append(dict(id=arm['id'], seed=arm['seed'], arm=arm['arm'],
                                             original_whole_seconds=whole['complete_seconds'],
                                             supervisor_legacy_seconds=arm['complete_seconds'],
                                             whole_receipt_SHA=a.sha(directory/'whole_arm_receipt.json')))
        else:
            require_equal(scalar(b['complete_seconds']), arm['complete_seconds'], repr(ownkey)+' original full clock', 1e-9)
        if arm['complete_seconds'] is None and campaign == 'campaign':
            require_equal(scalar(b['complete_seconds_interval']), arm['complete_seconds_interval'], repr(ownkey)+' original outward clock interval')
        if campaign == 'campaign':
            for field in ('formal_protocol_qualified', 'formal_performance', 'full_clock_within_frozen_cap'):
                # Signed recovery endpoints can omit this old-reader field;
                # its independently verified interval still qualifies its cap.
                if b.get(field, '') != '':
                    require_equal(scalar(b[field]), arm[field], repr(ownkey)+' '+field)
            if not arm['formal_protocol_qualified']:
                require_equal(b['formal_protocol_failure'], VIOLATION, 'actual42 formal failure')
                require_equal(scalar(b['full_clock_cap_excess_seconds']), arm['full_clock_cap_excess_seconds'], 'actual42 excess', 1e-9)
            endpoints.append(dict(id=arm['id'], seed=arm['seed'], arm=arm['arm'], U=arm['U'], L=arm['L'], gap=arm['gap'],
                                  certificate=arm['certificate'], complete_seconds=arm['complete_seconds'],
                                  complete_seconds_interval=arm.get('complete_seconds_interval'),
                                  formal_protocol_qualified=arm['formal_protocol_qualified']))
        observations = a.obj(directory/'observations.json')
        declared = {o['payload']['call']: o['payload'] for o in observations if o['payload']['kind'] == 'call'}
        skipped = {o['payload']['call'] for o in observations if o['payload']['kind'] == 'not_started'}
        returned = {o['payload']['call'] for o in observations if o['payload']['kind'] == 'returned'}
        a.require(set(declared)-skipped == {call['call'] for call in arm['native_records']},
                  'independent actual Optimize records cover every original unskipped call')
        for number, call in declared.items():
            r = one('native_calls', ownkey, call=number)
            payload = declared[number]
            require_equal(scalar(r['actual_Optimize']), number not in skipped, 'actual Optimize retained')
            require_equal(scalar(r['returned']), number in returned, 'original returned journal flag retained')
            require_equal(r['model_SHA'], payload['model_sha256'], 'current exact call model SHA')
            require_equal(scalar(r['full_original']), payload['full_original'], 'original full_original flag retained')
            require_equal(scalar(r['native_bound_preconditions']), payload['native_preconditions'], 'original native prerequisite flag retained')
            require_equal(scalar(r['settings']), payload['settings'], 'actual current call numerical settings')
            for field, rawfield in (('gini_lower', 'lower_g'), ('gini_upper', 'upper_g'), ('cutoff', 'cutoff')):
                require_equal(scalar(r[field]), payload[rawfield], 'actual current call '+field, 1e-12)
            if number in skipped:
                continue
            actual_native_keys.add(ownkey+(number,))
            record = next(c for c in arm['native_records'] if c['call'] == number)
            require_equal(scalar(r['native_bounds_mathematically_qualified']), record.get('native_bounds_mathematically_qualified', True),
                          'current lower-claim qualification')
            absent = number not in returned
            require_equal(scalar(r['returned_journal_missing']), absent, 'original missing returned event preserved')
            independently_proved = scalar(r['actual_normal_return_from_independent_rc_source'])
            a.require(isinstance(independently_proved, bool) and (not absent or independently_proved) and
                      (not independently_proved or arm['normal_completion']['returncode'] == 0),
                      'separate actual rc0 proof may coexist with returned event; every missing event requires independent proof')
            t = [q for q in table('native_type_readbacks') if key(q) == ownkey and q['model_SHA'] == record['model_SHA'] and
                 q['log_SHA'] == record['native_log_SHA']]
            a.require(len(t) == 1, 'actual native type/log readback unique')
            require_equal(scalar(t[0]['restored_native_types']), record['native_types'], 'actual restored native VType')
            call_total += 1
            returned_total += number in returned
            missing_total += absent
        for contract in arm['model_contracts']:
            contract_path = contract['path'].replace('\\','/')
            matches = [r for r in model_table if key(r) == ownkey and r['path'] == contract_path]
            a.require(len(matches) == 1, 'every original saved model publication is unique')
            r = matches[0]
            require_equal(r['SHA'], contract['SHA'], 'saved model byte identity')
            for field, independent in (('rows','rows'), ('columns','columns'), ('quantity_columns','quantity_columns'),
                                       ('frozen_A_B_rows_checked','AB_exact_rows')):
                require_equal(scalar(r[field]), contract[independent], 'saved model '+field, 0)
            require_equal(r['quantity_type'], 'C' if arm['arm'] == 'M-B' else 'I', 'p/d actual formulation domain')
            a.require(scalar(r['route_load_Y_integer']) is True and scalar(r['state_assignment_direction_binary']) is True,
                      'original route/load/Y and binary state/mode constraints reported')
            actual_model_keys.append(ownkey+(contract_path,))
        for start in arm['starts']:
            metadata_path = start['metadata_path'].replace('\\','/')
            r = one('starts', ownkey, start_path=metadata_path)
            for field, independent in (('start_sha256','metadata_SHA'), ('vector_sha256','values_SHA'), ('model_sha256','model_SHA'),
                                       ('columns','columns'), ('rows','rows_checked')):
                require_equal(scalar(r[field]), start[independent], 'all-column Start '+field, 0)
            a.require(scalar(r['per_column_restored_type_checked']) is True and scalar(r['ordered_native_columns_checked']) is True,
                      'actual submitted Start ordered columns and restored type reported')
            actual_start_keys.add(ownkey+(metadata_path,))
        ph = arm['physical']
        fleet = one('physical_fleets', ownkey)
        for field, independent in (('F','U'), ('G','G'), ('P','P')):
            require_equal(scalar(fleet[field]), ph[independent], 'own complete physical '+field)
        require_equal(scalar(fleet['Y']), ph['final_inventories'], 'own final station inventories')
        require_equal(scalar(fleet['complete_fleet_vehicles']), len(ph['routes']), 'complete physical vehicle namespace', 0)
        require_equal(scalar(fleet['total_return_load']), sum(r['return_load'] for r in ph['routes']), 'depot return inventory conservation', 0)
        cars = {int(c['vehicle']): c for c in scalar(fleet['cars'])}
        a.require(set(cars) == {r['vehicle'] for r in ph['routes']}, 'every own vehicle duration/return partition published')
        for route in ph['routes']:
            car = cars[route['vehicle']]
            for field, independent in (('pickup','total_pickup'), ('station_drop','total_station_drop'), ('return_unload','return_load'),
                                       ('travel_seconds','travel_seconds'), ('handling_seconds','handling_seconds'), ('closed_duration_seconds','duration_seconds')):
                require_equal(car[field], route[independent], 'own per-vehicle '+field)
        witnesses = [o['payload'] for o in observations if o['payload']['kind'] == 'witness']
        ubrows = [r for r in physical_table if key(r) == ownkey]
        a.require(len(ubrows) == len(witnesses)+1, 'every own committed physical UB plus final complete fleet published')
        for witness in witnesses:
            r = [q for q in ubrows if scalar(q['sequence']) == witness['sequence']]
            a.require(len(r) == 1, 'own journal witness publication unique')
            for field in ('F', 'G', 'P'):
                require_equal(scalar(r[0][field]), witness['objective' if field == 'F' else field], 'own committed witness '+field)
            require_equal(scalar(r[0]['native_first_find_exact']), False, 'no invented exact native first-discovery clock')
        kinds = Counter(c['solve_kind'] for c in arm['native_records'])
        am = a.rows(directory/'external/adaptive_mass_decision_ledger.csv') if (directory/'external/adaptive_mass_decision_ledger.csv').exists() else []
        events = a.rows(directory/'external/paper_tree_events.csv') if (directory/'external/paper_tree_events.csv').exists() else []
        targets = a.rows(directory/'external/native_target_ledger.csv') if (directory/'external/native_target_ledger.csv').exists() else []
        trace = a.rows(directory/'external/global_bound_trace.csv') if (directory/'external/global_bound_trace.csv').exists() else []
        for row in am:
            gap = float(row['U'])-float(row['B_p'])
            require_equal(float(row['proof_gap']), gap, 'actual AM proof gap')
            if gap > 1e-7:
                gains = [(float(row[n])-float(row['B_p']))/gap for n in ('B_L','B_R')]
                for n, gain in zip(('g_L_raw','g_R_raw'), gains):
                    require_equal(float(row[n]), gain, 'actual AM gain')
                gains = [min(1.,max(0.,g)) for g in gains]
                score = min(gains)*sum(gains)/2
                require_equal(float(row['S_AM']), score, 'actual AM score')
        mechanism = dict(campaign=campaign, id=arm['id'], seed=arm['seed'], arm=arm['arm'], actual_Optimize=len(arm['native_records']),
                         solve_kinds=dict(kinds), AM_actions=dict(Counter(row['selected_action'] for row in am)),
                         tree_events=dict(Counter(row['event'] for row in events)),
                         target_kind_counts=dict(Counter(row['target_kind'] for row in targets)),
                         maximum_open_relevant_leaves=max((int(row['open_relevant_leaf_count']) for row in trace), default=0),
                         actual_atomic_splits=len((arm.get('cover') or {}).get('actual_atomic_split_events', [])))
        m = one('mechanism_summary', ownkey)
        require_equal(scalar(m['initial_own_physical_U']), witnesses[0]['objective'] if witnesses else None, 'actual own startup physical U0')
        require_equal(scalar(m['reported_integer_witnesses']), len(witnesses), 'actual committed physical witness count', 0)
        for field, expected in (('actual_native_Optimize',len(arm['native_records'])), ('LP_calls',kinds['LP']),
                                ('terminal_MIP_calls',kinds['MIP']), ('child_bound_target_MIP_calls',kinds['CHILD_BOUND_TARGET_MIP']),
                                ('next_leaf_target_MIP_calls',kinds['NEXT_LEAF_TARGET_MIP']),
                                ('partial_target_MIP_calls',kinds['CHILD_BOUND_TARGET_MIP']+kinds['NEXT_LEAF_TARGET_MIP'])):
            require_equal(scalar(m[field]), expected, 'actual mechanism '+field, 0)
        require_equal(scalar(m['AM_action_counts']), mechanism['AM_actions'], 'actual AM actions')
        require_equal(scalar(m['actual_tree_event_counts']), mechanism['tree_events'], 'actual tree events')
        require_equal(scalar(m['maximum_open_relevant_leaves']), mechanism['maximum_open_relevant_leaves'], 'actual observed active leaves', 0)
        a.require(scalar(m['lookahead_LP_is_committed_split']) is False and
                  scalar(m['quantity_type_and_A_B_causal_contributions_reidentified']) is False,
                  'lookahead/partition distinction and no new p/d/A-B causal identification')
        mechanisms.append(mechanism)
        if campaign == 'campaign':
            for point in arm['checkpoints']:
                r = one('checkpoints', ownkey, seconds=point['seconds'])
                require_equal(scalar(r['observed']), point['observed'], 'fixed checkpoint observed window')
                for field in ('U','L','gap'):
                    require_equal(scalar(r[field]), point[field], 'qualified own fixed checkpoint '+field)
            time_partition = one('time_partitions', ownkey)
            require_equal(scalar(time_partition['complete_seconds']), arm['complete_seconds'], 'untrimmed time partition whole', 1e-9)
            require_equal(scalar(time_partition['nested_native_seconds_added']), False, 'no native double billing')
            if arm['complete_seconds'] is not None:
                require_equal(scalar(time_partition['partition_sum']), arm['complete_seconds'], 'complete time partition sums to raw whole', 1e-8)
            else:
                require_equal(scalar(time_partition['partition_sum']), None, 'unknown exact partition remains null')
                require_equal(scalar(time_partition['complete_seconds_interval']), arm['complete_seconds_interval'], 'untrimmed time partition interval')
    a.require(len([r for r in native_table if scalar(r['actual_Optimize']) is True]) == call_total == len(actual_native_keys),
              'published actual Optimize count has no omitted or extra calls')
    a.require(len(model_table) == len(actual_model_keys) and len(start_table) == len(actual_start_keys),
              'published models and actually submitted all-column Starts have no omitted or extra records')
    selected = value['selection']
    pairs = [*selected['main_pairs'].values(), *selected['other_main_pairs'], *selected['seed1_pairs'].values()]
    pp = table('pairs')+table('seed_pairs')
    a.require(len(pp) == len(pairs) == 39, 'all36 main comparisons and three prescribed Seed comparisons published')
    pair_keys = set()
    for own in pairs:
        pairkey = (own['id'], own['seed'], own['candidate'], own['control'])
        matches = [r for r in pp if (r['id'],int(r['seed']),r['candidate'],r['control']) == pairkey]
        a.require(len(matches) == 1 and pairkey not in pair_keys, 'every frozen comparison unique')
        pair_keys.add(pairkey)
        row = matches[0]
        # Names/basis prose differ between independently implemented readers;
        # compare every common mathematical/classification/materiality field.
        for field, expected in own.items():
            if field in row and field not in ('basis', 'panel_kind'):
                require_equal(scalar(row[field]), expected, 'frozen pair '+repr(pairkey)+' '+field)
    for field in ('stage','blocking_reasons','completed_native_formal_attempts','qualified_formal_arms','all42_valid_formal'):
        require_equal(selection[field], selected[field], 'strict final stage '+field)
    require_equal(summary['stage'], 'BLOCKED', 'primary summary strict final stage')
    for field in ('formal_arms','native_normal_formal_attempts'):
        require_equal(summary[field], 42, 'actual42 '+field, 0)
    require_equal(summary['qualified_formal_arms'], 41, '41 formal clock-qualified attempts', 0)
    require_equal(summary['all42_valid_formal'], False, 'actual42 not all formally valid')
    for data in (selection, summary):
        require_equal(data['evaluable_seed_pairs'], 2, 'only two evaluable Seed comparisons', 0)
        require_equal(data['formally_evaluable_seed_nonLOSS'], 2, 'evaluated Seed nonLOSS excludes UNEVALUABLE', 0)
        require_equal(data['Seed_sensitivity_assessment_complete'], False, 'incomplete formal Seed sensitivity')
    require_equal(selection['main_counts'].get('WIN',0), selected['main_WIN'], 'main WIN count', 0)
    require_equal(selection['main_counts'].get('LOSS',0), selected['main_LOSS'], 'main LOSS count', 0)
    require_equal(selection['seed_counts'], dict(Counter(p['classification'] for p in selected['seed1_pairs'].values())), 'actual Seed classes')
    require_equal(selection['main_severe_P_regressions'], selected['main_severe_P_regressions'], 'actual main severe P regressions', 0)
    require_equal(selection['seed_severe_P_regressions'], selected['seed1_severe_regressions'], 'evaluable Seed severe P regressions', 0)
    require_equal(selection['Seed0_WIN_to_Seed1_LOSS'], selected['seed0_WIN_to_seed1_LOSS'], 'observed Seed WIN-to-LOSS flips')
    require_equal(selection['reason_codes'], [], 'BLOCKED is not completed positive or negative performance decision')
    require_equal(selection['unassessed_support_conditions'], selected['unassessed_support_conditions'], 'blocked stage support predicates retained separately')
    strata = {name: len(wins) for group in selection['stratum_WIN_roles'].values() for name, wins in group.items()}
    require_equal(strata, selected['stratum_WIN'], 'actual size/geometry WIN strata')
    require_equal(summary['PE_SHA'], value['production_PE_SHA'], 'one final production PE identity')
    require_equal(summary['DLL_SHA'], value['DLL_SHA'], 'one unchanged DLL identity')
    require_equal(summary['actual_Optimize'], call_total, 'all qualification/formal actual Optimize count', 0)
    require_equal(summary['Optimize_returned'], returned_total, 'all actual returned journal events', 0)
    require_equal(summary['independently_proved_actual_native_returns_without_journal'], missing_total, 'separate missing-return rc0 evidence', 0)
    require_equal(summary['actual_native_returns_including_independent_rc_sources'], call_total, 'all actual successful API returns accounted', 0)
    require_equal(summary['route_oracle'], 0, 'no route oracle', 0)
    require_equal(summary['IIS'], 0, 'no IIS', 0)
    require_equal(summary['independent_engine_performance_rerun'], False, 'no solver rerun')
    provenance = {}
    for label, expected_exit in (('primary_final01',1), ('final_report_qualifiers01',0)):
        directory = a.out/'engineering'/label
        launch, receipt = a.obj(directory/'launch.json'), a.obj(directory/'receipt.json')
        a.require(receipt['exit_code'] == expected_exit and receipt['engineering'] and receipt['conservative_solver_starts'] == 0 and
                  receipt['stdout_SHA'] == a.sha(directory/'stdout.log') and receipt['stderr_SHA'] == a.sha(directory/'stderr.log'),
                  'actual zero-native primary reconstruction/annotation execution '+label)
        a.require(launch['sources'] == receipt['sources'], 'actual captured execution source inventory '+label)
        for name, digest in launch['sources'].items():
            a.require(a.sha(directory/'source_snapshot'/name) == digest, 'actual retained execution source '+label+' '+name)
        if label == 'primary_final01':
            error = a.txt(directory/'stderr.log')
            a.require('FileExistsError: [Errno 17] File exists:' in error and 'summary.json' in error and
                      "frozen.write(args.out/'summary.json', summary)" in error,
                      'retained original primary failure is final metadata exclusive-write after complete raw reconstruction')
        else:
            a.require(launch['sources']['scripts/round110_final_reader.py'] == summary['primary_reader_entry_SHA'] == a.sha(a.root/'scripts/round110_final_reader.py') and
                      launch['sources']['scripts/round110_report_qualifiers.py'] == summary['report_qualifier_source_SHA'] == a.sha(a.root/'scripts/round110_report_qualifiers.py'),
                      'current final reader and deterministic metadata correction are exactly source-bound')
        provenance[label] = dict(exit_code=receipt['exit_code'], engineering_seconds=receipt['seconds'],
                                 launch_SHA=a.sha(directory/'launch.json'), receipt_SHA=a.sha(directory/'receipt.json'),
                                 original_source_bindings=launch['sources'], Optimize=0, native_environment=0)
    budget = value['budget']
    fee_rows = table('fees')
    require_equal(summary['conservative_starts'], budget['paid_starts'], 'all enclosing conservative starts', 0)
    require_equal(summary['outer_solver_fee_seconds'], budget['paid_outer_seconds'], 'all enclosing outer fee seconds', 1e-8)
    require_equal(sum(int(r['conservative_process_starts']) for r in fee_rows), budget['paid_starts'], 'fee table retains every paid failed slot', 0)
    require_equal(sum(float(r['outer_seconds']) for r in fee_rows), budget['paid_outer_seconds'], 'fee table enclosing clocks', 1e-8)
    a.require(len(fee_rows) == len(value['fee_records']) and budget['paid_starts'] == 80 and
              abs(budget['paid_outer_seconds']-68982.26150893699) < 1e-8,
              'closed actual budget80/68982.26150893699 including failed wrappers and original lost slots')
    a.require(not table('unstarted', optional=True) and not table('failures', optional=True),
              'all42 native processes normal; formal clock breach separately preserved')
    floors = table('analytical_full_domain_bounds')
    expected_floors = {('G50-C1',0,'P-GRB'), ('G50-C2',0,'P-GRB'), ('G100-C1',0,'M-B'), ('G100-C1',0,'P-GRB')}
    a.require({(r['id'],int(r['seed']),r['arm']) for r in floors} == expected_floors and len(floors) == 4,
              'exact four current separately signed own full-domain floors')
    for row in floors:
        a.require(scalar(row['L']) == 0 and scalar(row['native_bound']) is False and scalar(row['borrowed_ENS_bound_or_certificate']) is False,
                  'all current original-domain floors separate from rejected native and another arm')
    frontier = [r for r in table('frontier') if (r['id'],int(r['seed']),r['arm']) == ('G100-C1',0,'M-B') and r['campaign'] == 'campaign']
    damaged_seen = False
    for row in frontier:
        damaged_seen = damaged_seen or row['event_type'].startswith('native_') or 'terminal_mip' in row['event_source']
        require_equal(scalar(row['raw_native_claim_mathematically_qualified']), not damaged_seen, 'persistent damaged scoped lower/cover provenance')
        require_equal(scalar(row['necessary_dependent_native_closure_withdrawn']), damaged_seen, 'persistent scoped closure withdrawal')
        if damaged_seen:
            require_equal(scalar(row['recomputed_complete_cover_bound']), 0, 'separate own full-domain floor after scoped rejection', 0)
    documents = {p.relative_to(a.root).as_posix(): a.txt(p).replace('\r\n','\n') for p in document_paths}
    a.require(documents, 'actual final narrative documents supplied for independent readback')
    final_text = documents[(a.out/'final_report.md').relative_to(a.root).as_posix()]
    # These exact statements bind the final reporting semantics; additional
    # numerical mechanism/fleet assertions are independently checked above.
    for needle in ('BLOCKED', VIOLATION, '3600.7215734999627', '3600.707823600038', 'UNEVALUABLE', '41', '42', '80', '68982.26150893699'):
        a.require(needle in final_text, 'final narrative required actual fact '+needle)
    narrative_predicates = {
        'final_report.md': (
            '**Unique stage: BLOCKED.**', '41 arms have qualifying complete clocks.',
            'Seed sensitivity assessment is incomplete.',
            'No cap was extended, time truncated, or performance arm rerun.',
            'ENS-C remains the default', '158 actual Optimize calls have',
            '156 returned journal events plus two independently proved normal returns',
            'There is **no real parent split in this round**',
            'Cross-arm witnesses are only exact-domain',
            'never that arm\'s UB, Start or online oracle.',
            'Missing returned events are formal P17 and M-B25 call4',
            'no qualified arm supplies a3600 performance observation',
            'G100-R1/R2 zero optimum is unproved.',
            'FileExistsError', 'without repeating mathematics or performance.'),
        'paper_candidate_spec.md': (
            'The present decision is BLOCKED',
            'G100-R2 is UNEVALUABLE due to its complete',
            'No formal stability or', 'completed paper-benchmark claim follows.',
            'These are additional finite observations of the inherited candidate, not new',
            'mathematical or algorithmic contributions.'),
        'reproduce.md': (
            'From the RESTORED cwd, its own common.py must invoke its own final reader:',
            'Never invoke worktree common.py for restored-root work.',
            'with --mode public', 'no --dll.', 'The final per-arm cap breach remains blocking'),
        'current_numerical_evidence.md': (
            'Own P26 U=.21697499525901037 remains positive/open',
            'It supplies no', 'P26 incumbent.',
            'LP calls1–3 stay distinct supported relaxation proofs',
            'All call4 native lower claims, including final zero, are',
            'independently of native.'),
        'RESUME.md': (
            'All fees are CLOSED:80conservative starts/68982.261508937outer seconds.',
            'G50-R1WIN,G100-R2UNEVALUABLE.',
            'No remaining research solve.',
            'Own positives15/26 remain open at original floor0; ownzero17/25 independently'),
    }
    checked_fragments = []
    for basename, fragments in narrative_predicates.items():
        name = (a.out/basename).relative_to(a.root).as_posix()
        a.require(name in documents, 'required actual final narrative '+name)
        text = documents[name]
        for needle in fragments:
            a.require(needle in text, 'independent final narrative required statement '+basename+' '+needle)
            checked_fragments.append(dict(file=name, required_statement=needle))
    a.require('Current completed count26, never-started27–42' not in
              documents[(a.out/'current_numerical_evidence.md').relative_to(a.root).as_posix()],
              'retained arm26 pause chronology must not be represented as final current state')
    table_sha = {p.name: a.sha(p) for p in sorted(reports.glob('*.csv'))}
    return dict(decision='ACCEPT_INDEPENDENT_BLOCKED_PUBLICATION_AND_NARRATIVE', stage='BLOCKED',
                all42_actual_endpoints_and_39_frozen_comparisons_agree=True, all_models_native_types_Starts_physical_fleets_and_mechanisms_agree=True,
                actual_Optimize=call_total, journal_returned=returned_total, separately_proved_missing_journal_returns=missing_total,
                qualified_formal_arms=41, all42_valid_formal=False, evaluable_seed_pairs=2, formally_evaluable_seed_nonLOSS=2,
                Seed_sensitivity_assessment_complete=False, strict_full_clock_blocker=VIOLATION,
                native_full_clock_flag_not_substituted=True, clock_trimmed=False, performance_rerun=False,
                own_endpoints=endpoints, own_mechanisms=mechanisms, qualification_whole_clocks=qualification_clocks, primary_table_SHA=table_sha,
                actual_primary_execution_provenance=provenance,
                primary_selection_SHA=a.sha(reports/'selection_decision.json'), primary_summary_SHA=a.sha(reports/'summary.json'),
                narrative_SHA={p.relative_to(a.root).as_posix(): a.sha(p) for p in document_paths},
                narrative_statement_checks=checked_fragments,
                later_operations_delivery_receipts_not_yet_reviewed=True)
