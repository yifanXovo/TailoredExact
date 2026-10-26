"""Actual admission and final/restored six-arm review, with exclusive receipts.

Main36 is a fixed audited import. The current two qualification or six formal
arms are independently reconstructed by the signed kernel and R111 core.
No performance helper or primary report implementation supplies mathematics.
"""
from pathlib import Path
from collections import Counter
import argparse
import ast
import copy
import csv
import datetime
import difflib
import hashlib
import json
import math
import os
import sys
import time
import traceback
from round111_import_main import Tee, write, digest
from round111_independent_core import Audit, ROUND, PE, DLL
import round111_independent_decision as decision

MAIN_IMPORT_SHA = '74cb24e040d2fa6d2efcc2614a9d90aaceaa6355ad17ed382f48731094c12049'
QUALIFICATION_RAW_SHA = 'c02b868bcf846b0811de8e738e8b4cc5b70996291b7e3bd52b1035dec40a8f9d'
PATH_OPTIONS = {'--out','--log','--process-phase-ledger','--external-gini-artifact-dir',
                '--primal-heuristic-generation-log','--progress-log','--native-evidence-dir','--gurobi-model-export'}


def argv_map(command):
    options = {}
    i = 1
    while i < len(command):
        key = command[i]
        assert key.startswith('--') and key not in options
        if key in ('--plain-baseline','--round100-continuous-quantities'):
            options[key] = True;i += 1
        else:
            assert i+1 < len(command)
            options[key] = command[i+1];i += 2
    return options


def finite_equal(a,actual,expected,label,tolerance=0.):
    if isinstance(expected,bool) or expected is None or isinstance(expected,str):
        valid = type(actual) is type(expected) and actual == expected
    elif isinstance(expected,(int,float)):
        valid = isinstance(actual,(int,float)) and math.isfinite(actual) and abs(actual-expected) <= tolerance
    elif isinstance(expected,list):
        valid = isinstance(actual,list) and len(actual) == len(expected)
        a.require(valid,label+' list shape')
        for index,(x,y) in enumerate(zip(actual,expected)):
            finite_equal(a,x,y,label+'/'+str(index),tolerance)
        return
    elif isinstance(expected,dict):
        a.require(isinstance(actual,dict) and set(actual) == set(expected),label+' all fields including unknown fields')
        for key,value in expected.items():
            finite_equal(a,actual[key],value,label+'/'+key,tolerance)
        return
    else:
        valid = actual == expected
    a.require(valid,label+': '+repr(actual)+' / '+repr(expected))


def inherited_main(a):
    folder = a.out/'review/inherited_main03'
    a.require(a.sha(folder/'audit.json') == MAIN_IMPORT_SHA,'fixed independent main36 import signature')
    audit,receipt = a.obj(folder/'audit.json'),a.obj(folder/'receipt.json')
    a.require(receipt['exit_code'] == 0 and receipt['audit_SHA'] == MAIN_IMPORT_SHA and
              audit['decision'] == 'ACCEPT_FIXED_R110_MAIN36_IMPORT','actually executed main36 import acceptance')
    a.require(audit['inherited_science_commit'] == 'c4efe042bc6654ccd2e14b7e0d65c904a15d3390' and
              audit['verified_R110_head'] == '13ed7eeb83b647f585837638ed9158b84f274d66' and
              audit['original_full_independent_audit_SHA'] == '958616d42215a6ee60d468a1f717182d59825ca230db5c82ff8c0b0fa5c09cab',
              'fixed actually executed historical raw authority')
    for path,expected in audit['retained_bindings'].items():
        a.require(a.sha(a.local(path)) == expected,'all finite retained import bytes '+path)
    records = a.obj(folder/'main36_actual_independent_records.json')
    rows = a.obj(folder/'main36_imported_rows.json')
    clocks = a.obj(folder/'main36_original_clock_evidence.json')
    derivations = a.obj(folder/'main36_qualification_derivations.json')
    a.require(len(records) == len(rows) == len(clocks) == 36 and len(derivations) == 4,'finite exact imported36 and explicit four empty fields')
    for index,(record,row,clock) in enumerate(zip(records,rows,clocks),1):
        a.require(record['formal_protocol_qualified'] is True and row['imported_formal_protocol_qualified'] is True and
                  clock['formal_protocol_qualified'] is True and (record['id'],record['arm'],record['seed']) == (row['id'],row['arm'],int(row['seed'])),
                  'each original independently qualified main record '+str(index))
        interval = [record['complete_seconds']]*2 if record['complete_seconds'] is not None else record['complete_seconds_interval']
        a.require(all(math.isfinite(v) for v in interval) and 0 < interval[0] <= interval[1] <= float(row['cap_seconds']),
                  'each entire original clock interval fits its original cap')
        a.require((row['formal_protocol_qualified'] == '') == (index in (15,17,25,26)), 'original empty qualification fields retained')
    a.require(audit['preserved_old_round110_stage'] == 'BLOCKED' and audit['preserved_old_all42_valid_formal'] is False,
              'old R110 invalid arm42 never requalified')
    # Reconstruct published primitives from every retained original table value,
    # preserving the original signed tiny gap; native-audit primitives stay in
    # the separate immutable records and already checked dual comparison.
    primitives = []
    from round111_import_main import Import
    for row in rows:
        value = {k:Import.value(row.get(k,'')) for k in ('U','L','gap','certificate','certificate_qualified','numbers_qualified',
                                                        'complete_seconds','complete_seconds_interval')}
        value.update(id=row['id'],seed=int(row['seed']),arm=row['arm'],PE_SHA=row['PE_SHA'],DLL_SHA=row['DLL_SHA'],formal_protocol_qualified=True)
        primitives.append(value)
    original_pairs = a.obj(folder/'main36_published_primitive_recomputed_pairs.json')
    for expected in original_pairs:
        candidate = next(v for v in primitives if (v['id'],v['arm']) == (expected['id'],expected['candidate']))
        control = next(v for v in primitives if (v['id'],v['arm']) == (expected['id'],expected['control']))
        finite_equal(a,a.decision['pair'](candidate,control),expected,'fixed independently recomputed main pair')
    roles = {v['id']:v for v in a.obj(folder/'authority/input_manifest.json')['roles']}
    return primitives,roles,audit


