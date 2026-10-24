"""One finite read-only entry for R132 internal review and public recovery.

--preflight reads only small plans, bindings, source text and input files. The
default checks all60D+24C closeout paths and closed G1 fee metadata before it
imports any inherited evidence reader or reads raw models/fleets/H/native logs.
No producer, analysis adapter, solver module, PE or DLL is executed or loaded.
The only writes are the caller-selected review receipt and retained prior
receipts. A final PASS is finite evidence review, never external replication or
a proof that every serialized numerical formulation has the same relaxation.
"""

from pathlib import Path, PurePosixPath
from fractions import Fraction as F
import argparse
import ast
import collections
import contextlib
import copy
import csv
import datetime
import hashlib
import importlib
import itertools
import gzip
import json
import math
import os
import statistics
import sys
import time
import traceback
import types

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
OUT_REL = 'results/unified_exact_round132'
PE = '2df9e0e160ecbcbd35c4e83eb434344893f9a59beb59667f3681772b4ff66d6c'
RESEARCH_PE = 'eac4e778cacb316c61928d4a6f1e4c90c8397cc94e0dc528695773703e98cce2'
DLL = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
BASE = 'b97418ecc0b9f739232af484f999770c130ceb76'
SOURCE = '7564a5415331b380e24d1ec06936dcfd56557e67'
LIMITS = dict(C=32400, D=84000, qualification=3600, E=10800, C3=4800, repair=8400)
# These accepted bindings seal the plans, full argv and producer adapters. This
# checker is deliberately not inserted into or used to alter either binding.
PINNED = {
    'D_execution_binding.json': '569fce35242e2e54a52aa63a145d5ffa3db7c5eabfacd5d9d2786198eeb4098c',
    'C_execution_binding.json': '3248070303dd4157ea0df766b859108b354dffffa7ee9909abe98352f9480135',
    'source_recipe.json': 'f1419a3f87a5e6d4438109b1d583d55f50f7bef82b8ccdd3fbb57b74f464cf03',
    'E_experiment_plan.json': 'd8de4cba395f475c83b8f22e8fc0abd31c887ffe0fdb6c289ce0af626adad7dd',
}
E_RUNNER = '8d0d723a32a8f11dcd240778e44d6f172c44f02fe5c65e05c706d13b9ceafdf6'
C_ROLES = (('SC-C15-B', 600), ('SC-B20-S', 1200), ('UC-C20-U', 1200), ('PB-C35-U', 2400))
C_PAIRS = (('S2R-GEOM', 'S2R'), ('S2R-SP', 'S2R'))
EXPRESSIONS = dict(off='S2R', geom='S2R-GEOM', sp='S2R-SP')
CASES = (
    dict(id='J1', b=[2,0,1,1], Q=[1,2], T=240),
    dict(id='J2', b=[2,1,0,0], Q=[1,2], T=240),
    dict(id='J3', b=[2,1,0,0], Q=[1,2], T=360),
    dict(id='J4', b=[1,1,1,1], Q=[1,1], T=240),
)
HASHES = {}
REPORTING_PREDECESSOR = dict(
    checker_SHA='a6939dae51f8f29870d6ad48934fd344afd55907af87be769e5537317afa3033',
    Git_commit='0456358c8dff158ee874036cf9d2fd10d4fba633',
    Git_blob='e9e08c4dbb1ad1e7e728881dac2f47307c77574d')
SOURCE_LOSS_PREDECESSOR = dict(
    checker_SHA='0e7d939c4e3a99561172170489733a83f524dc9d25f876da03c1977ffdbfc452',
    retained_bytes='results/unified_exact_round132/review/portable_checker_before_source_loss.py')
SOURCE_LOSS_DISPOSITION = 'UNEVALUABLE formal performance; independent own-zero proof retained; not ordinary open'
WITNESS_FIELDS = ('id','seed','method','producer_receipt_SHA','G_true','P_true','U','L')
LIFETIME_FIELDS = ('stage_waiter_lifetime_overlap_lower_seconds',
    'stage_waiter_lifetime_overlap_upper_seconds','stage_waiter_lifetime_overlap',
    'timing_environment_scope','counterfactual_clean_machine_T_cert')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    path = Path(path).resolve()
    if path not in HASHES:
        h = hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda: f.read(1048576), b''):
                h.update(block)
        HASHES[path] = h.hexdigest()
    return HASHES[path]


def portable(value):
    """Map a recorded evidence path exclusively into the caller's ROOT."""
    s = str(value).replace('\\', '/')
    if '..' in PurePosixPath(s).parts:
        raise AssertionError(('parent traversal in evidence path', value))
    markers = ('results/', 'reference/', 'scripts/', 'src/', 'include/', 'tests/')
    suffix = None
    for marker in markers:
        if s.startswith(marker):
            suffix = s
            break
        where = s.find('/' + marker)
        if where >= 0:
            suffix = s[where + 1:]
            break
    if suffix is None:
        # Frozen source identity contains this one root-level build file.
        if s == 'CMakeLists.txt':
            suffix = s
        else:
            raise AssertionError(('no published-root evidence mapping', value))
    rel = PurePosixPath(suffix)
    assert not rel.is_absolute() and '..' not in rel.parts
    mapped = ROOT.joinpath(*rel.parts).resolve()
    assert mapped.is_relative_to(ROOT), ('evidence path escaped supplied root', value)
    return mapped


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def same(a, b, tolerance=1e-8):
    assert a is not None and b is not None and math.isfinite(a) and math.isfinite(b), (a,b)
    assert abs(a-b) <= tolerance, (a,b,tolerance)


def equal(expected, actual, label):
    if expected is None:
        assert actual is None, ('invented null', label, actual)
    elif isinstance(expected, bool):
        assert actual is expected, ('boolean drift', label)
    elif isinstance(expected, (int,float)):
        same(actual, expected)
    elif isinstance(expected, dict):
        assert isinstance(actual, dict) and set(expected) <= set(actual), ('missing fields', label)
        for k,v in expected.items():
            equal(v, actual[k], (label,k))
    elif isinstance(expected, (list,tuple)):
        assert isinstance(actual, (list,tuple)) and len(actual)==len(expected), ('length drift', label)
        for k,(a,b) in enumerate(zip(expected,actual)):
            equal(a,b,(label,k))
    else:
        assert actual == expected, ('value drift', label, expected, actual)


def eligible(a):
    return all(a.get(k) is True for k in ('formal_protocol_qualified','numbers_qualified','certificate_qualified')) and not a.get('source_reduced',False)


def writable_open_flags(flags):
    # Windows O_NOINHERIT is 128; POSIX O_EXCL is often 128. Numeric masks
    # cannot cross that platform boundary. Access/create/truncate/append/excl
    # are denied using the interpreter's actual platform constants.
    mask=os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND|os.O_EXCL
    return bool(flags and flags & mask)


def readonly_flags_preflight():
    read_flags=os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOINHERIT',0)|getattr(os,'O_CLOEXEC',0)
    assert not writable_open_flags(read_flags)
    for flag in (os.O_WRONLY,os.O_RDWR,os.O_CREAT,os.O_TRUNC,os.O_APPEND,os.O_EXCL):
        assert writable_open_flags(read_flags|flag)
    return dict(status='PASS',platform_native_os_constants=True,read_flags_checked=read_flags,
        read_only_binary_noinherit_cloexec_not_misclassified=True,all_write_create_truncate_append_excl_flags_denied=True)


@contextlib.contextmanager
def disabled_ffi_import():
    """Legacy process helpers may import ctypes but must never use its FFI.

    On Windows importing real ctypes itself loads kernel32. A deliberately
    inert module lets unused function definitions load without any DLL. Every
    attempted FFI attribute access fails. The original sys.modules entry is
    restored after imports; inherited modules keep only this disabled object.
    """
    class DisabledFFI(types.ModuleType):
        def __getattr__(self,name):
            raise AssertionError(('FFI attribute unavailable in pure evidence review',name))
    absent=object();before=sys.modules.get('ctypes',absent)
    sys.modules['ctypes']=DisabledFFI('ctypes')
    try:yield
    finally:
        if before is absent:sys.modules.pop('ctypes',None)
        else:sys.modules['ctypes']=before


def disabled_ffi_preflight():
    before=sys.modules.get('ctypes')
    with disabled_ffi_import():
        import ctypes as disabled
        for name in ('WinDLL','CDLL','windll','Structure','pythonapi'):
            try:getattr(disabled,name)
            except AssertionError:pass
            else:raise AssertionError(('FFI was accessible',name))
    assert sys.modules.get('ctypes') is before
    return dict(status='PASS',historical_unused_FFI_import_is_inert=True,
        FFI_attributes_inaccessible=True,real_ctypes_or_native_library_not_imported=True)


def source_loss_endpoint_contract(arm,original,physical,panel,data,own,local,finding,launch):
    """A reporting disposition, never an exception to frozen eligibility.

    The caller independently replays the full fleet, journal, call domains,
    model/source/return predicates and seals before accepting this result.
    A cohort/P counterexample alone is insufficient: the local arm must have
    rejected the same damaged calls using its own verified exact-zero fleet.
    """
    assert not eligible(arm) and arm.get('source_reduced') is True
    assert arm.get('native_proof_qualified') is False
    assert all(arm.get(k) is True for k in ('formal_protocol_qualified','numbers_qualified','certificate_qualified'))
    assert arm.get('certificate') is True and arm.get('own_exact_zero') is True
    assert arm.get('proof_evidence')==arm.get('certificate_source')=='OWN_ZERO_CERTIFICATE'
    assert arm['U']==arm['L']==arm['gap']==physical['G']==physical['P']==physical['F']==0
    assert original['T_cert']==arm['T_produce'] and original['certificate'] is True
    assert own['own_U']==0 and own['own_exact_zero'] is True
    assert own['own_physical_verified'] is True and own['independent_floor0'] is True
    assert physical['Y'][1:]==data['D'][1:] and all(d>0 for d in data['D'][1:])
    assert panel['lambda']>=0 and all(math.isfinite(w) and w>=0 for w in data['w'][1:])
    # Equal integer inventories and positive targets give exact ratio one,
    # independently of the floating reported G/P or a native bound.
    assert all(F(y)/F(d)==1 for y,d in zip(physical['Y'][1:],data['D'][1:]))
    zeros=[w for w in own['witnesses'] if w.get('arm')==launch['arm'] and
        w.get('physical_verified') is True and w['G']==w['P']==w['F']==0 and
        w['input_SHA']==launch['panel']['input_sha256']]
    assert zeros, 'no own saved physical zero witness'
    damaged={(q['arm'],q['call']) for q in local['damaged_calls']}
    final_damaged={(q['arm'],q['call']) for q in finding['damaged_calls'] if q['arm']==launch['arm']}
    assert damaged and damaged==final_damaged, 'source loss must be independently supported within this arm'
    assert all(a==launch['arm'] for a,c in damaged)
    assert local['rejections'] and {(q['arm'],q['call']) for q in local['rejections']}==damaged
    for q in local['rejections']:
        assert q['call_rejected_as_a_whole'] is True and q['domain_verified'] is True
        assert q['model_SHA'] and q['model_SHA']==q['scope']['model_sha256']
        assert q['arm']==launch['arm'] and q['reason'] in ('full_bound_witness_inconsistency','local_bound_witness_inconsistency')
        counter=q['counterexample']
        assert counter['arm']==launch['arm'] and counter['F']==counter['G']==0
        assert counter['physical_verified'] is True and counter['input_SHA']==launch['panel']['input_sha256']
        matches=[w for w in zeros if w['source']==counter['source'] and w['available']==counter['available']]
        assert matches, 'rejection depends on a different or unverified counterexample'
        scope=q['scope']
        assert scope['full_original'] or any(scope['lower_g']-1e-7<=w['G']<=scope['upper_g']+1e-7 and
            w['F']<=scope['cutoff']+1e-7 for w in matches)
        assert math.isfinite(q['value']) and q['value']>counter['F']+1e-7
    return dict(damaged_calls=local['damaged_calls'],
        rejected_bound_values=[q['value'] for q in local['rejections']],
        own_zero_witness_sequences=sorted({w['sequence'] for w in zeros if w.get('sequence') is not None}))


def source_loss_record(core,item,finding,arm,original,physical,launch,line,method):
    """Read only the existing own rejection and own zero, no native repair."""
    dest=portable(launch['destination']);local=read(dest/'claim_rejections.json')
    data=core.evidence.instance(ROOT,launch['panel'])
    support=source_loss_endpoint_contract(arm,original,physical,launch['panel'],data,item['ind'],local,finding,launch)
    assert read(dest/'verification_closeout.json')['native_proof_qualified'] is False
    return dict(line=line,id=launch['id'],seed=launch['seed'],method=method,
        own_physical_zero_certificate_retained=True,native_proof_qualified=False,
        source_reduced=True,formal_performance_evidence_eligible=False,
        raw_reconstructed_T_cert=original['T_cert'],formal_performance_T_cert=None,
        T_produce=arm['T_produce'],T_verify=arm['T_verify'],T_total=arm['T_total'],
        disposition=SOURCE_LOSS_DISPOSITION,**support,
        native_source_reliability_unresolved=True,no_native_retry=True,
        sources=[dict(path=rel(p),SHA=sha(p)) for p in
            (dest/'independent_evidence.json',dest/'claim_rejections.json',dest/'producer_receipt.json')])


def reporting_disposition_summary(arms,pairs,losses):
    """All positions stay; only fully substantiated own-zero losses can close."""
    key=lambda a:(a['line'],a['id'],a['seed'],a['method'])
    by={key(a):a for a in arms};allowed={key(a) for a in losses}
    assert len(by)==len(arms) and len(allowed)==len(losses)
    unqualified={key(a) for a in arms if not eligible(a)}
    assert allowed<=unqualified, 'source loss cannot grant performance eligibility'
    unresolved=sorted(unqualified-allowed)
    unresolved_pairs=[]
    for q in pairs:
        if q['classification']!='UNEVALUABLE':continue
        keys=[(q['line'],q['id'],q['seed'],m) for m in (q['left'],q['right'])]
        if q.get('obstacle') or not any(k in allowed for k in keys) or any(not eligible(by[k]) and k not in allowed for k in keys):
            unresolved_pairs.append(dict(line=q['line'],group=q['group'],left=q['left'],right=q['right']))
        else:
            assert q['direction']=='UNEVALUABLE' and q['right_over_left_certification_ratio'] is None
            assert q['left_minus_right_seconds'] is None
            for k,side in zip(keys,('left','right')):
                if k in allowed:assert by[k]['T_cert'] is None and by[k]['censored'] is None and q[side+'_T_cert'] is None
    return dict(required_positions=len(arms),typed_positions=len(pairs),
        performance_qualified_observations=len(arms)-len(unqualified),
        disclosed_source_loss_observations=len(losses),
        native_source_qualified_observations=sum(a.get('native_proof_qualified') is True and not a.get('source_reduced') for a in arms),
        performance_unevaluable_comparisons=sum(q['classification']=='UNEVALUABLE' for q in pairs),
        unresolved_unqualified_observations=unresolved,unresolved_unevaluable_comparisons=unresolved_pairs,
        all_required_positions_performance_qualified=not unqualified,
        rejected_native_proof_reliability_restored=False,
        raw_own_zero_not_treated_as_open_or_time_win=True)


