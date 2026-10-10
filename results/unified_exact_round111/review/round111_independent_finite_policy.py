"""Finite policy regressions against actual signed current R110 proofs.

This checks retained identities, dispositions, true-G scopes and return facts.
The already executed exact Fraction matrix proofs are inherited, not replayed.
No old tuple licenses a new call; changing identity invalidates its signature.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import os
import sys
import time
import traceback
from round111_import_main import Tee, write, digest

ROUND = 'results/unified_exact_round111'
AUTH = ROUND+'/review/inherited_main03/authority'
PE = 'c0384284aefd5aa2acc5d885ef37b0cfad6f93d083a5feb9ee693c41a786b411'


def require(condition,label):
    if not condition:
        raise AssertionError(label)


def validate(proposal,signed,calls,returned,original):
    number,rid,seed,arm = original['key']
    require(proposal['key'] == signed['current_key'] == original['key'],'same current arm/model evidence identity')
    require(proposal['production_PE_SHA'] == signed['production_PE_SHA'] == PE and
            proposal['DLL_SHA'] == signed['DLL_SHA'] and proposal['campaign_identity_SHA'] == signed['campaign_identity_SHA'],
            'same actual current production/campaign identity')
    require(proposal['model_SHA'] == signed['current_model_SHA'] == signed['model_SHA'] == original['model_SHA'],
            'actual current model content identity')
    require(proposal['exact_vector_SHA'] == signed['exact_vector_SHA'] == original['exact_vector_SHA'] and
            proposal['raw_bindings'] == signed['raw_bindings'] == original['raw_bindings'],'unchanged actual complete-matrix proof bindings')
    require(proposal['reject_all_call_native_lower_claims'] is True and signed['reject_all_call_native_lower_claims'] is True and
            proposal['withdraw_necessary_dependent_closures'] is True,'all damaged call claims and necessary dependent closures withdrawn')
    require(proposal['qualified_L'] == signed['own_complete_original_domain_floor'] == 0. and
            proposal['own_U'] == signed['own_U'] == signed['result']['U'] == original['own_U'],
            'own physical endpoint plus independent original-domain nonnegative floor')
    require(proposal['certificate_from_own_exact_zero'] == signed['certificate_from_own_exact_zero'] == signed['result']['certificate'] == (proposal['own_U'] == 0.),
            'positive own U remains open; own exact zero certifies without native claims')
    require(signed['original_native_flags_preserved'] and signed['independently_proved_normal_return'] and
            signed['missing_returned_journal_preserved'] == (number in (17,25)) and
            ((4 not in returned) if number == 25 else (1 not in returned)) == signed['missing_returned_journal_preserved'],
            'normal API return is distinct from journal returned-event availability')
    require(signed['complete_seconds'] is None and signed['complete_seconds_interval'] == proposal['time']['interval'] and
            proposal['time']['exact_seconds'] is None,'missing exact whole clock retained as original outward interval')
    records = signed['result']['native_records']
    if number == 25:
        require(proposal['damaged_calls'] == signed['damaged_calls'] == [4] and
                proposal['preserved_distinct_LP_calls'] == signed['preserved_distinct_LP_calls'] == [1,2,3],
                'damaged terminal MIP and independent LP calls stay distinct')
        require([v['solve_kind'] for v in records] == ['LP','LP','LP','MIP'] and
                [v['native_bounds_mathematically_qualified'] for v in records] == [True,True,True,False],
                'positive-G LP proof is not rejected with damaged root-domain MIP')
        require(calls[4]['lower_g'] == 0 and calls[4]['upper_g'] == calls[4]['cutoff'] > 0 and
                calls[3]['lower_g'] > 0 and records[2]['returned_native_log_L'] > 0,
                'actual rejected zero vector has root-domain authority; positive-G right LP retains its own bound')
        require(signed['withdraw_necessary_dependent_closures'] and signed['result']['cover']['native_terminal_call_closure_withdrawn'],
                'damaged scoped native closure withdrawn independently of valid full-domain own-zero proof')
    else:
        require(len(records) == len(calls) == 1 and calls[1]['full_original'] == 1 and
                records[0]['native_bounds_mathematically_qualified'] is False,'cold complete-domain rejected call only')
    return True


def run(root,source,destination):
    root,source = Path(root).resolve(),Path(source).resolve()
    main = json.loads((root/ROUND/'review/inherited_main03/audit.json').read_bytes())
    original_import = json.loads((root/ROUND/'review/inherited_main03/main36_imported_rows.json').read_bytes())
    bindings,actual,checks = {},[],[]
    for number in (15,17,25,26):
        prefix = root/AUTH
        proposal_path,signed_path = prefix/f'recovery_{number:02d}.json',prefix/f'recovery_{number:02d}_signed_audit.json'
        for path in (proposal_path,signed_path):
            relative = path.relative_to(root).as_posix()
            require(digest(path.read_bytes()) == main['retained_bindings'][relative],'retained signed import artifact bytes')
            bindings[relative] = digest(path.read_bytes())
        proposal,signed = json.loads(proposal_path.read_bytes()),json.loads(signed_path.read_bytes())
        original = copy.deepcopy(proposal)
        obs_path = f'results/unified_exact_round110/campaign/raw/{number:02d}_{proposal["key"][1]}_S0_{proposal["key"][3]}/observations.json'
        raw = (source/obs_path).read_bytes()
        require(digest(raw) == proposal['raw_bindings'][obs_path],'actual original observations bound by current exact proof')
        observed = json.loads(raw)
        calls = {v['payload']['call']:v['payload'] for v in observed if v['payload']['kind'] == 'call'}
        returned = [v['payload']['call'] for v in observed if v['payload']['kind'] == 'returned']
        validate(proposal,signed,calls,returned,original)
        row = original_import[number-1]
        actual.append(dict(number=number,key=proposal['key'],observation_source_path=obs_path,observation_source_SHA=digest(raw),
                           calls=calls,returned_call_ids=returned,raw_audit_passed=row['raw_audit_passed'],
                           original_journal_return_missing=row['journal_return_missing'],independent_normal_return_proved=True,
                           own_U=proposal['own_U'],qualified_L=proposal['qualified_L'],certificate=proposal['certificate_from_own_exact_zero'],
                           signed_audit_SHA=digest(signed_path.read_bytes()),whole_clock_interval=proposal['time']['interval']))
        checks.append(dict(number=number,test='actual signed recovery and native scope/return dispositions',accepted=True))
        mutants = []
        p = copy.deepcopy(proposal);p['key'][0] += 100;mutants.append(('wrong current arm identity',p,signed,calls,returned))
        p = copy.deepcopy(proposal);p['model_SHA'] = '0'*64;mutants.append(('same tuple with different model bytes',p,signed,calls,returned))
        p = copy.deepcopy(proposal);p['reject_all_call_native_lower_claims'] = False;mutants.append(('retain one damaged native lower claim',p,signed,calls,returned))
        p = copy.deepcopy(proposal);p['withdraw_necessary_dependent_closures'] = False;mutants.append(('retain a necessary damaged derived closure',p,signed,calls,returned))
        s = copy.deepcopy(signed);s['missing_returned_journal_preserved'] = not s['missing_returned_journal_preserved'];mutants.append(('infer missing-event flag from rc0 alone',proposal,s,calls,returned))
        p = copy.deepcopy(proposal);p['time']['exact_seconds'] = p['time']['interval'][0];mutants.append(('fabricate exact clock from lower interval endpoint',p,signed,calls,returned))
        p = copy.deepcopy(proposal);p['certificate_from_own_exact_zero'] = not p['certificate_from_own_exact_zero'];mutants.append(('change own floor certification with same physical U',p,signed,calls,returned))
        if number == 25:
            p = copy.deepcopy(proposal);p['preserved_distinct_LP_calls'] = [1,2];mutants.append(('discard positive-G right LP with damaged MIP',p,signed,calls,returned))
            c = copy.deepcopy(calls);c[4]['lower_g'] = c[3]['lower_g'];mutants.append(('use root zero witness against positive-G damaged domain',proposal,signed,c,returned))
        for label,p,s,c,r in mutants:
            try:
                validate(p,s,c,r,original)
            except AssertionError:
                checks.append(dict(number=number,test=label,correctly_rejected=True))
            else:
                raise AssertionError('invalid mutated current evidence accepted: '+label)
    write(destination/'actual_current_policy_facts.json',actual)
    return dict(decision='ACCEPT_FINITE_CURRENT_NUMERICAL_RETURN_SCOPE_POLICY',actual_roles=[15,17,25,26],checks=checks,
                retained_input_bindings=bindings,actual_scope_return_fact_SHA=digest((destination/'actual_current_policy_facts.json').read_bytes()),
                source_old_root=str(source),repeated_fraction_or_full_matrix_math=False,old_raw_modified=False,
                future_calls_need_their_own_current_proof=True,no_tuple_recovery_authority=True,Optimize=0,native_environment=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--label',default='finite_policy01')
    args = parser.parse_args()
    destination = args.root.resolve()/ROUND/'review'/args.label
    destination.mkdir(parents=True,exist_ok=False)
    stdout = (destination/'stdout.log').open('x',encoding='utf-8',newline='\n')
    stderr = (destination/'stderr.log').open('x',encoding='utf-8',newline='\n')
    sys.stdout,sys.stderr = Tee(sys.stdout,stdout),Tee(sys.stderr,stderr)
    start = time.perf_counter()
    launch = dict(cwd=str(Path.cwd().resolve()),argv=sys.argv,PID=os.getpid(),root=str(args.root.resolve()),source_root=str(args.source_root.resolve()),
                  source_SHA=digest(Path(__file__).read_bytes()))
    write(destination/'launch.json',launch)
    (destination/'execution_source.py').open('xb').write(Path(__file__).read_bytes())
    code = 1
    try:
        audit = run(args.root,args.source_root,destination)
        audit['source_SHA'] = launch['source_SHA']
        write(destination/'audit.json',audit)
        print(json.dumps(dict(decision=audit['decision'],checks=len(audit['checks']))),flush=True)
        code = 0
    except Exception:
        traceback.print_exc()
    sys.stdout.flush();sys.stderr.flush()
    receipt = dict(exit_code=code,cwd=launch['cwd'],source_SHA=launch['source_SHA'],engineering_elapsed_seconds=time.perf_counter()-start,
                   stdout_SHA=digest((destination/'stdout.log').read_bytes()),stderr_SHA=digest((destination/'stderr.log').read_bytes()),Optimize=0,native_environment=0)
    if (destination/'audit.json').exists():
        receipt['audit_SHA'] = digest((destination/'audit.json').read_bytes())
    write(destination/'receipt.json',receipt)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