def actual_qualification(a):
    directory = a.out/'review/qualification_raw01'
    a.require(a.sha(directory/'audit.json') == QUALIFICATION_RAW_SHA,'exact actually executed two-CLI independent raw signature')
    value,receipt = a.obj(directory/'audit.json'),a.obj(directory/'receipt.json')
    a.require(value['decision'] == 'ACCEPT_ACTUAL_H100_TWO_CLI_RAW_QUALIFICATION' and receipt['exit_code'] == 0 and
              receipt['audit_SHA'] == QUALIFICATION_RAW_SHA and value['Optimize'] == value['native_environment'] == 0,
              'actual independent qualification execution passed without native launch')
    for path,expected in value['read_bindings'].items():
        a.require(a.sha(a.local(path)) == expected,'unchanged previously checked actual CLI raw/source '+path)
    a.require(value['qualification_identity_SHA'] == a.sha(a.out/'qualification/cli01/identity.json'),
              'original actually executed CLI identity remains immutable')
    return value


def identities(a,mode,pe_path,dll_path):
    production = a.obj(a.out/'production_identity.json')
    candidate = a.obj(a.out/'candidate_identity.json')
    campaign = a.obj(a.out/'campaign/identity.json')
    qualification = a.obj(a.out/'qualification/cli01/identity.json')
    a.require(production['production_PE_SHA'] == candidate['production_PE_SHA'] == campaign['candidate_binary_sha256'] == PE and
              production['DLL_SHA'] == candidate['DLL_SHA'] == campaign['dll_sha256'] == DLL,'unchanged actual PE DLL identities')
    a.require(production['source_bindings'] == candidate['source_bindings'] == campaign['source_hashes'] == qualification['source_hashes'] and
              len(production['source_bindings']) == 205,'same complete205 production bindings')
    for path,expected in production['source_bindings'].items():
        a.require(a.sha(a.root/path) == expected,'unchanged production source '+path)
    a.require(candidate['helpers'] == campaign['helpers'] and campaign['runner_sha256'] == a.sha(a.root/'scripts/round111_campaign.py'),
              'same final candidate/formal helper and runner identities')
    for path,expected in campaign['helpers'].items():
        a.require(a.sha(a.root/path) == expected,'all final performance helper bytes '+path)
    a.require(candidate['production_identity_SHA'] == a.sha(a.out/'production_identity.json') and
              candidate['protocol_SHA'] == campaign['prereg_sha256'] == qualification['prereg_sha256'] == a.sha(a.out/'protocol.json') and
              candidate['campaign_identity_SHA'] == a.sha(a.out/'campaign/identity.json') and
              candidate['qualification_campaign_identity_SHA'] == a.sha(a.out/'qualification/cli01/identity.json'),
              'exact final production/protocol/campaign/CLI bindings')
    if mode == 'public':
        restore = a.obj(a.root/'restore_receipt.json')
        a.require(restore['exit_code'] == 0 and restore['public_files_only'] and not restore['original_workspace_reads'] and
                  Path(restore['restored_root']).resolve() == a.root,'actual restored explicit-root public boundary')
        a.require(not a.local(campaign['launches'][0]['command'][0]).exists() and pe_path is None and dll_path is None,
                  'public mode excludes PE DLL and private binary fallback')
    else:
        a.require(pe_path is not None and dll_path is not None,'declared actual local PE and DLL paths')
        a.require(hashlib.sha256(Path(pe_path).read_bytes()).hexdigest() == PE and
                  hashlib.sha256(Path(dll_path).read_bytes()).hexdigest() == DLL,'independently rehashed actual PE DLL bytes without loading them')
    return production,candidate,campaign,qualification