def options(command):
    out = {}; j = 1
    while j < len(command):
        flag = command[j]
        assert flag.startswith('--') and flag not in out, ('duplicate/positional option',flag)
        j += 1
        if j < len(command) and not command[j].startswith('--'):
            out[flag] = command[j]; j += 1
        else:
            out[flag] = True
    return out


def command_contract(line, group, launch):
    p, method = launch['panel'], launch['method']; o = options(launch['command'])
    assert launch['id']==p['id']==group['role']['id'] and launch['seed']==p['gurobi_seed']==group['seed'] in (0,1)
    assert launch['repeat']==1 and launch['cap_seconds']==p['cap_seconds']==group['role']['cap_seconds']
    assert launch['hard_stop_seconds']==p['cap_seconds']-2 and launch['configuration']==dict(id='q0',MIPFocus=0,Cuts=-1)
    for flag,value in {'--lambda':'.15','--T':p['T_seconds'],'--pickup-time':60,'--drop-time':60,
        '--time-limit':p['cap_seconds']-6,'--process-wall-time-limit':p['cap_seconds'],
        '--process-shutdown-margin':30,'--threads':1,'--mip-threads':1,
        '--gurobi-seed':group['seed'],'--gurobi-presolve':-1}.items():
        if flag=='--lambda': same(float(o[flag]),.15,0.)
        else: assert o[flag]==str(value),(line,flag,o.get(flag),value)
    assert portable(o['--input'])==portable(p['input_path'])
    assert sha(portable(p['input_path']))==p['input_sha256']
    dest=portable(launch['destination'])
    assert dest.parent==portable(OUT_REL+'/'+group['name'])/'raw'
    for flag,name in {'--out':'result.json','--log':'native.log','--process-phase-ledger':'phases.csv',
        '--external-gini-artifact-dir':'external','--primal-heuristic-generation-log':'hga.csv',
        '--progress-log':'progress.csv','--native-evidence-dir':'journal'}.items():
        assert portable(o[flag])==dest/name,(flag,line)
    assert '--round128-mode' not in o and '--gurobi-hga-start' not in o
    if line=='D':
        assert launch['binary_layer']=='E3' and '--round132-expression' not in o
        if method in ('P','PS'):
            assert o['--method']=='gurobi' and o['--plain-baseline'] is True
            assert o['--round24-executable-sha256']==o['--round24-manifest-executable-sha256']==PE
            assert portable(o['--gurobi-model-export'])==dest/'compact.lp'
            if method=='PS': assert o['--round112-ens-start-compact'] is True and '--round127-mode' not in o
            else: assert o['--round127-mode']=='p' and '--round112-ens-start-compact' not in o
        else:
            assert method=='S2' and o['--round127-mode']=='ms2'
    else:
        expression=launch['expression']
        assert method=='S2R' and launch['binary_layer']=='R132-research' and launch['research_PE'] is True
        assert o['--round127-mode']=='s2-root' and o['--round132-expression']==expression
        assert launch['comparison_method']==EXPRESSIONS[expression]
    if method not in ('P','PS'):
        assert o['--method']=='gcap-frontier' and o['--algorithm-preset']=='research-round83-vds-equal-net-exchange'
        assert o['--round98-state-service']=='m-binary' and o['--round90-lp-g-split']=='false'
    return dest