def panel(a,campaign,admission):
    old = a.obj(a.out/'review/inherited_main03/authority/campaign_identity.json')['launches'][36:42]
    current = campaign['launches']
    a.require(len(current) == 6 and sum(v['cap_seconds'] for v in current) == 12600,'fixed six observations and12600 nominal seconds')
    for number,(launch,previous,expected) in enumerate(zip(current,old,decision.EXPECTED),1):
        a.require((launch['id'],launch['arm'],launch['cap_seconds']) == expected and launch['number'] == number and
                  launch['old_R110_number'] == previous['number'] == number+36 and launch['seed'] == launch['panel']['gurobi_seed'] == 1,
                  'exact fixed role order old-to-new map and Seed1')
        finite_equal(a,launch['panel'],previous['panel'],'same complete inherited per-arm panel')
        old_options,current_options = argv_map(previous['command']),argv_map(launch['command'])
        a.require(set(old_options) == set(current_options) and
                  all(current_options[k] == old_options[k] for k in current_options if k not in PATH_OPTIONS),
                  'all actual native options unchanged except new own output paths')
        for key in PATH_OPTIONS & set(current_options):
            a.require(a.local(current_options[key]).is_relative_to(a.local(launch['destination'])), 'all outputs stay in own arm')
        a.require('--round100-continuous-quantities' not in current_options and current_options['--process-shutdown-margin'] == '30' and
                  current_options['--gurobi-seed'] == '1' and current_options['--threads'] == current_options['--mip-threads'] == '1',
                  'unchanged integer state-only M-B Seed1 single-thread30-second reserve')
        a.require(a.sha(a.root/launch['panel']['input_path']) == launch['panel']['input_sha256'],'exact frozen current input bytes')
        if admission:
            a.require(not a.local(launch['destination']).exists(),'formal arm absent before actual independent signature')
    return current


def envelope(a,fixture_root):
    value = a.obj(a.out/'qualification/envelope.json')
    plan = a.obj(a.out/'replay_plan.json')
    a.require(value['passed'] and value['helper_SHA'] == a.sha(a.root/'scripts/round111_seed_audit.py') and
              value['replay_plan_SHA'] == a.sha(a.out/'replay_plan.json') and
              value['counterexamples_SHA'] == a.sha(a.out/'qualification/counterexamples01/audit.json'),'actual byte-bound fixed envelope')
    a.require(plan['equivalence_whitelist'] == ['/offline_audit_seconds','/neutral_exchange/offline_seconds'],
              'only two explicitly corrected nonmathematical replay timers excluded')
    observed = value['observations']
    a.require([r['number'] for r in observed] == [37,38,39,40,41,42,42,42] and len(observed) == 8,
              'all fixed fresh-process observations including three arm42 costs retained')
    all_labels = [v['label'] for v in observed]+['new_H100_P_replay01','new_H100_MB_replay01']
    compared = []
    for label in all_labels:
        directory = a.out/'qualification/replays'/label
        receipt = a.obj(directory/'receipt.json')
        if label in {v['label'] for v in observed}:
            source = next(v for v in observed if v['label'] == label)
            a.require(source['receipt_SHA'] == a.sha(directory/'receipt.json'),'exact fresh-process envelope receipt binding')
            a.require(0 <= receipt['necessary_postexit_seconds'] <= 15 and receipt['optimized_phase_metrics']['cached_models_after_clear'] == 0,
                      'every actual necessary postexit fits15 seconds and arm cache is cleared')
        a.require(receipt['kind'] == 'new' and receipt['error'] is None and receipt['comparison']['exact_recursive_equal'] and
                  receipt['comparison']['excluded'] == plan['equivalence_whitelist'] and receipt['Optimize'] == 0,
                  'all current replay mathematical outputs claimed exact')
        sample = next(v for v in plan['samples'] if v['number'] == receipt['number'] and
                      (v['campaign'] != 'campaign') == receipt['qualification_fixture'])
        original_path = sample['launch']['destination'].replace('\\','/')
        original_path = original_path[original_path.index('results/'):]
        path = Path(fixture_root)/original_path/'audit.json'
        baseline_bytes = path.read_bytes()
        a.require(digest(baseline_bytes) == receipt['comparison']['baseline_SHA'],'frozen actual old audit bytes for exact comparison')
        current_bytes = a.data(directory/'audit.json')
        a.require(digest(current_bytes) == receipt['comparison']['current_SHA'],'actual new replay bytes for exact comparison')
        baseline,current = json.loads(baseline_bytes),json.loads(current_bytes)
        for obj in (baseline,current):
            obj.pop('offline_audit_seconds',None)
            if 'neutral_exchange' in obj:
                obj['neutral_exchange'].pop('offline_seconds',None)
        finite_equal(a,current,baseline,'all decisive and unknown original/new replay fields')
        compared.append(dict(label=label,baseline_SHA=digest(baseline_bytes),current_SHA=digest(current_bytes),necessary_postexit_seconds=receipt['necessary_postexit_seconds']))
    counter = a.obj(a.out/'qualification/counterexamples01/audit.json')
    a.require(counter['passed'],'actual counterexample suite acceptance')
    policy = a.obj(a.out/'review/finite_policy01/audit.json')
    policy_receipt = a.obj(a.out/'review/finite_policy01/receipt.json')
    a.require(policy['decision'] == 'ACCEPT_FINITE_CURRENT_NUMERICAL_RETURN_SCOPE_POLICY' and policy_receipt['exit_code'] == 0 and
              policy_receipt['audit_SHA'] == a.sha(a.out/'review/finite_policy01/audit.json') and
              policy['actual_roles'] == [15,17,25,26] and not policy['repeated_fraction_or_full_matrix_math'],
              'actual finite current-call rejection/return/scope policy regression')
    a.require(value['maximum_necessary_postexit_seconds'] == max(v['necessary_postexit_seconds'] for v in observed) and
              value['shutdown_reserve_seconds'] == 30 and value['conservative_empirical_remaining_seconds'] > 0 and
              value['not_hard_realtime_bound'] and value['current_dynamic_checks_in_cap'] and value['R110_arm42_still_invalid'],
              'measured empirical reserve and immutable old cap policy')
    return dict(envelope_SHA=a.sha(a.out/'qualification/envelope.json'),comparisons=compared,
                counterexamples_SHA=a.sha(a.out/'qualification/counterexamples01/audit.json'),
                finite_policy_SHA=a.sha(a.out/'review/finite_policy01/audit.json'),maximum_necessary_postexit_seconds=value['maximum_necessary_postexit_seconds'])


def fees(a,remaining=0,remaining_seconds=0):
    records = []
    for path in sorted((a.out/'fees').glob('*/launch.json')):
        launch,receipt = a.obj(path),a.obj(path.parent/'receipt.json')
        a.require(launch['conservative_process_starts'] == receipt['conservative_process_starts'] and
                  not receipt.get('nested_seconds_added',False) and not receipt.get('earlier_failure_slots_refunded',False),
                  'every paid declared process tree and prior failure retained without nested billing')
        a.require(math.isfinite(receipt['outer_seconds']) and receipt['outer_seconds'] >= 0,'actual finite outer fee')
        qualification = launch.get('qualification',False)
        classification = path.parent/'charge_classification.json'
        if classification.exists():
            correction = a.obj(classification)
            a.require(correction['qualification'] is True,'explicit failed qualification wrapper charge retained')
            qualification = True
        charge = receipt['outer_seconds']
        interval_path = path.parent/'outer_accounting_interval.json'
        interval = None
        if interval_path.exists():
            correction = a.obj(interval_path)
            interval = correction['outer_seconds_interval']
            a.require(correction['original_outer_seconds'] == receipt['outer_seconds'] == interval[0] and
                      math.isfinite(interval[1]) and interval[1] >= interval[0] and correction['budget_charge_seconds'] == interval[1] and
                      correction['original_receipt_unchanged'] and correction['nested_seconds_added'] is False and correction['slots_refunded'] == 0,
                      'original incomplete fee preserved and explicit outward upper used for budget')
            a.require(correction['wrapper_creation_unix'] == launch['wrapper_creation_unix'] and
                      abs(interval[1]-(correction['exit_observed_no_later_than_unix']-launch['wrapper_creation_unix'])) <= 1e-6,
                      'outward total-process upper uses actual creation and observed exit boundary')
            charge = interval[1]
        records.append(dict(label=path.parent.name,**receipt,qualification=qualification,
                            original_launch_qualification_flag=launch.get('qualification',False),
                            budget_charge_seconds=charge,outer_accounting_interval=interval))
    starts = sum(v['conservative_process_starts'] for v in records)
    seconds = sum(v['budget_charge_seconds'] for v in records)
    qs = sum(v['conservative_process_starts'] for v in records if v['qualification'])
    qt = sum(v['budget_charge_seconds'] for v in records if v['qualification'])
    a.require(starts+remaining <= 24 and seconds+remaining_seconds <= 18000 and qs <= 8 and qt <= 600,
              'total24/18000 and qualification8/600 including failures and fixed remaining block')
    return dict(paid_starts=starts,paid_outer_seconds=seconds,qualification_starts=qs,qualification_outer_seconds=qt,
                remaining_reserved_starts=remaining,remaining_reserved_seconds=remaining_seconds,records=records)