def frozen_contract(out):
    for name,digest in PINNED.items():
        assert sha(out/name)==digest,('accepted immutable binding changed',name)
    dplan,cplan=read(out/'experiment_plan.json'),read(out/'C_experiment_plan.json')
    recipe,inputs=read(out/'source_recipe.json'),read(out/'input_manifest.json')
    db,cb=read(out/'D_execution_binding.json'),read(out/'C_execution_binding.json')
    da,ca=read(out/'D_argv_freeze.json'),read(out/'C_argv_freeze.json')
    asset,build=read(out/'E3_binding.json'),read(out/'research_build.json')
    assert dplan['round']==132 and dplan['base']==BASE and dplan['limits']==LIMITS and dplan['total_G1_limit']==144000
    for key,name in (('plan_SHA','experiment_plan.json'),('inputs_SHA','input_manifest.json'),('argv_SHA','D_argv_freeze.json')):
        assert db[key]==sha(out/name)
    for key,name in (('plan_SHA','C_experiment_plan.json'),('argv_SHA','C_argv_freeze.json'),('research_build_SHA','research_build.json')):
        assert cb[key]==sha(out/name)
    assert asset['PE_SHA']==PE and asset['DLL_SHA']==DLL and asset['source_commit']==SOURCE
    assert cb['PE_SHA']==build['PE_SHA']==RESEARCH_PE and cb['DLL_SHA']==build['DLL_SHA']==DLL
    assert build['default']=='off' and build['options']==['off','geom','sp']
    assert sha(ROOT/'scripts/round132_build.py')==build['generator_SHA']
    assert sha(ROOT/'scripts/Round132Expression.hpp')==build['header_SHA']
    assert sha(ROOT/'scripts/round132_C.py')==cb['runner_SHA']
    for name,digest in db['adapters'].items():
        assert sha(portable(name))==digest,('frozen producer adapter',name)
    assert len(recipe['roles'])==len(inputs['roles'])==12
    assert [p['id'] for p in inputs['roles']]==[f'{layer}-{role}' for layer in ('K','X') for role in ('15-S','15-B','20-S','20-U','35-B','35-U')]
    assert len({p['input_sha256'] for p in inputs['roles']})==12
    for initial,p in zip(recipe['roles'],inputs['roles']):
        assert all(p[k]==v for k,v in initial.items())
        assert sha(portable(p['input_path']))==p['input_sha256']
    assert cplan['pairs']==[list(x) for x in C_PAIRS] and cplan['formal_arms']==24 and cplan['cap_sum']==32400
    rows=[];keys=set();destinations=set();caps=collections.Counter();counts=collections.Counter()
    for line,groups,argv,binding,expected in (('D',dplan['D'],da,db,24),('C',cplan['groups'],ca,cb,8)):
        assert len(groups)==len(argv['plans'])==len(binding['groups'])==expected
        for number,(g,plan) in enumerate(zip(groups,argv['plans']),1):
            assert g['number']==number and sha(out/g['name']/'identity.json')==binding['groups'][g['name']]
            assert plan==read(out/g['name']/'identity.json') and plan['dll_sha256']==DLL
            assert plan['candidate_binary_sha256']==(PE if line=='D' else RESEARCH_PE)
            assert plan['source_hashes']==asset['source_bindings'] and plan['measured_source_commit']==SOURCE
            common=plan['prereg']['common']
            for k,v in dict(affinity_mask=4,threads=1,mip_threads=1,gurobi_presolve=-1,gurobi_seed=g['seed'],
                requested_mip_gap=0,requested_mip_gap_abs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,
                OptimalityTol=1e-6,native_limit_offset_seconds=6,hard_stop_offset_seconds=2,shutdown_margin_seconds=30).items():
                assert common[k]==v,('numerical/clock contract',line,number,k)
            if line=='D':
                prereg=recipe['full_run_table'][number-1]
                assert g['methods']==prereg['methods'] and g['seed']==prereg['seed'] and g['pairs']==prereg['pairs']
                assert [l['method'] for l in plan['launches']]==g['methods']
                assert g['role']==inputs['roles'][(number-1)//2]
            else:
                assert (g['role']['id'],g['role']['cap_seconds'])==C_ROLES[(number-1)//2]
                assert g['seed']==(number-1)%2 and sorted(g['expressions'])==['geom','off','sp']
                assert [l['expression'] for l in plan['launches']]==g['expressions']
            for position,l in enumerate(plan['launches'],1):
                assert l['number']==position
                if line=='D': assert l['group_number']==number
                dest=command_contract(line,g,l)
                key=(line,g['role']['id'],g['seed'],l.get('comparison_method',l['method']))
                assert key not in keys and dest not in destinations
                keys.add(key);destinations.add(dest);caps[line]+=l['cap_seconds'];counts[line]+=1
            rows.append((line,g,plan))
    assert counts==dict(D=60,C=24) and caps==dict(D=84000,C=32400)
    assert read(out/'E_experiment_plan.json')['cases']==list(CASES)
    assert sha(ROOT/'scripts/round132_joint.py')==E_RUNNER
    amendment=out/'engineering/E_shortage_coverage_amendment'
    before,after=read(amendment/'before.json'),read(amendment/'after.json')
    assert before['E_owned_output_absent'] and before['E_owned_fee_absent'] and before['E_enumeration_H_LP_support_not_exposed']
    assert before['D_C_results_not_used_for_case_selection'] and before['new_Optimize']==0
    assert sha(amendment/'E_experiment_plan.json')==after['old_plan_SHA']==before['files']['E_experiment_plan.json']
    assert sha(amendment/'round132_joint.py')==after['old_runner_SHA']==before['files']['round132_joint.py']
    assert after['new_plan_SHA']==PINNED['E_experiment_plan.json'] and after['new_runner_SHA']==E_RUNNER
    old_plan,new_plan=read(amendment/'E_experiment_plan.json'),read(out/'E_experiment_plan.json')
    assert {k:v for k,v in old_plan.items() if k not in ('UTC','cases')}=={k:v for k,v in new_plan.items() if k not in ('UTC','cases')}
    old_runner=(amendment/'round132_joint.py').read_text(encoding='utf-8')
    amended=old_runner.replace("id='J2',b=[2,2,0,0]","id='J2',b=[2,1,0,0]").replace("id='J3',b=[2,1,1,0]","id='J3',b=[2,1,0,0]")
    actual_runner=(ROOT/'scripts/round132_joint.py').read_text(encoding='utf-8')
    text_keys=('zero_cutoff','proof_binding','control_policy')
    tree=ast.parse(actual_runner);freeze=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='freeze')
    restored={n.arg:ast.literal_eval(n.value) for n in ast.walk(freeze) if isinstance(n,ast.keyword) and n.arg in text_keys}
    assert restored=={k:old_plan[k] for k in text_keys}
    without_restored=''.join(line for line in actual_runner.splitlines(keepends=True) if not any(line.strip().startswith(k+'=') for k in text_keys))
    assert amended==without_restored,'coverage correction changed more than the two inventories and preservation of existing text contracts'
    for line in ('D','C'):
        gate=read(out/'review'/f'{line}_admission.json')
        assert gate['decision']=='ACCEPT' and gate[f'{line}_execution_binding_SHA']==sha(out/f'{line}_execution_binding.json')
    return rows,dict(formal_arms=dict(counts),nominal_caps=dict(caps),typed_comparisons=64,
        D_primary_problems=12,D_primary_repeated_comparisons=24,PS_problems=6,PS_repeated_comparisons_per_direction=12,
        C_problems=4,C_repeated_comparisons_per_candidate=8,C_shared_baselines=8,
        original_and_research_binary_declarations_checked=True,binary_bytes_required_or_loaded=False)


def readiness(out,rows,own_fee=None):
    """Existence and small cost metadata only; no raw content is opened here."""
    missing=[]
    for line,g,plan in rows:
        for name in ('reconstructed.json',):
            if not (out/g['name']/name).is_file(): missing.append(rel(out/g['name']/name))
        for launch in plan['launches']:
            dest=portable(launch['destination'])
            for name in ('arm_total_receipt.json','producer_receipt.json','producer_seal.json','verification_closeout.json',
                'result.json','completion.json','audit.json','independent_evidence.json','native_claims.json','claim_rejections.json'):
                if not (dest/name).is_file(): missing.append(rel(dest/name))
        label=f'formal_{line}{g["number"]:02d}_01'
        rp=out/'fees'/label/'receipt.json'
        if not rp.is_file(): missing.append(rel(rp))
        else: assert read(rp)['exit_observed'],('formal outer process not observed closed',label)
    for name in ('observations.json','stratified_summary.json','resource_accounting.json','joint_results.json',
                 'physical_outcomes.csv','mechanism_costs.csv','trajectory_index.json','analysis_inputs.json',
                 'native_progress_index.json','historical_physical_outcomes.json','research_source_publication.json','sequence_completion.json',
                 'problem_objective_classification.json','timing_environment_exposure.csv','timing_environment_amendment.json',
                 'source_loss_dispositions.json'):
        if not (out/name).is_file(): missing.append(rel(out/name))
    for path in sorted((out/'fees').glob('*/launch.json')):
        if not (path.parent/'receipt.json').is_file():
            launch=read(path)
            if path.parent.name==own_fee:
                assert launch['kind'] not in LIMITS and any(str(x).replace('\\','/').endswith('/scripts/round132_portable_check.py') for x in launch['command'])
            else: missing.append(rel(path.parent/'receipt.json'))
    for path in sorted((out/'delivery_costs').glob('*/launch.json')):
        if not (path.parent/'receipt.json').is_file() and not this_readonly_delivery(read(path)):
            missing.append(rel(path.parent/'receipt.json'))
    return missing


def this_readonly_delivery(launch):
    """Only this checker can have a currently open non-G1 outer receipt."""
    command=launch.get('command',[])
    scripts=[x for x in command if str(x).replace('\\','/').endswith('/scripts/round132_portable_check.py')]
    if len(scripts)!=1 or Path(scripts[0]).resolve()!=ROOT/'scripts/round132_portable_check.py': return False
    if launch.get('kind')!='separate_delivery' or launch.get('G1') is not False or not launch.get('nested_child_time_not_added'): return False
    if '--receipt' not in command or '--receipt' not in sys.argv: return False
    return Path(command[command.index('--receipt')+1]).resolve()==Path(sys.argv[sys.argv.index('--receipt')+1]).resolve()


def independent_pair(left,right,line,g):
    q=dict(line=line,group=g['number'],id=g['role']['id'],seed=g['seed'],left=left['method'],right=right['method'],
        layer=g['role']['layer'] if line=='D' else 'C',V=g['role']['V'],classification='UNEVALUABLE',direction='UNEVALUABLE',
        left_T_cert=left.get('T_cert'),right_T_cert=right.get('T_cert'),left_minus_right_seconds=None,
        right_over_left_certification_ratio=None,
        objective_class=left['objective_class'] if left['objective_class']==right['objective_class'] else 'mixed_attained_endpoints',
        left_stage_waiter_lifetime_overlap=left.get('stage_waiter_lifetime_overlap'),
        right_stage_waiter_lifetime_overlap=right.get('stage_waiter_lifetime_overlap'))
    if not eligible(left) or not eligible(right): return q
    for k in ('PE_SHA','DLL_SHA','input_SHA','seed','repeat'):
        assert left[k]==right[k],('matched pair identity',k)
    a,b=bool(left['certificate']),bool(right['certificate'])
    if a and b:
        if abs(left['U']-right['U'])>1e-7:
            q['obstacle']='certified physical objectives disagree; investigation required';return q
        lt,rt=left['T_cert'],right['T_cert'];assert min(lt,rt)>0
        dt=lt-rt;threshold=max(10.,.1*min(lt,rt))
        q.update(classification='BOTH_CERTIFIED',direction='Win' if dt<0 else 'Lose' if dt>0 else 'Tie',
            left_minus_right_seconds=dt,right_over_left_certification_ratio=rt/lt,
            material_threshold_seconds=threshold,materiality='LEFT_MATERIALLY_FASTER' if -dt>=threshold else 'RIGHT_MATERIALLY_FASTER' if dt>=threshold else 'TIME_CLOSE')
    elif a: q.update(classification='LEFT_ONLY_CERTIFIED',direction='Win')
    elif b: q.update(classification='RIGHT_ONLY_CERTIFIED',direction='Lose')
    else: q.update(classification='BOTH_OPEN',direction='UNDETERMINED')
    return q


def independent_problem_classes(arms):
    """Classify same-line/input problems from independently verified evidence.

    Attained positive U does not prove a positive optimum. Physical exact zero
    proves zero; otherwise only a qualified L>1e-7 gives the numerical-policy
    positive class. This function supplies no endpoint or certificate to an arm.
    """
    buckets=collections.defaultdict(list)
    for arm in arms:
        buckets[arm['line'],arm['input_SHA']].append(arm)
    classified={};records=[]
    for key in sorted(buckets):
        candidates=[a for a in buckets[key] if eligible(a)]
        zeros=[a for a in candidates if a.get('G_true')==0 and a.get('P_true')==0]
        positive=[a for a in candidates if a['L']>1e-7]
        assert not (zeros and positive),('qualified physical zero contradicts positive bound',key)
        if zeros:
            label='zero_proved_by_qualified_physical_zero';support=zeros
        elif positive:
            label='positive_under_qualified_lower_bound';support=positive
        else:
            label='unknown_optimum_class';support=[]
        classified[key]=label
        records.append(dict(line=key[0],input_SHA=key[1],ids=sorted({a['id'] for a in candidates}),
            problem_objective_class=label,evidence=[{k:a.get(k) for k in WITNESS_FIELDS} for a in support]))
    return classified,records


def assign_problem_classes(arms,pairs):
    # The caller first rejects cross-arm lower/upper contradictions. Preserve
    # every own endpoint/certificate/clock while adding only descriptive fields.
    protected=('U','L','certificate','T_cert','T_produce','T_verify','T_total')
    before=[tuple(a.get(k) for k in protected) for a in arms]
    classified,records=independent_problem_classes(arms)
    by_problem=collections.defaultdict(set)
    for a in arms:
        a['problem_objective_class']=classified[a['line'],a['input_SHA']]
        by_problem[a['line'],a['id']].add(a['problem_objective_class'])
    for p in pairs:
        labels=by_problem[p['line'],p['id']]
        assert len(labels)==1,('ambiguous problem identity in pair',p['line'],p['id'])
        p['problem_objective_class']=next(iter(labels))
    assert before==[tuple(a.get(k) for k in protected) for a in arms]
    return records


def independent_waiter_exposure(begin,end,environment):
    birth=environment['old_waiter_creation_unix']
    lower_stop=environment['old_waiter_stop_unix_lower'];upper_stop=environment['old_waiter_stop_unix_upper']
    assert all(math.isfinite(v) for v in (begin,end,birth,lower_stop,upper_stop))
    assert begin<=end and birth<=lower_stop<=upper_stop
    start=max(begin,birth)
    lower=max(0.,min(end,lower_stop)-start)
    upper=max(0.,min(end,upper_stop)-start)
    assert 0<=lower<=upper<=end-begin
    if lower>0:
        scope='conservative overlap with original waiter lifetime; not parsing/CPU-contention/slowdown seconds'
    elif upper>0:
        scope='possible boundary overlap with original waiter lifetime'
    else:
        scope='no original-waiter lifetime overlap; ambient load not ruled out'
    return dict(stage_waiter_lifetime_overlap_lower_seconds=lower,
        stage_waiter_lifetime_overlap_upper_seconds=upper,stage_waiter_lifetime_overlap=upper>0,
        timing_environment_scope=scope,counterfactual_clean_machine_T_cert=None)


def reporting_logic_preflight():
    """Tiny synthetic contract cases only; not campaign evidence or a solve."""
    def arm(name,input_sha,U,L,G,P,qualified=True,line='D'):
        return dict(id=name,line=line,input_SHA=input_sha,seed=0,method=name,producer_receipt_SHA='0'*64,
            U=U,L=L,G_true=G,P_true=P,certificate=False,T_cert=None,T_produce=3.,T_verify=1.,T_total=4.,
            formal_protocol_qualified=qualified,numbers_qualified=qualified,certificate_qualified=qualified,source_reduced=False)
    aa=[arm('positive_attainment','a',.5,0.,.2,2.),arm('physical_zero','a',0.,0.,0.,0.),
        arm('near_zero_positive','b',1e-10,0.,0.,1e-9),arm('positive_bound','c',.5,2e-7,.2,2.),
        arm('unqualified_zero','d',0.,0.,0.,0.,qualified=False),arm('separate_line','a',.5,0.,.2,2.,line='C')]
    pairs=[dict(line='D',id='positive_attainment')]
    before=copy.deepcopy(aa);records=assign_problem_classes(aa,pairs)
    classes={(r['line'],r['input_SHA']):r['problem_objective_class'] for r in records}
    assert classes['D','a']=='zero_proved_by_qualified_physical_zero'
    assert classes['D','b']==classes['D','d']==classes['C','a']=='unknown_optimum_class'
    assert classes['D','c']=='positive_under_qualified_lower_bound'
    assert pairs[0]['problem_objective_class']==classes['D','a']
    assert all({k:v for k,v in after.items() if k!='problem_objective_class'}==old for old,after in zip(before,aa))
    try: independent_problem_classes([arm('zero','x',0.,0.,0.,0.),arm('bound','x',1.,2e-7,.5,2.)])
    except AssertionError: pass
    else: raise AssertionError('zero/bound contradiction was not rejected before classification')
    environment=dict(old_waiter_creation_unix=10.,old_waiter_stop_unix_lower=20.,old_waiter_stop_unix_upper=22.)
    for begin,end,expected in ((0.,9.,(0.,0.,False)),(8.,12.,(2.,2.,True)),
        (19.,21.,(1.,2.,True)),(20.,21.,(0.,1.,True)),(22.,24.,(0.,0.,False))):
        actual=independent_waiter_exposure(begin,end,environment)
        assert tuple(actual[k] for k in LIFETIME_FIELDS[:3])==expected
        assert actual['counterfactual_clean_machine_T_cert'] is None
    return dict(status='PASS',scope='synthetic reporting contract only; no campaign data',
        physical_zero_priority_near_zero_unknown_and_qualified_bound_checked=True,
        same_input_other_line_separation_checked=True,contradictions_rejected_before_classification=True,
        own_endpoints_and_clocks_unchanged=True,lifetime_boundaries_and_counterfactual_null_checked=True)


def source_loss_logic_preflight():
    """Tiny invented fixtures; no raw files, readers, native code or solver."""
    arm=dict(formal_protocol_qualified=True,numbers_qualified=True,certificate_qualified=True,
        source_reduced=True,native_proof_qualified=False,certificate=True,own_exact_zero=True,
        proof_evidence='OWN_ZERO_CERTIFICATE',certificate_source='OWN_ZERO_CERTIFICATE',
        U=0.,L=0.,gap=0.,T_produce=3.)
    original=dict(T_cert=3.,certificate=True)
    physical=dict(G=0.,P=0.,F=0.,Y=[0,1])
    panel=dict(input_sha256='a'*64)
    panel['lambda']=.15
    data=dict(D=[0,1],w=[0.,1.])
    launch=dict(arm='A',panel=panel)
    witness=dict(arm='A',physical_verified=True,G=0.,P=0.,F=0.,input_SHA='a'*64,
        source='own committed routes',available=2.,sequence=5)
    own=dict(own_U=0.,own_exact_zero=True,own_physical_verified=True,independent_floor0=True,witnesses=[witness])
    scope=dict(full_original=False,lower_g=0.,upper_g=.2,cutoff=.2,model_sha256='b'*64)
    rejection=dict(arm='A',call=1,call_rejected_as_a_whole=True,domain_verified=True,
        model_SHA='b'*64,scope=scope,reason='local_bound_witness_inconsistency',value=2e-7,
        counterexample={k:witness[k] for k in ('arm','physical_verified','G','F','input_SHA','source','available')})
    local=dict(damaged_calls=[dict(arm='A',call=1)],rejections=[rejection])
    args=[arm,original,physical,panel,data,own,local,copy.deepcopy(local),launch]
    protected=copy.deepcopy(args)
    support=source_loss_endpoint_contract(*args)
    assert support['own_zero_witness_sequences']==[5] and args==protected and not eligible(arm)
    mutations=[(0,'native_proof_qualified',True),(0,'formal_protocol_qualified',False),
        (0,'own_exact_zero',False),(1,'T_cert',2.),(2,'G',1e-12),(5,'independent_floor0',False)]
    for index,key,value in mutations:
        altered=copy.deepcopy(args);altered[index][key]=value
        try:source_loss_endpoint_contract(*altered)
        except AssertionError:pass
        else:raise AssertionError(('unsubstantiated source loss accepted',index,key))
    for mutate in ('foreign_counterexample','small_bound','out_of_scope','no_own_witness','no_local_rejection','extra_cohort_damage'):
        altered=copy.deepcopy(args)
        if mutate=='foreign_counterexample':altered[6]['rejections'][0]['counterexample']['arm']='other'
        elif mutate=='small_bound':altered[6]['rejections'][0]['value']=1e-8
        elif mutate=='out_of_scope':altered[6]['rejections'][0]['scope']['lower_g']=.1
        elif mutate=='no_own_witness':altered[5]['witnesses']=[]
        elif mutate=='no_local_rejection':altered[6]['rejections']=[]
        else:altered[7]['damaged_calls'].append(dict(arm='A',call=2))
        try:source_loss_endpoint_contract(*altered)
        except AssertionError:pass
        else:raise AssertionError(('insufficient own source-loss proof accepted',mutate))
    shared=dict(line='D',id='synthetic',seed=0,repeat=1,PE_SHA='p',DLL_SHA='d',input_SHA='a',
        objective_class='zero',native_proof_qualified=True)
    left=dict(shared,**arm,method='A',T_cert=None,censored=None)
    right=dict(left,method='B',source_reduced=False,native_proof_qualified=True,T_cert=4.,T_produce=4.,censored=False)
    group=dict(number=1,seed=0,role=dict(id='synthetic',V=1,layer='K'))
    q=independent_pair(left,right,'D',group)
    ss=reporting_disposition_summary([left,right],[q],[left])
    assert q['direction']==q['classification']=='UNEVALUABLE' and ss['performance_qualified_observations']==1
    assert not ss['unresolved_unqualified_observations'] and not ss['unresolved_unevaluable_comparisons']
    unresolved=reporting_disposition_summary([left,right],[q],[])
    assert unresolved['unresolved_unqualified_observations'] and unresolved['unresolved_unevaluable_comparisons']
    return dict(status='PASS',scope='synthetic own-zero/source-loss reporting contract only',
        frozen_performance_eligibility_unchanged=True,raw_own_zero_and_clock_not_mutated=True,
        foreign_witness_and_missing_own_rejection_blocked=True,nonzero_or_unclosed_evidence_not_waived=True,
        source_loss_position_retained_as_UNEVALUABLE=True,unexplained_unqualified_evidence_blocks=True)


def summarized(aa,pp):
    both=[q for q in pp if q['classification']=='BOTH_CERTIFIED']
    ratios=[q['right_over_left_certification_ratio'] for q in both]
    return dict(problems=len({q['id'] for q in pp}),repeated_comparisons=len(pp),
        directions=dict(collections.Counter(q['direction'] for q in pp)),classes=dict(collections.Counter(q['classification'] for q in pp)),
        certificates={m:sum(eligible(a) and a['certificate'] for a in aa if a['method']==m) for m in sorted({a['method'] for a in aa})},
        both_certified_n=len(both),both_certified_intersection=[dict(id=q['id'],seed=q['seed']) for q in both],
        conditional_geometric_mean_right_over_left=math.exp(statistics.fmean(map(math.log,ratios))) if ratios else None)


def strata(arms,pairs):
    broad={};fine={}
    for line in ('D','C'):
        pp=[q for q in pairs if q['line']==line]
        for left,right in sorted({(q['left'],q['right']) for q in pp}):
            selected=[q for q in pp if (q['left'],q['right'])==(left,right)]
            def summary_of(qq):
                keys={(q['id'],q['seed']) for q in qq}
                aa=[a for a in arms if a['line']==line and a['method'] in (left,right) and (a['id'],a['seed']) in keys]
                return summarized(aa,qq)
            for layer in sorted({q['layer'] for q in selected}):
                broad[f'{line}:{layer}:{left}/{right}']=summary_of([q for q in selected if q['layer']==layer])
            for dimension in ('id','V','objective_class','problem_objective_class'):
                for value in sorted({str(q[dimension]) for q in selected}):
                    fine[f'{line}:{left}/{right}:{dimension}={value}']=summary_of([q for q in selected if str(q[dimension])==value])
            if line=='D':
                for layer in ('K','X'):
                    for size in sorted({q['V'] for q in selected if q['layer']==layer}):
                        fine[f'D:{layer}:{left}/{right}:V={size}']=summary_of([q for q in selected if q['layer']==layer and q['V']==size])
    return broad,fine


@contextlib.contextmanager
def no_handoff_write(adapter):
    old=adapter.write;notes=[]
    def record(path,value):
        path=portable(path);assert path.name=='round127_empty_route_handoff.json',('unexpected reader mutation',path)
        if path.exists(): assert read(path)==value
        notes.append(dict(path=rel(path),recomputed=True,raw_modified=False))
    adapter.write=record
    try: yield notes
    finally: adapter.write=old


def reader_imports():
    sys.path.insert(0,str(ROOT/'scripts'))
    # Keep these narrow, deferred imports explicit so the publisher's static
    # dependency closure also includes the pure reader and helper modules.
    with disabled_ffi_import():
        import round108_reader as core
        import read_round118 as reconstruction
        import read_round116 as source_reader
        import round130_evidence as evidence
        import round127_evidence as handoff
        import compare_round112_startup as H
        import round130_portable_check as prior
    modules=[core,reconstruction,source_reader,evidence,handoff,H,prior]
    for module in list(sys.modules.values()):
        file=getattr(module,'__file__',None)
        if not file or Path(file).resolve().parent!=ROOT/'scripts': continue
        if Path(file).resolve()==Path(__file__).resolve(): continue
        assert Path(file).resolve().is_relative_to(ROOT)
        if hasattr(module,'ROOT'): module.ROOT=ROOT
        if hasattr(module,'portable'):
            # Most inherited readers use portable(root,value), the old portable
            # checker uses portable(value). Both routes enforce the same ROOT.
            module.portable=(lambda root,value: portable(value)) if module.__name__!='round130_portable_check' else portable
    for module in modules:
        assert Path(module.__file__).resolve().is_relative_to(ROOT),('foreign reader import',module.__name__)
    modules[0].start_reader.ROOT=ROOT
    return modules


@contextlib.contextmanager
def readonly_boundary():
    """Fail closed if an inherited pure reader tries an old path or mutation."""
    state={'active':True};runtime=Path(sys.base_prefix).resolve()
    def hook(event,args):
        if not state['active']: return
        if event in ('subprocess.Popen','os.system','ctypes.dlopen','os.exec','os.posix_spawn'):
            raise AssertionError(('forbidden native/process action in pure review',event))
        if event=='import' and str(args[0]).split('.')[0] in ('gurobipy','gurobi','cplex'):
            raise AssertionError(('forbidden solver import',args[0]))
        if event=='open' and isinstance(args[0],(str,bytes,Path)):
            path=Path(args[0]).resolve();mode=args[1] if len(args)>1 else None
            flags=args[2] if len(args)>2 else 0
            assert not (isinstance(mode,str) and any(c in mode for c in 'wax+')),('reader write attempt',path)
            assert not writable_open_flags(flags),('reader write flags',path,flags)
            assert path.is_relative_to(ROOT) or path.is_relative_to(runtime),('read outside supplied root',path)
            assert path.suffix.lower() not in ('.exe','.dll'),('binary bytes are not evidence-reader input',path)
    sys.addaudithook(hook)
    try: yield
    finally: state['active']=False


def fleet_resources(core,p,physical):
    data=core.evidence.instance(ROOT,p);routes=[];returns=[]
    for route in physical['routes']:
        k=route['vehicle'];ops={o['station']:o for o in route['operations']}
        load=peak=P=D=0
        for station in route['nodes'][1:-1]:
            op=ops[station];P+=op['pickup'];D+=op['drop'];load+=op['pickup']-op['drop'];peak=max(peak,load)
            assert 0<=load<=p['Q_vector'][k]
        distance=math.fsum(math.dist(data['xy'][i],data['xy'][j]) for i,j in zip(route['nodes'],route['nodes'][1:]))
        travel=distance/1.5;handling=(p['pickup_seconds']+p['drop_seconds'])*P
        assert travel+handling<=p['T_seconds']+1e-7
        returns.append(load)
        routes.append(dict(vehicle=k,stations=len(ops),pickup=P,drop=D,return_load=load,peak_load=peak,Q=p['Q_vector'][k],
            travel_seconds=travel,handling_seconds=handling,total_seconds=travel+handling,T=p['T_seconds']))
    assert sum(physical['Y'][1:])==sum(data['b'][1:])-sum(returns)
    omega=sum(data['w'][1:]);assert omega>0
    return dict(G_true=physical['G'],P_true=physical['P'],P_avg=physical['P']/omega,Omega=omega,
        lambda_value=p['lambda'],rho=p['lambda']*omega,final_inventory=physical['Y'][1:],initial_inventory=data['b'][1:],target=data['D'][1:],
        total_initial_inventory=sum(data['b'][1:]),total_final_inventory=sum(physical['Y'][1:]),
        serviced_stations=sum(q['stations'] for q in routes),pickups=[q['pickup'] for q in routes],
        drops=[q['drop'] for q in routes],return_loads=returns,route_resources=routes)


def validate_seal(dest,launch,plan):
    producer,total=read(dest/'producer_receipt.json'),read(dest/'arm_total_receipt.json')
    seal,closeout=read(dest/'producer_seal.json'),read(dest/'verification_closeout.json')
    origin,completion=read(dest/'child_process_origin.json'),read(dest/'completion.json')
    assert origin['command']==launch['command'] and origin['PE_SHA']==plan['candidate_binary_sha256'] and origin['seed']==launch['seed']
    assert origin['creation_from_live_OS_handle'] is True
    assert producer['producer_seal_SHA']==sha(dest/'producer_seal.json')
    assert seal['native_stopped_no_reentry'] and seal['required_outputs_closed']
    for name,digest in seal['required_SHA'].items():
        path=(dest/name).resolve();assert path.is_relative_to(dest)
        assert sha(path)==digest,('producer sealed output changed',rel(dest),name)
    assert total['producer_receipt_SHA']==closeout['producer_receipt_SHA']==sha(dest/'producer_receipt.json')
    assert total['verification_closeout_SHA']==sha(dest/'verification_closeout.json')
    for key,name in (('audit_SHA','audit.json'),('own_evidence_SHA','independent_evidence.json'),
                     ('claims_SHA','native_claims.json'),('rejection_SHA','claim_rejections.json')):
        assert closeout[key]==sha(dest/name)
    assert closeout['no_new_solution_or_certificate_backfilled'] and closeout['necessary_verification_complete']
    produced=producer['t_produce_perf']-producer['t0_perf'];verified=total['t_verified_perf']-producer['t_produce_perf']
    assert 0<produced<=launch['cap_seconds'] and verified>=0
    assert completion['returncode']==0 and completion['stop_reason']=='normal_return' and completion['within_cap']
    return dict(T_produce=produced,T_verify=verified,T_total=produced+verified,
        producer_interval_unix=[producer['t0_unix'],producer['t_produce_unix']],
        producer_seal_SHA=sha(dest/'producer_seal.json'),producer_receipt_SHA=sha(dest/'producer_receipt.json'),
        verification_closeout_SHA=sha(dest/'verification_closeout.json'))


def geometry_difference(base,other,n,beta,targets):
    for key in ('objective','order','types','bounds'):
        assert base[key]==other[key],('geometry non-row difference',key)
    expected=collections.Counter();families=collections.Counter()
    rnames=[f'r_{i}' for i in range(1,n+1)]
    supper=0.
    # r's own box remains the capacity box. The factory's centering constant
    # uses the tightened integer Y domain divided by target, not that box.
    for i in range(1,n+1): supper+=base['bounds'][f'Y_{i}'][1]/targets[i]
    fixed=max(0.,n*beta*supper/(n-1));c=-float(n)*beta
    def row(co,rhs):
        return tuple(sorted((k,v) for k,v in co.items() if v)), '<=', rhs
    for i in range(1,n+1):
        for j in range(i+1,n+1):
            co={name:c for name in rnames};co[f'h_{i}_{j}']=float(n-1)
            expected[row(co,0.)]+=1;families['spread']+=1
            for a,b in ((i,j),(j,i)):
                expected[row({f'r_{a}':1.,f'r_{b}':-1.},fixed)]+=1;families['fixed_centering']+=1
                co={name:c for name in rnames};co[f'r_{a}']+=float(n-1);co[f'r_{b}']-=float(n-1)
                expected[row(co,0.)]+=1;families['variable_S_centering']+=1
    a,b=collections.Counter(base['rows']),collections.Counter(other['rows'])
    assert not b-a and a-b==expected,('geometry exact family/multiplicity difference',n,beta)
    return dict(deleted_families=dict(families),deleted_rows=sum(expected.values()),added_rows=0,
        all_other_rows_columns_domains_types_objective_preserved=True)


def projection_difference(base,other):
    assert base['objective']==other['objective']
    columns=set(base['types'])-{'W_SP'};assert set(other['types'])==columns
    for name in columns:
        assert base['types'][name]==other['types'][name] and base['bounds'][name]==other['bounds'][name]
    low=[];high=[];keep=[]
    for terms,sense,rhs in base['rows']:
        co=dict(terms)
        if not co.get('W_SP',0): keep.append((terms,sense,rhs));continue
        assert sense!='='
        if sense=='>=': co={k:-v for k,v in co.items()};rhs=-rhs
        item=({k:F.from_float(v) for k,v in co.items()},F.from_float(rhs))
        (low if co['W_SP']<0 else high).append(item)
    assert len(low)==2 and len(high)==3,('complete four MC plus active SP W uses',len(low),len(high))
    lo,hi=base['bounds']['W_SP'];low.append(({'W_SP':F(-1)},-F.from_float(lo)));high.append(({'W_SP':F(1)},F.from_float(hi)))
    after=collections.Counter(other['rows']);unchanged=collections.Counter(keep)
    assert not unchanged-after
    actual=list((after-unchanged).elements());assert len(actual)==len(low)*len(high)==12
    residuals=[]
    for l,lr in low:
        for u,ur in high:
            a,b=-l['W_SP'],u['W_SP']
            co={k:b*l.get(k,F(0))+a*u.get(k,F(0)) for k in l.keys()|u.keys() if k!='W_SP'}
            co={k:v for k,v in co.items() if v};rhs=b*lr+a*ur;matches=[]
            for j,(terms,sense,rr) in enumerate(actual):
                cc=dict(terms)
                if sense!='<=' or cc.keys()!=co.keys(): continue
                err=abs(F.from_float(rr)-rhs)+sum(abs(F.from_float(cc[k])-v)*F.from_float(max(map(abs,base['bounds'][k]))) for k,v in co.items())
                matches.append((err,j))
            assert matches,('FM row support/multiplicity absent',co.keys())
            err,j=min(matches);actual.pop(j);residuals.append(float(err))
    assert not actual and max(residuals)<1e-7
    return dict(removed_W_columns=1,removed_W_rows=5,complete_reference_FM_pairs=12,
        coefficient_domain_serialization_residual_bound=max(residuals),all_other_domains_types_objective_preserved=True,
        exact_reference_rational_combinations=True,serialized_output_checked_numerically_not_exact_equivalence=True)


def formal_evidence(out,rows):
    core,reconstruction,source_reader,evidence,handoff,H,prior=reader_imports()
    assets=read(out/'E3_binding.json')
    for name,digest in assets['source_bindings'].items():
        assert sha(portable(name))==digest,('original production source changed',name)
    environment_path=out/'timing_environment_amendment.json';environment=read(environment_path)
    reporting_inputs=[dict(path=rel(environment_path),SHA=sha(environment_path))]
    arms=[];pairs=[];artifacts=[];inputs=[];physical_rows=[];errors=[];mechanisms=[];notes=[];losses=[]
    for line,g,plan in rows:
        camp=out/g['name'];saved=read(camp/'reconstructed.json')['arms'];assert len(saved)==len(plan['launches'])
        inputs.append(dict(line=line,group=g['number'],identity=rel(camp/'identity.json'),identity_SHA=sha(camp/'identity.json'),
            reconstructed=rel(camp/'reconstructed.json'),reconstructed_SHA=sha(camp/'reconstructed.json')))
        for original,launch in zip(saved,plan['launches']):
            assert (original['id'],original['input_SHA'],original['seed'],original['method'])==(launch['id'],launch['panel']['input_sha256'],launch['seed'],launch['method'])
            assert portable(original['destination'])==portable(launch['destination'])
            assert original['PE_SHA']==plan['candidate_binary_sha256'] and original['DLL_SHA']==DLL
        recs=collections.defaultdict(list);items=[];local={};native={};hs={}
        with no_handoff_write(handoff) as diagnostic,evidence.extension():
            for launch in plan['launches']:
                try: items.append(reconstruction.item(ROOT,launch,plan,recs))
                except Exception as error:
                    items.append(None);errors.append(dict(line=line,group=g['number'],method=launch.get('comparison_method',launch['method']),stage='reader_item',error=repr(error)))
            witnesses=[dict(w,arm=item['l']['method']) for item in items if item is not None and item['complete'] for w in item['ind']['witnesses']]
            for launch,original,item in zip(plan['launches'],saved,items):
                method=launch.get('comparison_method',launch['method']);dest=portable(launch['destination']);p=launch['panel']
                try:
                    assert item is not None and item['complete'],'sealed arm could not be independently reconstructed'
                    finding=source_reader.reconcile(item.get('claims',[]),witnesses)
                    arm=reconstruction.finalize(ROOT,item,finding,recs)
                    clocks=validate_seal(dest,launch,plan);result=read(dest/'result.json')
                    assert arm['producer_receipt_SHA']==original['producer_receipt_SHA']==clocks['producer_receipt_SHA']
                    reporting_inputs.append(dict(path=rel(dest/'producer_receipt.json'),SHA=clocks['producer_receipt_SHA']))
                    physical=core.full_fleet(ROOT,p,result);same(physical['F'],arm['U'],1e-7)
                    for key in ('U','L','gap','T_produce','T_verify','T_total'):
                        same(arm[key],original[key])
                    same(arm['gap'],arm['U']-arm['L'],1e-14)
                    for key in ('certificate','formal_protocol_qualified','numbers_qualified','certificate_qualified','source_reduced'):
                        assert original.get(key,False)==arm.get(key,False),(line,g['number'],method,key)
                    for key in ('native_proof_qualified','own_exact_zero','certificate_source','proof_evidence','rejected_calls'):
                        assert original.get(key)==arm.get(key),(line,g['number'],method,key)
                    for key in ('T_produce','T_verify','T_total'): same(arm[key],clocks[key])
                    raw_tcert=arm['T_produce'] if arm.get('formal_protocol_qualified') and arm['certificate'] else None
                    equal(raw_tcert,original['T_cert'],'unaltered producer reconstruction certificate clock')
                    loss=None
                    if arm.get('source_reduced'):
                        loss=source_loss_record(core,item,finding,arm,original,physical,launch,line,method)
                    tcert=arm['T_produce'] if eligible(arm) and arm['certificate'] else None
                    resource=fleet_resources(core,p,physical)
                    arm.update(line=line,group=g['number'],method=method,seed=g['seed'],repeat=1,
                        underlying_reader_method=launch['method'],binary_layer=launch['binary_layer'],T_cert=tcert,
                        raw_reconstructed_T_cert=original['T_cert'],raw_reconstructed_certificate=original['certificate'],
                        formal_performance_evidence_eligible=eligible(arm),censored=not arm['certificate'] if eligible(arm) else None,
                        performance_qualification_disposition=SOURCE_LOSS_DISPOSITION if loss else 'QUALIFIED' if eligible(arm) else 'UNQUALIFIED_UNRESOLVED',
                        signed_gap=arm['U']-arm['L'],layer=p['layer'] if line=='D' else 'C',
                        objective_class='zero' if physical['G']==0 and physical['P']==0 else 'positive',
                        near_zero_positive_U=0<arm['U']<=1e-7)
                    arm.update({k:resource[k] for k in ('G_true','P_true','P_avg','Omega','rho')})
                    arm.update(independent_waiter_exposure(*clocks['producer_interval_unix'],environment))
                    physical_rows.append(dict(line=line,id=arm['id'],seed=arm['seed'],method=method,**resource))
                    calls=[q['payload'] for q in read(dest/'observations.json') if q['payload']['kind']=='call']
                    assert len({q['call'] for q in calls})==len(calls)
                    facts=[];root_model=None;root_call=None;seen=set()
                    for call in calls:
                        path=portable(call['model_path']);assert sha(path)==call['model_sha256']
                        assert call['settings']==dict(read_return_code=0,Threads=1,Seed=g['seed'],Presolve=-1,
                            MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)
                        if call['model_sha256'] not in seen:
                            m=core.lp_model(path);family=collections.Counter(prior.support_family(r) for r in m['rows'])
                            if launch['method']=='S2': assert family['cover_3']==family['conditional_3']==0
                            facts.append(dict(SHA=call['model_sha256'],rows=len(m['rows']),columns=len(m['order']),
                                nonzeros=sum(len(t) for t,s,b in m['rows']),pair_cover=family['cover_2'],pair_conditional=family['conditional_2'],
                                triple_cover=family['cover_3'],triple_conditional=family['conditional_3'],ordered_supply=family['ordered_supply'],W_present='W_SP' in m['types']))
                            seen.add(call['model_sha256'])
                            if root_call is None and (call['full_original'] or call['leaf']=='L0'): root_call,root_model=call,m
                    assert read(dest/'call_log_views.json')['bindings']==item['view']['bindings']
                    assert read(dest/'call_log_views.json')['actual_Optimize']==arm['native_Optimize']
                    entry=dict(launch=launch,dest=dest,result=result,calls=calls,arm=arm,item=item)
                    detail=None
                    if launch['method']=='P':
                        assert read(dest/'round127_parameters.json')==dict(MIPFocus=0,Cuts=-1,NumStart_before_optimize=0,loaded_after_presets=True,authoritative_model_environment=True)
                        if calls: assert len(calls)==1 and calls[0]['full_original'] and sha(dest/'compact.lp')==p['reference']['canonical_sha256']
                    else:
                        own=H.reconstruct(ROOT,p,dest);hs[method]=own
                        if line=='C' and own['complete']:
                            detail=prior.root_chain(core,entry,own)
                        elif line=='D' and launch['method']=='S2' and calls:
                            detail=prior.split_cover_details(core,entry)
                        elif launch['method']=='PS' and calls:
                            detail=importlib.import_module('round112_audit').start_audit(ROOT,p,dest)
                    native[method]=dict(root=root_model,call=root_call,own_H=hs.get(method),native_Optimize=arm['native_Optimize'])
                    external_ledger=bool(core.rows(dest/'external/paper_optimize_ledger.csv')) if (dest/'external/paper_optimize_ledger.csv').is_file() else False
                    root_attributes=dict(root_rows=len(root_model['rows']) if root_model else None,
                        root_columns=len(root_model['order']) if root_model else None,
                        root_nonzeros=sum(len(t) for t,s,b in root_model['rows']) if root_model else None,
                        root_W_present='W_SP' in root_model['types'] if root_model else None,
                        root_scope=[root_call['lower_g'],root_call['upper_g']] if external_ledger and root_call else None,
                        root_cutoff=root_call.get('cutoff') if external_ledger and root_call else None)
                    artifacts.append(dict(line=line,group=g['number'],id=arm['id'],seed=arm['seed'],method=method,
                        final_fleet=physical,qualified=eligible(arm),certificate=arm['certificate'],native_Optimize=arm['native_Optimize'],
                        native_proof_qualified=arm.get('native_proof_qualified'),source_reduced=arm.get('source_reduced',False),
                        own_physical_zero_certificate_retained=bool(loss),raw_reconstructed_T_cert=original['T_cert'],
                        source_return_cover_rebuilt=True,actual_returned_calls=item['chain']['actual'],
                        actual_models=facts,root_attributes=root_attributes,domain_Start_or_cover=detail,
                        own_H_complete=hs[method]['complete'] if method in hs else None,**clocks))
                    if loss:losses.append(loss)
                except Exception as error:
                    errors.append(dict(line=line,group=g['number'],method=method,stage='arm_qualification',error=repr(error)))
                    arm=dict(line=line,group=g['number'],id=launch['id'],seed=g['seed'],repeat=1,method=method,
                        PE_SHA=plan['candidate_binary_sha256'],DLL_SHA=DLL,input_SHA=p['input_sha256'],binary_layer=launch['binary_layer'],
                        formal_protocol_qualified=False,numbers_qualified=False,certificate_qualified=False,source_reduced=False,
                        U=None,L=None,gap=None,signed_gap=None,certificate=False,T_produce=None,T_verify=None,T_total=None,T_cert=None,
                        objective_class='unknown',layer=p['layer'] if line=='D' else 'C',raw_saved_endpoint=original,
                        failure_reason=repr(error))
                arms.append(arm);assert method not in local;local[method]=arm
        notes.extend(diagnostic)
        if line=='C' and set(native)==set(EXPRESSIONS.values()):
            off=native['S2R'];group_facts=dict(line=line,group=g['number'],id=g['role']['id'],seed=g['seed'])
            if all(hs[m]['complete'] for m in EXPRESSIONS.values()):
                assert all(hs[m]['fleet']==hs['S2R']['fleet'] and hs[m]['semantic_traces']==hs['S2R']['semantic_traces'] for m in EXPRESSIONS.values())
                group_facts['independently_paid_H_semantics_and_capacity_assigned_fleets_equal']=True
            else: group_facts['backend_attribution']='H incomplete; no native cost attribution admitted'
            if all(native[m]['root'] is not None for m in EXPRESSIONS.values()):
                for m in EXPRESSIONS.values():
                    for field in ('lower_g','upper_g','cutoff'): same(native[m]['call'][field],off['call'][field],0.)
                targets=core.evidence.instance(ROOT,g['role'])['D']
                group_facts['geometry']=geometry_difference(off['root'],native['S2R-GEOM']['root'],g['role']['V'],off['call']['upper_g'],targets)
                group_facts['projection']=projection_difference(off['root'],native['S2R-SP']['root'])
            else: group_facts['actual_matrix_difference']='UNEXPOSED; no actual matrix fabricated'
            mechanisms.append(group_facts)
        if line=='D' and 'PS' in hs and 'S2' in hs:
            fields=dict(full_H_complete=hs['PS']['complete'] and hs['S2']['complete'],
                semantic_trace_equal=hs['PS']['semantic_traces']==hs['S2']['semantic_traces'],
                complete_capacity_assigned_fleet_equal=hs['PS']['fleet']==hs['S2']['fleet'])
            mechanisms.append(dict(line=line,group=g['number'],id=g['role']['id'],seed=g['seed'],PS_S2_own_H=fields,
                backend_attribution_eligible=all(fields.values()) and all(native[m]['native_Optimize']>0 for m in ('PS','S2'))))
        wanted=g['pairs'] if line=='D' else C_PAIRS
        pairs.extend(independent_pair(local[left],local[right],line,g) for left,right in wanted)
    assert len(arms)==len({(a['line'],a['id'],a['seed'],a['method']) for a in arms})==84
    assert len(pairs)==64 and sum(q['line']=='D' for q in pairs)==48 and sum(q['line']=='C' for q in pairs)==16
    dispositions=reporting_disposition_summary(arms,pairs,losses)
    conflicts=[]
    for key in sorted({(a['line'],a['input_SHA']) for a in arms}):
        aa=[a for a in arms if (a['line'],a['input_SHA'])==key and a['U'] is not None]
        best=min((a['U'] for a in aa),default=None)
        for a in aa:
            if eligible(a) and a['L']>best+1e-7:
                conflicts.append(dict(line=a['line'],id=a['id'],seed=a['seed'],method=a['method'],own_L=a['L'],other_verified_U=best))
    problem_records=[]
    if conflicts or errors:
        # A contradiction must be reported before a problem is labelled zero
        # or positive. No normal reporting table is qualified on this branch.
        broad,fine={},{}
    else:
        problem_records=assign_problem_classes(arms,pairs)
        broad,fine=strata(arms,pairs)
    return dict(arms=arms,pairs=pairs,arm_evidence=artifacts,physical_rows=physical_rows,
        strata=broad,problem_size_objective_strata=fine,C_and_PS_mechanisms=mechanisms,errors=errors,
        problem_objective_classification=problem_records,reporting_input_identities=reporting_inputs,
        source_loss_dispositions=losses,reporting_dispositions=dispositions,
        cross_arm_contradictions=conflicts,input_identities=inputs,empty_route_handoff_read_only_diagnostics=notes,
        original_root_fallback=False,incumbents_bounds_or_certificates_transferred=False)


def exhaustive_service_vectors(case,k):
    """Independent finite service-vector domain; no LP or imported E runner."""
    q=case['Q'][k];choices=[]
    for b in case['b']:
        options=[(0,0,0)]
        options.extend((u,0,1) for u in range(1,min(b,q)+1))
        options.extend((0,u,1) for u in range(1,min(2-b,q)+1))
        choices.append(options)
    def has_order(v,remaining,load):
        if not remaining: return True
        return any(0<=load+v[i][0]-v[i][1]<=q and
            has_order(v,remaining-{i},load+v[i][0]-v[i][1]) for i in remaining)
    result=set()
    for v in itertools.product(*choices):
        P=sum(x[0] for x in v);D=sum(x[1] for x in v)
        if 0<=P-D<=q and 120*P<=case['T'] and has_order(v,{i for i,x in enumerate(v) if x[2]},0):
            result.add(v)
    return result


def row_fraction(terms,sense,rhs):
    senses={'<':'<=','>':'>=','=':'=','<=':'<=','>=':'>='}
    return tuple(sorted((n,F(v)) for n,v in terms.items() if v)),senses[sense],F(rhs)


def validate_reference_matrix(core,d,case,cars,joint,ranks):
    base=core.lp_model(d/'canonical/original.lp');matrix=read(d/'B_ref_exact_matrix.json')
    rows=collections.Counter(row_fraction({n:F.from_float(v) for n,v in t},s,F.from_float(b)) for t,s,b in base['rows'])
    bounds={n:[F.from_float(x) for x in bb] for n,bb in base['bounds'].items()}
    def add(co,sense='=',rhs=0): rows[row_fraction(co,sense,rhs)]+=1
    for k,ps in enumerate(cars):
        mix=[f'mix{k}[{j}]' for j in range(len(ps))]
        bounds.update({name:[F(0),F(1)] for name in mix});add({name:1 for name in mix},rhs=1)
        for i in range(4):
            for t,prefix in enumerate(('p','d','z')):
                co={f'{prefix}_{k}_{i+1}':1}
                co.update({name:-ps[j]['v'][i][t] for j,name in enumerate(mix) if ps[j]['v'][i][t]})
                add(co)
    for i,b in enumerate(case['b']):
        states=[y for y in range(3) if f'state_{i+1}_{y}' in base['types'] and y!=b]
        theta={(k,y):f'theta{k}_{i}_{y}' for k in range(2) for y in states if abs(y-b)<=case['Q'][k]}
        bounds.update({name:[F(0),F(1)] for name in theta.values()})
        for y in states:
            co={theta[k,y]:1 for k in range(2) if (k,y) in theta};co[f'state_{i+1}_{y}']=-1;add(co)
        for k in range(2):
            ys=[y for y in states if (k,y) in theta]
            for prefix,coefficient in (('z',lambda y:1),('p',lambda y:max(b-y,0)),('d',lambda y:max(y-b,0))):
                co={theta[k,y]:coefficient(y) for y in ys if coefficient(y)};co[f'{prefix}_{k}_{i+1}']=-1;add(co)
    for rank in ranks:
        co=collections.Counter()
        for i,sign,q in rank['events']:
            for y in range(3):
                name=f'state_{i+1}_{y}'
                if name in base['types'] and ((sign=='p' and y<=case['b'][i]-q) or (sign=='d' and y>=case['b'][i]+q)):
                    co[name]+=1
        add(co,'<=',rank['RHS'])
    for mask in range(1,16):
        inside={i+1 for i in range(4) if mask&(1<<i)};outside=set(range(5))-inside
        stock=sum(case['b'][i-1] for i in inside)
        for incoming in (True,False):
            co={f'Y_{i}':1 if incoming else -1 for i in inside}
            for k in range(2):
                arcs=itertools.product(outside,inside) if incoming else itertools.product(inside,outside)
                for a,b in arcs: co[f'x_{k}_{a}_{b}']=-case['Q'][k]
            add(co,'<=',stock if incoming else -stock)
    actual_bounds={n:[F(v) for v in bb] for n,bb in matrix['bounds'].items()}
    actual=collections.Counter(row_fraction(r['coefficients'],r['sense'],r['RHS']) for r in matrix['rows'])
    assert actual_bounds==bounds and actual==rows,'full exact binary64 reference differs from canonical + complete car/R98/ranks/IR construction'
    return matrix,dict(canonical_SHA=sha(d/'canonical/original.lp'),reference_exact_matrix_SHA=sha(d/'B_ref_exact_matrix.json'),
        rows=sum(rows.values()),columns=len(bounds),complete_reference_structure_checked=True,
        exact_coefficients_of_loaded_binary64_matrix=True,all_variable_types_relaxed_to_continuous=True)


def validate_rational_support(d,item,matrix,vectors,names):
    assert item['reference_exact_matrix_SHA']==sha(d/'B_ref_exact_matrix.json') and item['enumeration_SHA']==sha(d/'enumeration.json')
    w=item['w'];rhs=max(sum(a*b for a,b in zip(w,v)) for v in vectors)
    assert item['Psi_exact']==rhs
    proof=item['proof']
    if proof['status']!='EXACT_EXTENSION':
        assert proof.get('obstacle') and not proof.get('strict',False)
        return dict(status='NUMERICAL_CANDIDATE_ONLY',obstacle=proof['obstacle'])
    vals={n:F(v) for n,v in proof['values'].items()};assert set(vals)<=set(matrix['bounds'])
    def at(n): return vals.get(n,F(0))
    for n,(lo,hi) in matrix['bounds'].items(): assert F(lo)<=at(n)<=F(hi),('exact witness bound',n)
    for row in matrix['rows']:
        lhs=sum(F(c)*at(n) for n,c in row['coefficients'].items());rr=F(row['RHS'])
        assert lhs==rr if row['sense']=='=' else lhs<=rr if row['sense']=='<' else lhs>=rr,('exact witness row',row['name'])
    lhs=sum(F(c)*at(n) for c,n in zip(w,names));assert F(proof['lhs'])==lhs and proof['RHS']==rhs
    assert proof['strict']==(lhs>rhs)
    assert proof['all_rows_and_bounds_checked']==len(matrix['rows'])+len(matrix['bounds'])
    return dict(status='STRICT_EXACT_FULL_REFERENCE_WITNESS' if lhs>rhs else 'EXACT_EXTENSION_WITHOUT_STRICT_SEPARATION',
        lhs=str(lhs),exact_joint_RHS=rhs,rows_checked=len(matrix['rows']),bounds_checked=len(matrix['bounds']),
        reference_exact_matrix_SHA=sha(d/'B_ref_exact_matrix.json'),enumeration_SHA=sha(d/'enumeration.json'))


def joint_matrix_extension(reference,matrix,vectors,names):
    """Exactly the complete joint columns, above the same reference matrix."""
    expected=collections.Counter(row_fraction(r['coefficients'],r['sense'],r['RHS']) for r in reference['rows'])
    bounds={n:[F(v) for v in bb] for n,bb in reference['bounds'].items()}
    mix=[f'joint_mix[{j}]' for j in range(len(vectors))]
    bounds.update({n:[F(0),F(1)] for n in mix})
    expected[row_fraction({n:1 for n in mix},'=',1)]+=1
    for t,n in enumerate(names):
        co={n:1};co.update({mix[j]:-v[t] for j,v in enumerate(vectors) if v[t]})
        expected[row_fraction(co,'=',0)]+=1
    actual=collections.Counter(row_fraction(r['coefficients'],r['sense'],r['RHS']) for r in matrix['rows'])
    assert {n:[F(v) for v in bb] for n,bb in matrix['bounds'].items()}==bounds and actual==expected
    assert matrix['rows'][:len(reference['rows'])]==reference['rows'],'joint model changed existing ordered reference rows'
    return dict(complete_joint_columns=len(vectors),added_link_rows=25,reference_rows_and_domains_unchanged=True)


def objective_numerics(matrix,receipt,objective,constant):
    """Primal/dual numerical consistency of a saved return, never a solve."""
    assert receipt['model_sense']==1 and receipt['no_extra_Optimize'] and receipt['strict_rational_optimality_not_claimed']
    assert {n:F(v) for n,v in receipt['objective_coefficients'].items()}==objective and F(receipt['objective_constant'])==constant
    assert receipt['Runtime']>=0 and receipt['Work']>=0 and receipt['native_status']!=3
    if receipt['native_status']!=2:
        assert 'objective' not in receipt
        return dict(status='UNKNOWN_NATIVE_RETURN',native_status=receipt['native_status'],strict_rational_optimality=False)
    bounds={n:[F(v) for v in bb] for n,bb in matrix['bounds'].items()}
    values={n:F(v) for n,v in receipt['values'].items()};rc={n:F(v) for n,v in receipt['reduced_costs'].items()}
    pi={int(j):F(v) for j,v in receipt['row_duals_by_index'].items()}
    assert set(values)<=set(bounds) and set(rc)<=set(bounds) and set(pi)<=set(range(len(matrix['rows'])))
    x=lambda n:values.get(n,F(0));stationarity={n:objective.get(n,F(0))-rc.get(n,F(0)) for n in bounds}
    primal=F(0);dual_sign=F(0);complement=F(0);row_dual=F(0)
    for n,(lo,hi) in bounds.items():
        primal=max(primal,lo-x(n),x(n)-hi)
        reduced=rc.get(n,F(0));endpoint=lo if reduced>=0 else hi
        complement=max(complement,abs(reduced*(x(n)-endpoint))/(1+abs(reduced)+abs(x(n))+abs(endpoint)))
    for j,row in enumerate(matrix['rows']):
        co={n:F(v) for n,v in row['coefficients'].items()};rhs=F(row['RHS']);multiplier=pi.get(j,F(0))
        lhs=sum(v*x(n) for n,v in co.items());sense=row['sense'];slack=lhs-rhs
        primal=max(primal,abs(slack) if sense=='=' else slack if sense=='<' else -slack)
        dual_sign=max(dual_sign,multiplier if sense=='<' else -multiplier if sense=='>' else F(0))
        complement=max(complement,abs(multiplier*slack)/(1+abs(multiplier)+abs(lhs)+abs(rhs)))
        for n,v in co.items(): stationarity[n]-=v*multiplier
        row_dual+=multiplier*rhs
    objective_value=constant+sum(c*x(n) for n,c in objective.items())
    station=max(map(abs,stationarity.values()),default=F(0));primal=max(primal,F(0));dual_sign=max(dual_sign,F(0))
    feasible=float(receipt['numeric_policy']['FeasibilityTol']);optimal=float(receipt['numeric_policy']['OptimalityTol'])
    assert float(primal)<=max(1e-7,feasible)*1.01,('saved original-objective primal violation',float(primal))
    assert float(station)<=max(1e-7,optimal)*1.01 and float(dual_sign)<=max(1e-7,optimal)*1.01
    assert float(complement)<=max(1e-7,feasible,optimal)*1.01
    same(float(objective_value),receipt['objective'],1e-7)
    bound_dual=sum(rc.get(n,F(0))*(lo if rc.get(n,F(0))>=0 else hi) for n,(lo,hi) in bounds.items())
    dual_candidate=constant+row_dual+bound_dual
    return dict(status='NUMERICALLY_CONSISTENT_SAVED_LP_RETURN',native_status=2,objective=receipt['objective'],
        all_primal_columns_rows_bounds_checked=True,max_primal_residual=float(primal),max_stationarity_residual=float(station),
        max_dual_sign_residual=float(dual_sign),max_scaled_complementarity_residual=float(complement),
        raw_primal_minus_RC_bound_dual=float(objective_value-dual_candidate),
        dual_candidate_not_promoted_to_an_exact_global_bound=True,native_quality=receipt.get('native_quality'),
        strict_rational_optimality=False)


def joint_evidence(out):
    core=importlib.import_module('round108_reader');result=read(out/'joint_results.json')
    identity=read(out/'joint/identity.json');plan=read(out/'E_experiment_plan.json');asset=read(out/'E3_binding.json')
    assert identity['assets']==asset and identity['all_original_production_sources_checked']
    assert identity['base']==BASE and identity['plan_SHA']==result['plan_SHA']==sha(out/'E_experiment_plan.json')
    assert identity['runner_SHA']==result['runner_SHA']==sha(ROOT/'scripts/round132_joint.py')
    assert result['limited_directions_do_not_prove_full_hull_equality'] and result['no_large_separator_or_production_change']
    assert result['execution']=='COMPLETE_BOUNDED_TINY_STEP','required finite tiny E campaign is not fully closed'
    assert [r['id'] for r in result['cases']]==[c['id'] for c in CASES]
    facts=[]
    for case,saved in zip(CASES,result['cases']):
        d=out/'joint'/case['id'];enum=read(d/'enumeration.json');assert enum['case']==case and enum['complete_universe']
        for name in ('reference_infeasibility_contradiction.json','joint_infeasibility_contradiction.json','control_contradiction.json','objective_contradiction.json'):
            assert not (d/name).exists(),('E contradiction requires investigation',case['id'],name)
        cars=enum['cars'];assert len(cars)==2
        for k,ps in enumerate(cars):
            domain=exhaustive_service_vectors(case,k);actual={tuple(tuple(x) for x in p['v']) for p in ps}
            assert actual==domain and len(actual)==len(ps),'complete one-car projected service domain missing/duplicated'
            for p in ps:
                v=p['v'];active={i for i,x in enumerate(v) if x[2]};order=p['route']
                assert len(order)==len(set(order)) and set(order)==active
                load=0
                for i in order: load+=v[i][0]-v[i][1];assert 0<=load<=case['Q'][k]
                P=sum(x[0] for x in v);D=sum(x[1] for x in v)
                assert (p['pickup'],p['drop'],p['return_load'])==(P,D,P-D) and 120*P<=case['T']
        expected={(a,b) for a,p in enumerate(cars[0]) for b,q in enumerate(cars[1]) if all(p['v'][i][2]+q['v'][i][2]<=1 for i in range(4))}
        actual=[tuple(x) for x in enum['joint_pair_indices']];assert set(actual)==expected and len(actual)==len(expected)
        joint=[(cars[0][a],cars[1][b]) for a,b in actual]
        vectors=[tuple(x for car in pair for station in car['v'] for x in station) for pair in joint]
        pools=[[None]+[(i,'p',q) for q in range(1,b+1)]+[(i,'d',q) for q in range(1,3-b)] for i,b in enumerate(case['b'])]
        events=[tuple(e for e in es if e is not None) for es in itertools.product(*pools) if any(e is not None for e in es)]
        ranks=[]
        for es in events:
            rhs=max(sum(any(car['v'][i][0 if sign=='p' else 1]>=q for car in pair) for i,sign,q in es) for pair in joint)
            ranks.append(dict(events=[list(e) for e in es],RHS=rhs))
        assert read(d/'rank_rows.json')==ranks
        matrix,matrix_fact=validate_reference_matrix(core,d,case,cars,joint,ranks)
        assert saved['canonical_SHA']==matrix_fact['canonical_SHA'] and saved['reference_exact_matrix_SHA']==matrix_fact['reference_exact_matrix_SHA']
        queries=read(d/'support_queries.json');controls=read(d/'event_controls.json')
        chosen=ranks[::max(1,len(ranks)//8)][:8];assert queries['controls']==controls and len(controls)==len(chosen)==8
        for control,rank in zip(controls,chosen):
            assert control['events']==rank['events'] and control['exact_rank']==rank['RHS']
            if control['value'] is None: assert control['qualification']=='UNKNOWN'
            else: assert control['qualification']=='PASS' and control['value']<=rank['RHS']+1e-7
        records=queries['records'];assert [q['direction'] for q in records]==list(range(64))
        names=[f'{prefix}_{k}_{i+1}' for k in range(2) for i in range(4) for prefix in ('p','d','z')]
        normal_vectors={}
        for q in records:
            j=q['direction'];w=[int(hashlib.sha256(f'round132-joint-v2|{case["id"]}|{j}|{t}'.encode()).hexdigest()[:8],16)%5-2 for t in range(24)]
            normal_vectors[j]=w;rhs=max(sum(a*b for a,b in zip(w,v)) for v in vectors)
            if q.get('status')=='UNKNOWN': assert q.get('native_status')!=3;continue
            assert q['w']==w and q['Psi_exact']==rhs
            same(q['gap'],q['reference_support']-rhs,1e-12)
        strict=[]
        if (d/'best_separation.json').is_file():
            best=read(d/'best_separation.json')
            for key in ('best_numeric','best_strict'):
                item=best[key]
                if item is None: continue
                assert item['w']==normal_vectors[item['direction']]
                fact=validate_rational_support(d,item,matrix,vectors,names)
                if key=='best_strict': assert fact['status']=='STRICT_EXACT_FULL_REFERENCE_WITNESS';strict.append(fact)
            equal(saved['best_numeric'],best['best_numeric'],'E best numeric snapshot')
            equal(saved['best_strict'],best['best_strict'],'E best strict snapshot')
        else: assert saved['best_numeric'] is None and saved['best_strict'] is None
        equal(saved,read(d/'case_result.json'),'E case summary')
        assert saved['single_plans']==list(map(len,cars)) and saved['joint_pairs']==len(joint) and saved['IR_rows']==30
        assert saved['threshold_ranks']==len(ranks) and saved['queried_directions']==64
        before,after=saved['full_current_micro_objective_reference'],saved['full_current_micro_objective_joint']
        if before is None or after is None: assert saved['current_objective_increment'] is None
        else: same(saved['current_objective_increment'],after-before,1e-12);assert after>=before-1e-7
        joint_matrix=read(d/'B_joint_exact_matrix.json');assert saved['joint_exact_matrix_SHA']==sha(d/'B_joint_exact_matrix.json')
        extension=joint_matrix_extension(matrix,joint_matrix,vectors,names)
        canonical=core.lp_model(d/'canonical/original.lp')
        obj={n:F.from_float(v) for n,v in canonical['objective'][0]};constant=F.from_float(canonical['objective'][1])
        objectives=[]
        for filename,actual_matrix,value in (('original_objective_reference.json',matrix,before),('original_objective_joint.json',joint_matrix,after)):
            assert saved['original_objective_receipt_SHAs'][filename]==sha(d/filename)
            native=read(d/filename);equal(value,native.get('objective'),('saved original objective',filename))
            objectives.append(dict(receipt=filename,SHA=sha(d/filename),**objective_numerics(actual_matrix,native,obj,constant)))
        facts.append(dict(id=case['id'],single_service_vectors=list(map(len,cars)),joint_pairs=len(joint),threshold_ranks=len(ranks),
            independently_recomputed_exact_support_RHS=64,event_controls=8,strict_witnesses=strict,**matrix_fact,
            original_objective_increment=saved['current_objective_increment'],joint_matrix_extension=extension,
            original_objective_receipts=objectives,original_objective_status='saved native primal/dual numerical consistency; no exact optimum or external solve',
            all_feasible_service_vectors_complete=True,one_physical_order_per_vector_suffices_for_this_projection=True))
    return dict(status='FINITE_TINY_E_CHECKED',cases=facts,execution=result['execution'],real_role_E2_to_E4_admitted=False,
        full_real_role_steps=result['full_real_role_steps'],finite_unseparated_normals_are_not_equivalence=True,
        exact_threshold_ranks_not_identified_with_R101_necessary_resource_ranks=True)


def cost_evidence(out,own_fee=None):
    by={k:0. for k in LIMITS};separate=0.;records=[];active=[]
    for path in sorted((out/'fees').glob('*/launch.json')):
        label=path.parent.name;launch=read(path);rp=path.parent/'receipt.json'
        if not rp.is_file():
            assert label==own_fee and launch['kind'] not in LIMITS
            active.append(dict(label=label,kind=launch['kind'],current_readonly_invocation_only=True));continue
        r=read(rp);outer=r['outer_seconds'];g1=r['G1_seconds'];delivery=r['separately_reported_seconds']
        assert outer>=0 and g1>=0 and delivery>=0 and r['exit_observed'] and r['nested_H_LP_MIP_not_added']
        same(outer,g1+delivery,1e-6)
        segments=list((out/'cost_segments'/label).glob('*.json'))
        disjoint=0.
        for q in segments:
            segment=read(q);assert segment['native_Optimize']==0 and segment['seconds']>=0;disjoint+=segment['seconds']
        assert disjoint<=outer
        if launch['kind'] in LIMITS:
            same(g1,outer-disjoint,1e-6);by[launch['kind']]+=g1
        else: same(g1,0.,0.)
        separate+=delivery
        records.append(dict(label=label,kind=launch['kind'],exit_code=r['exit_code'],outer_seconds=outer,G1_seconds=g1,
            separately_reported_seconds=delivery,disjoint_verification_segments=disjoint,launch_SHA=sha(path),receipt_SHA=sha(rp)))
    assert sum(by.values())<=144000 and all(by[k]<=cap for k,cap in LIMITS.items()),('budget exceeded',by)
    author=read(out/'resource_accounting.json');equal(by,author['by_category'],'G1 category accounting')
    same(sum(by.values()),author['G1_seconds'],1e-6)
    delivery_records=[];current_delivery=[]
    for path in sorted((out/'delivery_costs').glob('*/launch.json')):
        launch=read(path);rp=path.parent/'receipt.json'
        assert launch['kind']=='separate_delivery' and launch['G1'] is False and launch['nested_child_time_not_added']
        if not rp.is_file():
            assert this_readonly_delivery(launch)
            current_delivery.append(dict(label=path.parent.name,current_readonly_invocation_only=True));continue
        r=read(rp);assert r['G1_seconds']==0 and r['exit_observed'] and r['outer_process_counted_once'] and r['no_formal_window_changed']
        same(r['seconds'],r['separately_reported_seconds'],0.)
        assert r['seconds']>=0
        delivery_records.append(dict(label=path.parent.name,**r,launch_SHA=sha(path),receipt_SHA=sha(rp)))
    assert len(current_delivery)<=1
    # Later internal/public verification receipts cannot be retroactively added
    # to an earlier author accounting snapshot. Report both exact snapshots.
    return dict(G1_seconds=sum(by.values()),by_category=by,limits=LIMITS,closed_fees=records,
        closed_separately_reported_seconds=separate,current_readonly_fee_pending=active,
        closed_delivery_processes=delivery_records,current_delivery_process_pending=current_delivery,
        closed_delivery_outer_seconds=sum(r['seconds'] for r in delivery_records),
        closed_separate_measured_total_seconds=separate+sum(r['seconds'] for r in delivery_records),
        author_separately_reported_snapshot=author['separately_reported_seconds'],all_G1_fees_closed=True,
        own_receipt_elapsed_must_be_closed_by_external_delivery_supervisor=True,nested_H_LP_MIP_never_added=True)


def qualification_evidence(out):
    core=importlib.import_module('round108_reader');prior=importlib.import_module('round130_portable_check')
    H=importlib.import_module('compare_round112_startup')
    native=read(out/'qualification/C_native_qualification.json');report=read(out/'qualification/C_matrix_qualification.json')
    wording=read(out/'qualification/C_matrix_wording_addendum.json');build=read(out/'research_build.json')
    assert native['passed'] and report['passed'] and report['LP_calls']==12 and report['H_calls']==0
    assert wording['original_report_SHA']==sha(out/'qualification/C_matrix_qualification.json')
    assert report['research_PE_SHA']==build['PE_SHA'] and report['research_exporter_SHA']==build['exporter_SHA']
    publication=read(out/'research_source_publication.json')
    assert publication['frozen_production_sources_unchanged'] and publication['no_PE_DLL_objects_archive_or_license_published']
    assert {r['stem'] for r in publication['files']}==set(build['generated_sources'])
    for row in publication['files']:
        assert sha(portable(row['published']))==row['SHA']==build['generated_sources'][row['stem']]['SHA']
    assert [r['name'] for r in native['records']]==[f'qualification/C_native_{x}' for x in ('E3','off','geom','sp')]
    models={};hs={};facts=[];raw=[]
    for r in native['records']:
        key=r['name'].rsplit('_',1)[-1];camp=out/r['name'];i=read(camp/'identity.json')
        assert len(i['launches'])==1 and i['candidate_binary_sha256']==(PE if key=='E3' else RESEARCH_PE) and i['dll_sha256']==DLL
        l=i['launches'][0];d=portable(l['destination']);a=read(camp/'reconstructed.json')['arms'][0]
        assert eligible(a);clocks=validate_seal(d,l,i)
        h=H.reconstruct(ROOT,l['panel'],d);assert h['complete'];hs[key]=h
        calls=[q['payload'] for q in read(d/'observations.json') if q['payload']['kind']=='call']
        assert len(calls)==2 and all(c['leaf']=='L0' and c['settings']['Seed']==0 for c in calls)
        path=portable(calls[0]['model_path']);assert sha(path)==r['matrix_SHA']
        m=core.lp_model(path);models[key]=m
        detail=prior.root_chain(core,dict(dest=d,result=read(d/'result.json'),calls=calls,launch=l,arm=a),h)
        facts.append(dict(name=r['name'],matrix_SHA=sha(path),own_H_complete=True,Start_and_root_chain=detail,**clocks))
        raw.append(dict(path=rel(path),SHA=sha(path)))
    assert models['E3']==models['off'] and facts[0]['matrix_SHA']==facts[1]['matrix_SHA']
    assert all(h['fleet']==hs['E3']['fleet'] and h['semantic_traces']==hs['E3']['semantic_traces'] for h in hs.values())
    # Completed exact fixture matrices are uniquely located; failed attempts
    # stay in the release and accounting, but are not silently substituted.
    expected=[(r['id'],'root' if r['interval'][0]==0 else 'positive_lower') for r in report['records']]
    attempts=[p for p in sorted((out/'qualification').glob('C_matrices*')) if p.is_dir() and
        all((p/id/label/expression/'original.lp').is_file() for id,label in expected for expression in ('E3','off','geom','sp'))]
    assert len(attempts)==1,('one completed finite matrix qualification required',list(map(rel,attempts)))
    matrix_facts=[];directory=attempts[0]
    for r,(id,label) in zip(report['records'],expected):
        d=directory/id/label;mm={name:core.lp_model(d/name/'original.lp') for name in ('E3','off','geom','sp')}
        assert mm['E3']==mm['off'] and sha(d/'E3/original.lp')==sha(d/'off/original.lp')
        n=sum(name.startswith('Y_') for name in mm['off']['types'])
        # The fixture target is read from the actual ratio equalities, whose
        # coefficient is exactly -1/D for the integer target. These tiny
        # qualification fixtures have integral targets; reject an ambiguity.
        targets=[0]
        for j in range(1,n+1):
            candidates=[]
            for terms,sense,rhs in mm['off']['rows']:
                co=dict(terms)
                if sense=='=' and rhs==0 and set(co)=={f'r_{j}',f'Y_{j}'} and co[f'r_{j}']==1 and co[f'Y_{j}']<0:
                    target=round(-1/co[f'Y_{j}'])
                    assert -1./target==co[f'Y_{j}'];candidates.append(target)
            assert len(candidates)==1;targets.append(candidates[0])
        geo=geometry_difference(mm['off'],mm['geom'],n,r['interval'][1],targets)
        sp=projection_difference(mm['off'],mm['sp'])
        solved=r['canonical_all_continuous_LP'];assert set(solved)=={'off','geom','sp'}
        assert max(q['value'] for q in solved.values())-min(q['value'] for q in solved.values())<1e-7
        for name,q in solved.items():
            assert q['rows']==len(mm[name]['rows']) and q['columns']==len(mm[name]['order']) and q['Runtime']>=0 and q['Work']>=0
        matrix_facts.append(dict(id=id,interval=r['interval'],geometry=geo,projection=sp,
            default_off_E3_same_bytes=True,actual_paths_and_SHAs=[dict(path=rel(d/x/'original.lp'),SHA=sha(d/x/'original.lp')) for x in mm],
            reported_continuous_LP_values_numerically_consistent=True,continuous_LP_not_resolved_here=True))
    return dict(default_off_original_E3_byte_and_behavioral_bridge=True,native_qualification=facts,
        matrix_qualification=matrix_facts,completed_attempt=rel(directory),all12_prior_qualification_LP_calls_retained=True,
        numerical_consistency_not_universal_rational_equivalence=True,failed_attempts_not_erased=True)


def mechanism_costs(out,rows,formal_facts):
    core=importlib.import_module('round108_reader')
    author={(r['line'],r['id'],int(r['seed']),r['method']):r for r in csv_rows(out/'mechanism_costs.csv')}
    evidence={(r['line'],r['id'],r['seed'],r['method']):r for r in formal_facts['arm_evidence']}
    facts=[]
    def cell(row,k):
        s=row.get(k,'')
        if s=='': return None
        if s in ('True','False'): return s=='True'
        if s.startswith(('[','{')): return json.loads(s)
        try: return float(s)
        except ValueError: return s
    for line,g,plan in rows:
        for l in plan['launches']:
            method=l.get('comparison_method',l['method']);key=(line,l['id'],l['seed'],method);saved=author[key]
            d=portable(l['destination']);r=read(d/'result.json');ledger_path=d/'external/paper_optimize_ledger.csv'
            ledger=core.rows(ledger_path) if ledger_path.is_file() else [];lp=[q for q in ledger if q['solve_kind']=='LP'];mip=[q for q in ledger if q['solve_kind']!='LP']
            optimize=int(float(saved['native_Optimize']))
            if ledger: assert len(ledger)==optimize
            def summed(field,qq):
                if not qq: return 0. if optimize==0 else None
                try: return sum(float(q[field]) for q in qq)
                except (KeyError,ValueError): return None
            native_lp=core.rows(d/'external/lp_status_ledger.csv') if (d/'external/lp_status_ledger.csv').is_file() else []
            initial=next((q for q in native_lp if q['leaf_id']=='L0'),None)
            starts=[read(p) for p in (d/'external/native_logs').glob('*.round68.start.json')]
            if (d/'native.log.round112.start.json').is_file(): starts.append(read(d/'native.log.round112.start.json'))
            calc=dict(LP_calls=len(lp),MIP_calls=len(mip) if ledger else optimize,child_LP_calls=sum(q['leaf_id']!='L0' for q in lp),
                target_MIP_calls=sum(q['solve_kind']!='MIP' for q in mip),
                canonical_continuous_LP_bound=float(initial['lower_bound']) if initial and initial['bound_available']=='1' else None,
                LP_native_seconds=summed('solver_runtime',lp),MIP_native_seconds=summed('solver_runtime',mip) if ledger else r.get('gurobi_runtime'),
                LP_Work=summed('work',lp),MIP_Work=summed('work',mip) if ledger else r.get('gurobi_work'),
                nodes=summed('nodes',ledger) if ledger else r.get('gurobi_node_count'),
                native_simplex_iterations=summed('simplex_iterations',ledger) if ledger else None,
                native_barrier_iterations=summed('barrier_iterations',ledger) if ledger else None,
                model_build_seconds=r.get('external_gini_tree_model_build_seconds') if ledger else r.get('gurobi_model_build_seconds'),
                model_read_seconds=r.get('external_gini_tree_model_read_seconds') if ledger else r.get('gurobi_model_read_seconds'),
                split_count=r.get('external_gini_tree_split_count') if ledger else None,
                actual_submitted_Starts=sum(bool(q.get('submitted')) for q in starts),Start_receipts=len(starts),
                Start_mapping_seconds=sum(q['mapping_validation_submission_seconds'] for q in starts) if starts and all('mapping_validation_submission_seconds' in q for q in starts) else None,
                H_plus_admission_seconds=0. if method=='P' else r.get('process_elapsed_at_exact_phase_start_seconds') if optimize else None)
            calc.update(evidence[key]['root_attributes'])
            calc.update({k:evidence[key][k] for k in ('T_produce','T_verify','T_total')})
            for k,v in calc.items(): equal(v,cell(saved,k),('mechanism costs',key,k))
            for field,key_name in (('status','Start_statuses'),('exact_vector_observed_in_mipsol','Start_exact_vectors_observed'),('integer_vector_observed_in_mipsol','Start_integer_vectors_observed')):
                expected=collections.Counter(json.dumps(q.get(field,'unknown') if field=='status' else q.get(field)) for q in starts)
                actual=collections.Counter(json.dumps(x) for x in cell(saved,key_name));assert actual==expected
            facts.append(dict(line=line,id=l['id'],seed=l['seed'],method=method,**calc,
                native_components_not_added_to_own_or_G1_time=True,missing_native_fields_preserved_as_null=True))
    assert len(facts)==len(author)==84
    return facts


def progress_and_history(out,rows,core):
    index=read(out/'native_progress_index.json');assert index['no_historical_gurobi_work_traversal']
    indexed={r['result']:r for r in index['records']};assert len(indexed)==len(index['records'])
    trajectory=read(out/'trajectory_index.json')['arms'];trajectory_by={(x['line'],x['id'],x['seed'],x['method']):x for x in trajectory}
    checked=[];wanted=set();carrier_indexes={}
    archive_manifest=out/'raw_archive_manifest.json'
    if archive_manifest.is_file():
        for archive in read(archive_manifest)['archives']:
            idx=archive['member_index'];path=portable(idx['path']);assert sha(path)==idx['SHA256']
            blob=gzip.decompress(path.read_bytes());assert len(blob)==idx['decoded_bytes'] and hashlib.sha256(blob).hexdigest()==idx['decoded_SHA256']
            members=json.loads(blob);assert len(members)==len({m['path'] for m in members})==archive['file_count']
            carrier_indexes[archive['name']]={m['path']:m for m in members}
    for line,g,plan in rows:
        for l in plan['launches']:
            d=portable(l['destination']);r=read(d/'result.json');name=r.get('gurobi_progress_path')
            if not name: continue
            p=portable(name);assert p.is_relative_to(ROOT/'results/gurobi_work') and p.is_file()
            key=rel(d/'result.json');wanted.add(key);record=indexed[key]
            assert record['path']==rel(p) and record['exists'] and record['bytes']==p.stat().st_size and record['SHA']==sha(p)
            assert record['id']==l['id'] and record['seed']==l['seed'] and record['method']==l.get('comparison_method',l['method'])
            sources=trajectory_by[line,l['id'],l['seed'],record['method']]['sources']
            source=next(x for x in sources if x['path']==rel(p));assert source['bytes']==p.stat().st_size and source['SHA']==sha(p)
            carrier=None
            if carrier_indexes:
                carrier=g['name'].replace('/','_')+'.zip';member=carrier_indexes[carrier][rel(p)]
                assert member['SHA256']==sha(p) and member['bytes']==p.stat().st_size
            checked.append(dict(result=key,path=rel(p),bytes=p.stat().st_size,SHA=sha(p),corresponding_current_carrier=carrier))
    assert set(indexed)==wanted,'native progress index includes unrequested old work or misses actual current paths'
    historical=read(out/'historical_physical_outcomes.json');assert historical['exact_small_dependency_only'] and historical['no_historical_raw_carrier_restored']
    path=ROOT/'results/unified_exact_round131/review/final_independent_evidence.json'
    reference=read(path);assert reference['status']=='PASS'
    panels=read(ROOT/'results/unified_exact_round131/input_manifest.json')['roles']
    aa=read(ROOT/'results/unified_exact_round131/observations.json')['arms'];facts=[]
    assert [r['id'] for r in historical['rows']]==['SC-C15-B','PB-C35-U']
    for row in historical['rows']:
        id=row['id'];p=next(x for x in panels if x['id']==id)
        saved=next(x for x in reference['arm_evidence'] if (x['id'],x['seed'],x['repeat'],x['method'])==(id,0,1,'S2'))
        arm=next(x for x in aa if (x['id'],x['seed'],x['repeat'],x['method'])==(id,0,1,'S2'))
        assert saved['qualified'] and arm['PE_SHA']==PE and arm['DLL_SHA']==DLL and arm['input_SHA']==p['input_sha256']
        fleet=core.full_fleet(ROOT,p,saved['final_complete_fleet']);same(fleet['F'],arm['U'],1e-7)
        assert row['line']=='R131 historical final S2' and row['new_performance_observation'] is False
        assert row['inherited_source_SHA']==sha(path) and row['inherited_from']==rel(path)
        equal(fleet_resources(core,p,fleet),row,('historical physical',id))
        facts.append(dict(id=id,version='R131',method='S2',seed=0,new_performance_observation=False,
            source_SHA=sha(path),input_SHA=p['input_sha256'],physically_replayed=True))
    return dict(actual_current_native_progress=checked,historical_fleets=facts,old_gurobi_work_enumerated=False,
        old_raw_carriers_required_or_read=False)


def compare_problem_classification(out,expected):
    saved=read(out/'problem_objective_classification.json')
    for flag in ('unknown_is_not_positive','near_zero_positive_is_not_zero',
        'no_arm_U_L_T_cert_or_certificate_changed','no_information_supplied_to_production'):
        assert saved[flag] is True,('problem classification scope flag',flag)
    records={(r['line'],r['input_SHA']):r for r in saved['records']}
    assert len(records)==len(saved['records'])==len(expected)
    assert set(records)=={(r['line'],r['input_SHA']) for r in expected}
    witnesses_checked=0
    def witness_key(w):
        return w['id'],w['seed'],w['method'],w['producer_receipt_SHA']
    for record in expected:
        actual=records[record['line'],record['input_SHA']]
        assert actual['problem_objective_class']==record['problem_objective_class']
        assert actual['ids']==record['ids']
        ww={witness_key(w):w for w in actual['evidence']}
        assert len(ww)==len(actual['evidence'])==len(record['evidence'])
        assert set(ww)=={witness_key(w) for w in record['evidence']}
        for witness in record['evidence']:
            reported=ww[witness_key(witness)]
            assert set(reported)==set(WITNESS_FIELDS)
            equal(witness,reported,('problem class evidence',record['line'],record['input_SHA'],witness_key(witness)))
            if record['problem_objective_class']=='zero_proved_by_qualified_physical_zero':
                assert reported['G_true']==reported['P_true']==0, 'near-zero positive is not a physical zero'
            else:
                assert record['problem_objective_class']=='positive_under_qualified_lower_bound' and reported['L']>1e-7
            witnesses_checked+=1
        if record['problem_objective_class']=='unknown_optimum_class': assert not actual['evidence']
    return dict(problem_records=len(records),qualified_classification_witnesses_checked=witnesses_checked,
        physical_zero_distinguished_from_near_zero_positive=True,unknown_not_relabelled_positive=True,
        own_U_L_certificates_and_clocks_not_transferred_or_changed=True)


def compare_timing_exposure(out,arms):
    rows=csv_rows(out/'timing_environment_exposure.csv')
    by={(r['line'],r['id'],int(r['seed']),r['method']):r for r in rows}
    assert len(rows)==len(by)==len(arms)==84
    assert set(by)=={(a['line'],a['id'],a['seed'],a['method']) for a in arms}
    fields={'line','id','seed','method','group','producer_receipt_SHA',*LIFETIME_FIELDS}
    for a in arms:
        key=(a['line'],a['id'],a['seed'],a['method']);r=by[key]
        assert set(r)==fields and int(r['group'])==a['group']
        assert r['producer_receipt_SHA']==a['producer_receipt_SHA']
        for name in LIFETIME_FIELDS[:2]: same(float(r[name]),a[name],0.)
        assert r['stage_waiter_lifetime_overlap'] in ('True','False')
        assert (r['stage_waiter_lifetime_overlap']=='True') is a['stage_waiter_lifetime_overlap']
        assert r['timing_environment_scope']==a['timing_environment_scope']
        assert r['counterfactual_clean_machine_T_cert']=='', 'counterfactual time must remain null'
    return dict(own_producer_intervals_independently_recomputed=84,exposure_CSV_rows_checked=84,
        lifetime_overlap_not_parsing_CPU_contention_or_slowdown=True,no_overlap_not_quiescence=True,
        clean_machine_counterfactuals_invented=False)


def compare_source_loss_dispositions(out,facts,author,bound_inputs):
    saved=read(out/'source_loss_dispositions.json')
    assert saved['raw_reconstructed_files_unchanged'] is True and saved['no_Optimize'] is True
    key=lambda a:(a['line'],a['id'],a['seed'],a['method'])
    actual={key(r):r for r in saved['records']}
    expected={key(r):r for r in facts['source_loss_dispositions']}
    assert len(actual)==len(saved['records']) and set(actual)==set(expected)
    for k,record in expected.items():
        equal(record,actual[k],('independently supported source-loss disposition',k))
        for binding in record['sources']:
            assert bound_inputs.get(binding['path'])==binding['SHA'],('missing own source-loss input binding',k,binding['path'])
    ss=facts['reporting_dispositions']
    assert author['performance_qualified_observations']==ss['performance_qualified_observations']
    assert author['disclosed_source_loss_observations']==ss['disclosed_source_loss_observations']
    assert author['raw_reconstructed_files_unchanged'] is True
    assert not author['missing'] and not author['analysis_issues']
    assert len(facts['physical_rows'])==len(facts['arm_evidence'])==84
    return dict(disclosed_own_zero_source_losses_checked=len(expected),
        performance_qualified_observations=ss['performance_qualified_observations'],
        performance_unevaluable_comparisons=ss['performance_unevaluable_comparisons'],
        raw_own_zero_and_original_clocks_preserved=True,formal_T_cert_and_censoring_null_for_source_loss=True,
        all_required_positions_and_all84_physical_cost_timing_trajectory_rows_required=True,
        native_source_reliability_unresolved=bool(expected),performance_eligibility_not_relaxed=True)


def author_comparison(out,facts):
    author=read(out/'observations.json');assert author['execution']=='ALL_C_D_ARMS_SEALED'
    aa={(a['line'],a['id'],a['seed'],a['method']):a for a in author['arms']}
    pp={(p['line'],p['group'],p['left'],p['right']):p for p in author['pairs']}
    assert len(aa)==84 and len(pp)==64
    for arm in facts['arms']:
        saved=aa[arm['line'],arm['id'],arm['seed'],arm['method']]
        for key in ('U','L','gap','signed_gap','T_produce','T_verify','T_total','T_cert','certificate',
            'formal_protocol_qualified','numbers_qualified','certificate_qualified','PE_SHA','DLL_SHA','input_SHA',
            'source_reduced','native_proof_qualified','own_exact_zero','certificate_source','proof_evidence',
            'raw_reconstructed_T_cert','raw_reconstructed_certificate','formal_performance_evidence_eligible',
            'performance_qualification_disposition','censored',
            'objective_class','problem_objective_class','near_zero_positive_U','G_true','P_true','native_Optimize',
            'producer_receipt_SHA',*LIFETIME_FIELDS):
            equal(arm.get(key),saved.get(key),('author arm',arm['line'],arm['id'],arm['seed'],arm['method'],key))
        if arm['objective_class']=='zero':
            assert saved['G_true']==saved['P_true']==0
    for pair in facts['pairs']:
        equal(pair,pp[pair['line'],pair['group'],pair['left'],pair['right']],('author pair',pair['line'],pair['group']))
    summary=read(out/'stratified_summary.json')
    equal(facts['strata'],summary['strata'],'broad denominators')
    equal(facts['problem_size_objective_strata'],summary['problem_size_objective_strata'],'problem/size/endpoint denominators')
    assert summary['D_arms']==60 and summary['C_arms']==24 and summary['seed_repeats_not_independent'] and summary['full_raw_signed_gaps_preserved']
    physical={ (r['line'],r['id'],int(r['seed']),r['method']):r for r in csv_rows(out/'physical_outcomes.csv') }
    assert len(physical)==len(facts['physical_rows'])
    for row in facts['physical_rows']:
        source=physical[row['line'],row['id'],row['seed'],row['method']]
        for k,v in row.items():
            if k in ('line','id','method'): assert source[k]==v
            elif isinstance(v,(list,dict)): equal(v,json.loads(source[k]),('physical resource',k))
            else: equal(v,float(source[k]),('physical scalar',k))
    index=read(out/'analysis_inputs.json');assert index['immutable_group_arm_input_Seed_and_destination_identity_checked'] and not index['issues']
    bound_inputs={}
    for record in index['inputs']:
        path=portable(record['path']);assert sha(path)==record['SHA']
        name=rel(path)
        assert name not in bound_inputs or bound_inputs[name]==record['SHA']
        bound_inputs[name]=record['SHA']
    assert len(facts['reporting_input_identities'])==85
    assert len({r['path'] for r in facts['reporting_input_identities']})==85
    for record in facts['reporting_input_identities']:
        assert bound_inputs.get(record['path'])==record['SHA'],('missing amendment/producer binding',record['path'])
    assert index['runner_SHA']==sha(ROOT/'scripts/round132_analysis.py')
    losses=compare_source_loss_dispositions(out,facts,author,bound_inputs)
    problem=compare_problem_classification(out,facts['problem_objective_classification'])
    timing=compare_timing_exposure(out,facts['arms'])
    return dict(arms=84,typed_pairs=64,strata_and_all_conditioned_intersections_match=True,
        resource_rows=len(physical),signed_gaps_not_clipped=True,open_time_not_imputed=True,
        problem_classification=problem,timing_exposure=timing,producer_and_amendment_input_SHA_bindings_checked=85,
        source_loss_reporting=losses,
        author_analysis_not_imported_or_executed=True)


def csv_rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))


def check(root,preflight=False,own_fee=None):
    global ROOT
    ROOT=Path(root).resolve();HASHES.clear();out=ROOT/OUT_REL
    assert ROOT.is_dir() and (ROOT/'scripts/round132_portable_check.py').is_file()
    assert Path(__file__).resolve()==ROOT/'scripts/round132_portable_check.py','execute the checker in the supplied root, never another checkout'
    rows,contract=frozen_contract(out)
    reporting_sources=[dict(path=rel(p),SHA=sha(p)) for p in (
        ROOT/'scripts/round132_analysis.py',out/'timing_environment_amendment.json',out/'review/final_reporting_addendum.md')]
    identity=dict(checker_SHA=sha(Path(__file__)),accepted_bindings=PINNED,
        reporting_predecessor=REPORTING_PREDECESSOR,source_loss_predecessor=SOURCE_LOSS_PREDECESSOR,
        reporting_coverage_source_identities=reporting_sources,
        small_plan_input_hashes=[dict(path=rel(p),SHA=h) for p,h in HASHES.items()],**contract)
    if preflight:
        return dict(status='ACCEPT',review_stage='small_plan_preflight_only',**identity,
            reporting_logic_selfcheck=reporting_logic_preflight(),
            source_loss_logic_selfcheck=source_loss_logic_preflight(),
            readonly_flags_selfcheck=readonly_flags_preflight(),
            disabled_ffi_selfcheck=disabled_ffi_preflight(),
            evidence_reader_modules_imported=False,models_fleets_H_or_native_logs_read=False,
            Optimize=0,native_starts=0,compilation=0,final_result_acceptance=False),0
    missing=readiness(out,rows,own_fee=own_fee)
    if missing:
        return dict(status='NOT_READY',reason='all60D+24C closeouts, closed G1 fees and final derived sources are required before raw reading',
            missing=missing,**identity,evidence_reader_modules_imported=False,models_fleets_H_or_native_logs_read=False,
            Optimize=0,native_starts=0,compilation=0,final_result_acceptance=False),2
    sequence=read(out/'sequence_completion.json')
    assert sequence['D_arms']==60 and sequence['C_arms']==24 and not sequence['budget']['unclosed']
    with readonly_boundary():
        facts=formal_evidence(out,rows)
        if facts['errors'] or facts['cross_arm_contradictions']:
            return dict(status='REVIEW_BLOCKED_INVALID_OR_CONTRADICTORY_EVIDENCE',**identity,**facts,
                Optimize=0,native_starts=0,compilation=0,no_performance_retry_authorized=True),1
        if facts['reporting_dispositions']['unresolved_unqualified_observations'] or facts['reporting_dispositions']['unresolved_unevaluable_comparisons']:
            return dict(status='REVIEW_BLOCKED_UNQUALIFIED_FORMAL_OBSERVATIONS',**identity,**facts,
                Optimize=0,native_starts=0,compilation=0,scientific_algorithm_rejection=False,no_performance_retry_authorized=True),1
        author=author_comparison(out,facts)
        qualification=qualification_evidence(out);mechanism=mechanism_costs(out,rows,facts)
        joint=joint_evidence(out);costs=cost_evidence(out,own_fee=own_fee)
        progress=progress_and_history(out,rows,importlib.import_module('round108_reader'))
    return dict(status='PASS',**identity,**facts,author_output_comparison=author,C_qualification=qualification,
        mechanism_costs=mechanism,E=joint,cost_accounting=costs,
        trajectories_and_scoped_history=progress,all_final_complete_fleets_physically_replayed=True,
        full_source_return_Start_cover_reader_reused=True,finite_evidence_review_not_external_replication=True,
        PASS_scope='Faithful finite evidence/reporting, including disclosed UNEVALUABLE own-zero source losses; rejected native proof reliability is not restored.',
        all_required_formal_positions_closed=True,
        serialized_numerical_equivalence_not_claimed=True,Optimize=0,native_starts=0,compilation=0),0


def write_receipt(path,result):
    path=Path(path).resolve();assert path.is_relative_to(ROOT),'receipt must be inside the supplied review/recovery root'
    assert 'raw' not in path.relative_to(ROOT).parts and path.suffix=='.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        j=1
        while path.with_name(path.stem+f'.prior{j:02d}'+path.suffix).exists(): j+=1
        old=path.with_name(path.stem+f'.prior{j:02d}'+path.suffix);old.write_bytes(path.read_bytes())
        result['previous_receipt_retained']=rel(old)
    result['UTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--preflight',action='store_true')
    parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--own-fee',help='exact current delivery-only fee label; never waives an open G1 fee')
    args=parser.parse_args();start=time.perf_counter()
    try: result,code=check(args.root,preflight=args.preflight,own_fee=args.own_fee)
    except Exception as error:
        result,code=dict(status='FAILED_REVIEW_PRESERVE_EVIDENCE',error=repr(error),traceback=traceback.format_exc(),
            Optimize=0,native_starts=0,compilation=0,no_performance_retry_authorized=True),1
    result['seconds']=time.perf_counter()-start;write_receipt(args.receipt,result)
    print(json.dumps({k:result[k] for k in ('status','Optimize','seconds')},ensure_ascii=False))
    return code


if __name__=='__main__':
    raise SystemExit(main())