def wrapper_closure(a,campaign,qualification,qualified):
    """Close only the two accounting/write-order edits after the actual CLIs.

    This does not pretend that retained-raw branch replay is another CLI.
    Exact AST normalization proves the supervisor and math paths unchanged.
    """
    closure = a.obj(a.out/'qualification/final_wrapper_closure.json')
    actual,final = closure['actual_CLI_helper_bindings'],closure['final_helper_bindings']
    a.require(closure['passed'] and actual == qualification['helpers'] and final == campaign['helpers'] and
              set(actual) == set(final),'original actual CLI and final wrapper helper bindings')
    changed = {p for p in actual if actual[p] != final[p]}
    a.require(changed == {'scripts/round111_campaign.py','scripts/round111_common.py'},
              'only billed accounting/write ordering and outward fee reading changed')
    a.require(closure['original_cli_identity_SHA'] == a.sha(a.out/'qualification/cli01/identity.json') and
              closure['actual_qualification_identity_SHA'] == a.sha(a.out/'qualification/identity.json') and
              closure['original_CLI_fee_receipt_SHA'] == a.sha(a.out/'fees/qualification_cli02/receipt.json'),
              'all actual CLI original identities and incomplete fee receipt remain unchanged')
    def dump(node):return ast.dump(node,include_attributes=False)
    def function(tree,name):return next(v for v in tree.body if isinstance(v,ast.FunctionDef) and v.name == name)
    comparisons = {}
    for path in sorted(changed):
        before_bytes = a.data(a.out/'fees/qualification_cli02/source_snapshot'/path)
        after_bytes = a.data(a.root/path)
        a.require(digest(before_bytes) == actual[path] and digest(after_bytes) == final[path] ==
                  a.sha(a.out/'qualification/final_wrapper_sources'/path),'actual and final exact wrapper source bytes')
        before,after = before_bytes.decode('utf-8'),after_bytes.decode('utf-8')
        bt,at = ast.parse(before),ast.parse(after)
        name = Path(path).name
        change_function = 'billed' if name == 'round111_campaign.py' else 'budget'
        bf,af = function(bt,change_function),function(at,change_function)
        bt.body.remove(bf);at.body.remove(af)
        a.require(dump(bt) == dump(at),'every other module statement, function, import and native supervisor unchanged '+name)
        if change_function == 'billed':
            old_trailer = bf.body.pop()
            new_try = next(v for v in af.body if isinstance(v,ast.Try))
            new_trailer = new_try.body.pop()
            a.require(isinstance(old_trailer,ast.If) and isinstance(old_trailer.test,ast.Name) and
                      old_trailer.test.id == 'qualification' and dump(old_trailer) == dump(new_trailer),
                      'exact qualification trailer moved inside existing exception/fee enclosure')
            removed = []
            for func in (bf,af):
                trial = next(v for v in func.body if isinstance(v,ast.Try))
                loop = next(v for v in trial.body if isinstance(v,ast.For) and isinstance(v.target,ast.Name) and v.target.id == 'number')
                metrics = [v for v in loop.body if isinstance(v,ast.Expr) and isinstance(v.value,ast.Call) and
                           isinstance(v.value.func,ast.Name) and v.value.func.id == 'write' and
                           len(v.value.args) == 2 and dump(v.value.args[1]) == dump(ast.parse('audit.last_metrics',mode='eval').body)]
                a.require(len(metrics) == 1,'one exact required audit metadata write in each old/final loop')
                removed.append(metrics[0]);loop.body.remove(metrics[0])
            a.require(dump(removed[0]) == dump(removed[1]) and dump(bf) == dump(af),
                      'all billed code identical after exactly two allowed statement relocations')
        else:
            charge = next(v for v in af.body if isinstance(v,ast.FunctionDef) and v.name == 'charge')
            allowed_charge = ast.parse("""def charge(p):
    actual=read(p.parent/'receipt.json')['outer_seconds']
    correction=p.parent/'outer_accounting_interval.json'
    if correction.exists():
        value=read(correction)
        assert value['original_outer_seconds']==actual
        lower,upper=value['outer_seconds_interval']
        assert lower==actual and upper>=lower and value['budget_charge_seconds']==upper
        return upper
    return actual
""").body[0]
            a.require(dump(charge) == dump(allowed_charge),'bounded outward interval charge has no runtime/native side effect')
            af.body.remove(charge)
            class OriginalCharge(ast.NodeTransformer):
                def visit_Call(self,node):
                    if isinstance(node.func,ast.Name) and node.func.id == 'charge':
                        assert len(node.args) == 1 and isinstance(node.args[0],ast.Name) and node.args[0].id == 'p' and not node.keywords
                        return ast.parse("read(p.parent/'receipt.json')['outer_seconds']",mode='eval').body
                    return self.generic_visit(node)
            af = OriginalCharge().visit(af)
            a.require(dump(bf) == dump(af),'only existing fee sum readers replaced by validated outward total charge')
        diff = ''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
                                          fromfile='actual_cli/'+name,tofile='final/'+name))
        comparisons[name] = dict(actual_SHA=digest(before_bytes),final_SHA=digest(after_bytes),diff_SHA=digest(diff.encode('utf-8')))
        a.require(comparisons[name]['diff_SHA'] == closure['diff_SHA'][name],'exact independently reconstructed textual wrapper diff')
    a.require(closure['final_sources']['scripts/round111_seed_audit.py'] == actual['scripts/round111_seed_audit.py'] ==
              final['scripts/round111_seed_audit.py'] and closure['actual_native_qualification_not_rerun'] and
              closure['limited_wrapper_boundary_closure_not_byte_identical_CLI'] and
              closure['identical_supervisor_native_argv_math_adapter'],'explicit limited closure and unchanged actual Seed math adapter')
    replays = closure['wrapper_replay']
    a.require([r['mode'] for r in replays] == ['normal','trailer_failure'],'normal and qualifier-tail failure actual branch coverage')
    measured = []
    for item in replays:
        directory = a.local(item['path'])
        audit = a.obj(directory/'audit.json')
        fee = a.obj(directory/'fees/retained_wrapper/receipt.json')
        eng_path = a.local(item['engineering_receipt'])
        engineering = a.obj(eng_path)
        a.require(item['audit_SHA'] == a.sha(directory/'audit.json') and
                  item['receipt_SHA'] == audit['fee_receipt_SHA'] == a.sha(directory/'fees/retained_wrapper/receipt.json') and
                  item['engineering_receipt_SHA'] == a.sha(eng_path),'actual retained-raw replay and engineering receipt bytes')
        a.require(engineering['exit_code'] == 0 and engineering['native_processes'] == engineering['Optimize'] == 0 and
                  item['actual_native_processes'] == item['Optimize'] == audit['actual_native_processes'] == audit['Optimize'] == 0 and
                  audit['passed'] and audit['mode'] == item['mode'] and audit['retained_supervisor_boundary'] and
                  audit['not_a_new_CLI_qualification'] and audit['final_sources'] == final,
                  'actually executed bounded final-wrapper replay without new native or new CLI qualification')
        for path,expected in engineering['sources'].items():
            a.require(a.sha(eng_path.parent/'source_snapshot'/path) == expected,'actual engineering source snapshot '+path)
        a.require(engineering['sources']['scripts/round111_wrapper_replay.py'] ==
                  '82d4e8dd23eab8b09198d534817e7a860ebcb01f8dc31035e916dc764d6a5f03',
                  'independently inspected retained-copy supervisor replacement source')
        finite_equal(a,audit['source_comparisons'],comparisons,'actual replay source closure comparisons')
        events = audit['events']
        a.require(all(math.isfinite(v['end_tick']) and math.isfinite(v['seconds']) and v['seconds'] >= 0 for v in events) and
                  all(x['end_tick'] < y['end_tick'] for x,y in zip(events,events[1:])),
                  'actual replay monotonically ordered necessary write completions')
        metrics = [e for e in events if e['path'].endswith('/audit_execution_metrics.json')]
        a.require(len(metrics) == 2,'both arm metadata writes actually measured')
        for event in metrics:
            whole = next(e for e in events if e['path'] == event['path'].replace('audit_execution_metrics.json','whole_arm_receipt.json'))
            a.require(event['end_tick'] < whole['end_tick'],'required metadata completes before whole-arm clock receipt')
        maximum = max(v['seconds'] for v in metrics)
        a.require(maximum == audit['maximum_required_metadata_write_seconds'] == item['maximum_required_metadata_write_seconds'],
                  'actual maximum incremental necessary metadata cost')
        measured.append(maximum)
        a.require(fee['exit_code'] == (0 if item['mode'] == 'normal' else 1) and fee['actual_native_children_with_launch'] == 0,
                  'normal return and actual qualifier-tail exception charge codes')
        if item['mode'] == 'normal':
            ident_event = next(e for e in events if e['path'] == 'qualification/identity.json')
            fee_event = next(e for e in events if e['path'] == 'fees/retained_wrapper/receipt.json')
            a.require(ident_event['end_tick'] < fee_event['end_tick'] and (directory/'qualification/identity.json').exists(),
                      'actual success qualification identity completes before final fee charge')
        else:
            a.require((directory/'fees/retained_wrapper/failure.txt').exists() and not (directory/'qualification/identity.json').exists() and
                      isinstance(audit['actual_expected_exception'],str),'actual trailer rejection retained with no false qualified identity')
        for call,launch in zip(audit['retained_calls'],qualification['launches']):
            a.require(call['number'] == launch['number'] and call['actual_native_children'] == 0 and
                      call['audit_SHA'] == a.sha(a.local(launch['destination'])/'audit.json'),'same actual two CLI raw retained-copy boundary')
    maximum = max(measured)
    a.require(maximum == closure['added_required_metadata_cost_seconds'],'bounded measured metadata allowance')
    envelope_value = a.obj(a.out/'qualification/envelope.json')
    costs = [v['necessary_postexit_seconds']+maximum for v in envelope_value['observations']]
    finite_equal(a,costs,closure['all_empirical_postexit_with_added_metadata_seconds'],'all eight fresh empirical costs plus required metadata')
    a.require(len(costs) == 8 and all(0 <= v <= 15 for v in costs),'all eight final limited-wrapper empirical postexit costs within15')
    finite_equal(a,closure['corrected_qualification_outer_interval'],a.obj(a.out/'fees/qualification_cli02/outer_accounting_interval.json'),
                 'actual observed exit total outer upper supplement')
    return dict(closure_SHA=a.sha(a.out/'qualification/final_wrapper_closure.json'),source_comparisons=comparisons,
                independent_AST_accounting_and_write_order_equivalence=True,actual_CLI_not_repeated=True,
                actual_independent_qualification_raw_SHA=QUALIFICATION_RAW_SHA,metadata_maximum_seconds=maximum,
                final_empirical_postexit_seconds=costs,not_hard_realtime_bound=True)


def run(a,mode,pe_path,dll_path,fixture_root):
    main,roles,inherited = inherited_main(a)
    production,candidate,campaign,qualification = identities(a,mode,pe_path,dll_path)
    launches = panel(a,campaign,mode == 'admission')
    protocol = a.obj(a.out/'protocol.json')
    a.require(protocol['evidence_layer'] == decision.LAYER and protocol['formal_arms'] == 6 and protocol['maximum_starts'] == 24 and
              protocol['maximum_outer_seconds'] == 18000 and protocol['qualification_maximum_starts'] == 8 and
              protocol['qualification_maximum_outer_seconds'] == 600 and protocol['engineering_postexit_maximum_seconds'] == 15 and
              protocol['shutdown_margin_seconds'] == 30 and protocol['common_parameters']['gurobi_seed'] == 1,
              'frozen current Seed1 budget and empirical/clock rules')
    value = dict(mode=mode,evidence_layer=decision.LAYER,production_PE_SHA=PE,DLL_SHA=DLL,
                 candidate_identity_SHA=a.sha(a.out/'candidate_identity.json'),campaign_identity_SHA=a.sha(a.out/'campaign/identity.json'),
                 qualification_identity_SHA=a.sha(a.out/'qualification/identity.json'),protocol_SHA=a.sha(a.out/'protocol.json'),
                 helper_bindings=campaign['helpers'],inherited_main_import_SHA=MAIN_IMPORT_SHA,inherited_main36_qualified=True,
                 inherited_main_raw_reaudited=False,Optimize=0,native_environment=0)
    if mode == 'admission':
        value['empirical_equivalence'] = envelope(a,fixture_root)
        previous = actual_qualification(a)
        value['final_wrapper_closure'] = wrapper_closure(a,campaign,qualification,previous)
        qualified = previous['own_actual_qualification_arms']
        for record,entry in zip(qualified,qualification['launches']):
            a.require(record['formal_protocol_qualified'] and entry['cap_seconds'] <= 120 and record['seed'] == 1,
                      'actual fixed H100 functional full clock')
        a.require(len(qualified) == 2 and [(v['id'],v['arm']) for v in qualified] == [('H100','P-GRB'),('H100','M-B')] and
                  any(v['solve_kind'] == 'LP' for v in qualified[1]['native_records']) and
                  any(v['solve_kind'] == 'MIP' for v in qualified[1]['native_records']) and qualified[1]['starts'],
                  'two actual Seed1 CLI model/type/LP/MIP/Start paths independently reconstructed')
        value['own_actual_qualification_arms'] = qualified
        value['qualification_raw_audit_SHA'] = QUALIFICATION_RAW_SHA
        value['qualification_math_repeated'] = False
        value['budget'] = fees(a,9,12600+360)
        value['decision'] = 'ACCEPT'
        value['all6_complete_argv'] = [v['command'] for v in launches]
        value['formal_arms_already_started'] = 0
        value['signed_unix'] = time.time()
        value['signed_UTC'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        value['not_hard_realtime_guarantee'] = True
    else:
        admission = a.obj(a.out/'review/performance_admission.json')
        a.require(admission['decision'] == 'ACCEPT' and admission['candidate_identity_SHA'] == value['candidate_identity_SHA'] and
                  admission['campaign_identity_SHA'] == value['campaign_identity_SHA'] and admission['helper_bindings'] == campaign['helpers'],
                  'performance sources frozen at actually signed admission')
        records = []
        for launch in launches:
            directory = a.local(launch['destination'])
            actual = a.obj(directory/'launch.json')
            # Native journals and all modeled checks are recomputed below. An
            # actual timestamp boundary is additionally checked when recorded.
            if 'started_unix' in actual:
                a.require(actual['started_unix'] >= admission['signed_unix'],'native launch after actual independent signature')
            record,models,q = a.arm(launch,campaign)
            records.append(record)
        value['own_actual_current_seed_arms'] = records
        value['selection'] = decision.selection(a.decision['pair'],main,records,roles,True)
        value['stage'] = value['selection']['stage']
        value['budget'] = fees(a)
        value['decision'] = 'ACCEPT_INDEPENDENT_LAYERED_CURRENT_RAW_DECISION'
    value['completed_checks'] = a.checks
    value['read_bindings'] = a.reads
    value['explicit_read_root'] = str(a.root)
    value['no_original_root_fallback'] = mode == 'public'
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--mode',choices=['admission','final','public'],required=True)
    parser.add_argument('--label',required=True)
    parser.add_argument('--pe',type=Path)
    parser.add_argument('--dll',type=Path)
    parser.add_argument('--fixture-root',type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    destination = root/ROUND/'review'/args.label
    destination.mkdir(parents=True,exist_ok=False)
    stdout = (destination/'stdout.log').open('x',encoding='utf-8',newline='\n')
    stderr = (destination/'stderr.log').open('x',encoding='utf-8',newline='\n')
    sys.stdout,sys.stderr = Tee(sys.stdout,stdout),Tee(sys.stderr,stderr)
    start = time.perf_counter()
    source_bindings = {}
    for path in (Path(__file__),Path(__file__).with_name('round111_independent_core.py'),
                 Path(__file__).with_name('round111_independent_decision.py'),Path(__file__).with_name('round111_import_main.py')):
        source_bindings[path.name] = digest(path.read_bytes())
        (destination/path.name).open('xb').write(path.read_bytes())
    launch = dict(cwd=str(Path.cwd().resolve()),argv=sys.argv,PID=os.getpid(),root=str(root),mode=args.mode,
                  actual_fixture_root=str((args.fixture_root or root).resolve()),source_bindings=source_bindings,
                  start_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),Optimize=0,native_environment=0)
    write(destination/'launch.json',launch)
    code = 1
    try:
        a = Audit(root,destination)
        audit = run(a,args.mode,args.pe,args.dll,args.fixture_root or root)
        audit['reviewer_source_bindings'] = source_bindings
        write(destination/'audit.json',audit)
        if args.mode == 'admission':
            # Exclusive creation prevents overwriting an earlier performance
            # authorization. Actual failed admissions never create this file.
            write(root/ROUND/'review/performance_admission.json',audit)
        print(json.dumps(dict(decision=audit['decision'],stage=audit.get('stage'),checks=audit['completed_checks'])),flush=True)
        code = 0
    except Exception:
        error = traceback.format_exc()
        traceback.print_exc()
        write(destination/'hold.json',dict(decision='HOLD',error=error,Optimize=0,native_environment=0))
    sys.stdout.flush();sys.stderr.flush()
    receipt = dict(exit_code=code,cwd=launch['cwd'],explicit_read_root=str(root),mode=args.mode,
                   engineering_elapsed_seconds=time.perf_counter()-start,source_bindings=source_bindings,
                   stdout_SHA=digest((destination/'stdout.log').read_bytes()),stderr_SHA=digest((destination/'stderr.log').read_bytes()),
                   Optimize=0,native_environment=0)
    if (destination/'audit.json').exists():
        receipt['audit_SHA'] = digest((destination/'audit.json').read_bytes())
    write(destination/'receipt.json',receipt)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
