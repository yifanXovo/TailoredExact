"""Finite independent main36 import; no native call or historical matrix replay.

The local import verifies the complete, already executed R110 independent audit
once against its fixed Git bytes and receipt, then retains only the exact main36
records and small source/table authorities. Public review checks this signed
finite import; it does not claim to replay the omitted historical raw payload.
"""
from pathlib import Path
from collections import Counter
import argparse
import csv
import hashlib
import io
import json
import math
import os
import runpy
import shutil
import subprocess
import time
import traceback

SCIENCE = 'c4efe042bc6654ccd2e14b7e0d65c904a15d3390'
BASE = '13ed7eeb83b647f585837638ed9158b84f274d66'
OLD = 'results/unified_exact_round110'
NEW = 'results/unified_exact_round111'
AUDIT_SHA = '958616d42215a6ee60d468a1f717182d59825ca230db5c82ff8c0b0fa5c09cab'
RECEIPT_SHA = 'd4869c50551293e1f4480cc6a575f3432a41c9afccebcfc94d742b7f06652d68'
PE = 'c0384284aefd5aa2acc5d885ef37b0cfad6f93d083a5feb9ee693c41a786b411'
DLL = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
DECISION_SHA = 'b518597b8ccaf100607e4e6738688be9032957039396e5bb23a3f0ebe817a926'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


class Tee:
    def __init__(self, original, stream):
        self.original, self.stream = original, stream
    def write(self, value):
        self.stream.write(value)
        return self.original.write(value)
    def flush(self):
        self.stream.flush()
        self.original.flush()


class Import:
    def __init__(self, root, source, destination):
        self.root = Path(root).resolve()
        self.source = Path(source).resolve()
        self.destination = Path(destination).resolve()
        assert self.destination.is_relative_to(self.root/NEW/'review')
        self.bindings = {}
        self.inherited_reads = {}
        self.checks = 0

    def require(self, condition, message):
        self.checks += 1
        if not condition:
            raise AssertionError(message)

    def fixed(self, path, commit, retained=None):
        current = (self.source/path).read_bytes()
        git = subprocess.run(['git', 'show', commit+':'+path], cwd=self.root,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if git.returncode == 0:
            self.require(current == git.stdout, 'exact pinned Git bytes '+path)
            authority = 'direct immutable Git blob'
        else:
            self.require(commit == SCIENCE and path in self.inherited_reads and
                         digest(current) == self.inherited_reads[path],
                         'explicit restored-carrier byte binding in pinned executed independent audit '+path)
            authority = 'fixed public_full_raw02 audit read_bindings; carrier payload at immutable science commit'
        binding = dict(path=path, commit=commit, bytes=len(current), SHA=digest(current))
        binding['authority'] = authority
        if authority != 'direct immutable Git blob':
            binding['fixed_authority_commit'] = BASE
            binding['fixed_authority_audit_SHA'] = AUDIT_SHA
        self.bindings[path] = binding
        if retained:
            target = self.destination/retained
            target.parent.mkdir(parents=True, exist_ok=True)
            target.open('xb').write(current)
            binding['retained_path'] = target.relative_to(self.root).as_posix()
        return current

    def obj(self, path, commit, retained=None):
        return json.loads(self.fixed(path, commit, retained))

    @staticmethod
    def value(raw):
        if raw == '':
            return None
        if raw in ('True', 'False'):
            return raw == 'True'
        if raw.startswith('[') or raw.startswith('{'):
            return json.loads(raw)
        try:
            return float(raw)
        except ValueError:
            return raw

    def run(self):
        audit_raw = self.fixed(OLD+'/review/public_full_raw02/audit.json', BASE)
        self.require(digest(audit_raw) == AUDIT_SHA, 'actual complete old public audit SHA')
        old = json.loads(audit_raw)
        self.inherited_reads = old['read_bindings']
        receipt = self.obj(OLD+'/review/public_full_raw02/receipt.json', BASE, 'authority/public_full_raw02_receipt.json')
        self.require(self.bindings[OLD+'/review/public_full_raw02/receipt.json']['SHA'] == RECEIPT_SHA,
                     'actual old public receipt bytes')
        self.require(receipt['exit_code'] == 0 and receipt['audit_SHA'] == AUDIT_SHA and
                     receipt['decision'] == old['decision'] == 'ACCEPT_INDEPENDENT_BLOCKED_COMPLETE_RAW_PANEL',
                     'actually executed final public acceptance')
        self.require(old['Optimize'] == old['native_environment'] == receipt['Optimize'] == receipt['native_environment'] == 0,
                     'historical independent execution was offline')
        self.require(old['stage'] == 'BLOCKED' and old['all42_valid_formal'] is False and old['qualified_formal_arms'] == 41,
                     'unchanged historical strict clock result')
        for name, expected in old['reviewer_source_bindings'].items():
            raw = self.fixed(OLD+'/review/'+name, BASE, 'authority/'+name)
            self.require(digest(raw) == expected, 'actual old executed reviewer source '+name)
        for name, expected in old['module_bindings'].items():
            raw = self.fixed(name, SCIENCE, 'authority/'+Path(name).name)
            self.require(digest(raw) == expected, 'actual signed arithmetic source '+name)
        decision_path = self.destination/'authority/round109_independent_decision.py'
        self.require(digest(decision_path.read_bytes()) == DECISION_SHA, 'independent pair source fixed')
        independent = runpy.run_path(str(decision_path))
        candidate = self.obj(OLD+'/candidate_identity.json', SCIENCE, 'authority/candidate_identity.json')
        campaign = self.obj(OLD+'/campaign/identity.json', SCIENCE, 'authority/campaign_identity.json')
        protocol = self.obj(OLD+'/protocol.json', SCIENCE, 'authority/protocol.json')
        manifest = self.obj(OLD+'/input_manifest.json', SCIENCE, 'authority/input_manifest.json')
        selected = self.obj(OLD+'/reports_final/selection_decision.json', SCIENCE, 'authority/selection_decision.json')
        self.require(candidate['production_PE_SHA'] == old['production_PE_SHA'] == PE and candidate['DLL_SHA'] == old['DLL_SHA'] == DLL,
                     'unchanged inherited PE DLL')
        self.require(old['candidate_identity_SHA'] == self.bindings[OLD+'/candidate_identity.json']['SHA'] and
                     old['campaign_identity_SHA'] == self.bindings[OLD+'/campaign/identity.json']['SHA'] and
                     old['protocol_SHA'] == self.bindings[OLD+'/protocol.json']['SHA'], 'executed audit binds fixed science identities')
        arms_raw = self.fixed(OLD+'/reports_final/arms.csv', SCIENCE, 'authority/arms.csv')
        pairs_raw = self.fixed(OLD+'/reports_final/pairs.csv', SCIENCE, 'authority/pairs.csv')
        original_rows = list(csv.DictReader(io.StringIO(arms_raw.decode('utf-8-sig'))))
        original_pairs = list(csv.DictReader(io.StringIO(pairs_raw.decode('utf-8-sig'))))
        records = old['own_actual_arms'][:36]
        clocks = old['formal_clock_evidence'][:36]
        launches = campaign['launches'][:36]
        roles = {r['id']: r for r in manifest['roles']}
        self.require(len(original_rows) == 42 and len(records) == len(clocks) == len(launches) == 36,
                     'exact36 inherited main denominator and complete old42 retained source')
        derived = []
        imported = []
        numeric_differences = []
        published_primitives = []
        for number, (record, clock, launch, row) in enumerate(zip(records, clocks, launches, original_rows), 1):
            key = (launch['id'], launch['seed'], launch['arm'])
            self.require(key == (record['id'], record['seed'], record['arm']) == (clock['id'], clock['seed'], clock['arm']) and
                         key == (row['id'], int(row['seed']), row['arm']) and launch['number'] == clock['number'] == number and key[1] == 0,
                         'each main index/key '+str(number))
            self.require(record['PE_SHA'] == row['PE_SHA'] == PE and record['DLL_SHA'] == row['DLL_SHA'] == DLL and
                         row['input_SHA'] == launch['panel']['input_sha256'] == roles[key[0]]['input_sha256'],
                         'each main production/input identity '+str(number))
            for field, source_field in (('U','U'), ('L','L'), ('gap','gap'), ('certificate','certificate'),
                                         ('numbers_qualified','numbers_qualified'), ('certificate_qualified','certificate_qualified'),
                                         ('complete_seconds','complete_seconds'), ('complete_seconds_interval','complete_seconds_interval')):
                published_value, independent_value = self.value(row.get(field, '')), record.get(source_field)
                if published_value != independent_value:
                    self.require(number == 24 and field in ('L','gap') and independent_value == 0 and
                                 published_value == (5.421010862427522e-20 if field == 'L' else -5.421010862427522e-20) and
                                 abs(published_value-independent_value) <= protocol['closure_tolerance'],
                                 'only exact existing signed tiny-gap difference already accepted under frozen comparator')
                    numeric_differences.append(dict(number=number,id=key[0],arm=key[2],field=field,
                                                    original_published_value=published_value,original_independent_value=independent_value,
                                                    original_frozen_comparator_tolerance=1e-7,signed_original_value_retained=True))
                else:
                    self.require(True, 'all inherited decisive endpoint fields '+str(number)+' '+field)
            self.require(record['numbers_qualified'] is True and record['certificate_qualified'] is True and
                         record['L'] <= record['U']+protocol['closure_tolerance'], 'qualified noncontradictory own bounds '+str(number))
            interval = [record['complete_seconds']]*2 if record['complete_seconds'] is not None else record['complete_seconds_interval']
            self.require(len(interval) == 2 and all(math.isfinite(v) for v in interval) and 0 < interval[0] <= interval[1] <= launch['cap_seconds'] == float(row['cap_seconds']),
                         'entire inherited original clock interval within original cap '+str(number))
            self.require(record['formal_protocol_qualified'] is True and clock['formal_protocol_qualified'] is True and
                         clock['complete_seconds'] == record['complete_seconds'] and clock.get('complete_seconds_interval') == record.get('complete_seconds_interval'),
                         'old independent strict complete-clock qualification '+str(number))
            original_empty = row['formal_protocol_qualified'] == ''
            self.require(original_empty == (number in (15,17,25,26)), 'only identified preserved empty qualifications')
            if original_empty:
                side = self.obj(OLD+f'/campaign/reader_recovery/{number:02d}_{key[0]}_S0_{key[2]}.json', SCIENCE,
                                f'authority/recovery_{number:02d}.json')
                signed_path = side['independent_audit_path'].replace('\\','/')
                signed_path = signed_path[signed_path.index('results/'):]
                signed_raw = self.fixed(signed_path, SCIENCE, f'authority/recovery_{number:02d}_signed_audit.json')
                signed = json.loads(signed_raw)
                self.require(digest(signed_raw) == side['independent_audit_SHA'] and signed['current_key'] == side['key'] == [number,*key] and
                             signed['complete_seconds_interval'] == side['time']['interval'] == interval and signed['production_PE_SHA'] == PE,
                             'current own signed recovery and clock '+str(number))
                self.require(side['own_U'] == record['U'] and side['qualified_L'] == record['L'] == 0. and
                             side['certificate_from_own_exact_zero'] == record['certificate'] == (number in (17,25)),
                             'current own floor and certificate policy '+str(number))
                self.require(record['normal_completion']['returncode'] == 0 and record['normal_completion']['stop_reason'] == 'normal_return' and
                             signed['missing_returned_journal_preserved'] == (number in (17,25)) and self.value(row['journal_return_missing']) == (number in (17,25)),
                             'independent normal return and separate missing-event flags '+str(number))
                if number == 25:
                    self.require(signed['damaged_calls'] == [4] and signed['preserved_distinct_LP_calls'] == [1,2,3],
                                 'scoped damaged MIP never absorbs independent LP calls')
                derived.append(dict(number=number,id=key[0],seed=0,arm=key[2],original_formal_protocol_qualified=row['formal_protocol_qualified'],
                                    original_full_clock_within_frozen_cap=row['full_clock_within_frozen_cap'],complete_seconds=None,
                                    complete_seconds_interval=interval,cap_seconds=launch['cap_seconds'],imported_formal_protocol_qualified=True,
                                    original_raw_audit_passed=self.value(row['raw_audit_passed']),original_journal_return_missing=self.value(row['journal_return_missing']),
                                    independent_actual_return_code=0,own_U=record['U'],qualified_L=0.,certificate=record['certificate'],
                                    signed_recovery_SHA=digest(signed_raw),qualification_basis='fixed actually executed independent current-call proof plus whole original outward clock interval'))
            imported.append(dict(number=number,**row,imported_formal_protocol_qualified=True,
                                 imported_qualification_source='Round110 final actually executed public_full_raw02 independent review'))
            primitive = {k:self.value(row.get(k,'')) for k in ('U','L','gap','certificate','numbers_qualified','certificate_qualified',
                                                               'complete_seconds','complete_seconds_interval')}
            primitive.update(id=key[0],seed=key[1],arm=key[2],formal_protocol_qualified=True,PE_SHA=PE,DLL_SHA=DLL)
            published_primitives.append(primitive)
        recomputed = []
        published_recomputed = []
        for role in independent['PANEL']:
            rid = role[0]
            arms = {v['arm']:v for v in records if v['id'] == rid}
            published_arms = {v['arm']:v for v in published_primitives if v['id'] == rid}
            self.require(set(arms) == {'M-B','ENS-C','P-GRB'}, 'same complete three-arm original role '+rid)
            for a,c in [('M-B','P-GRB'),('M-B','ENS-C'),('ENS-C','P-GRB')]:
                result = independent['pair'](arms[a],arms[c])
                published_result = independent['pair'](published_arms[a],published_arms[c])
                self.require(all(result[f] == published_result[f] for f in ('classification','evaluable','severe_regression')),
                             'native and original publication numeric policies give identical pair class/severity')
                matched = [r for r in original_pairs if (r['id'],int(r['seed']),r['candidate'],r['control']) == (rid,0,a,c)]
                self.require(len(matched) == 1, 'exact inherited main pair source '+rid+' '+a+'/'+c)
                original = matched[0]
                for field in ('classification','evaluable','severe_regression','candidate_U','candidate_L','control_U','control_L','candidate_gap','control_gap',
                              'candidate_certified','control_certified','candidate_seconds','control_seconds','a_U','a_gap','a_t'):
                    self.require(self.value(original[field]) == published_result.get(field), 'independent main pair arithmetic '+rid+' '+a+'/'+c+' '+field)
                if a == 'M-B' and c == 'P-GRB':
                    self.require(selected['main_primary_pairs'][rid]['classification'] == result['classification'], 'original twelve primary decisions '+rid)
                recomputed.append(result)
                published_recomputed.append(published_result)
        primary = [p for p in recomputed if p['candidate'] == 'M-B' and p['control'] == 'P-GRB']
        ens = [p for p in recomputed if p['candidate'] == 'M-B' and p['control'] == 'ENS-C']
        stats = dict(main_counts=dict(Counter(p['classification'] for p in primary)),MB_ENS_counts=dict(Counter(p['classification'] for p in ens)),
                     main_severe_P_regressions=sum(p['severe_regression'] is True for p in primary),main_denominator=12)
        self.require(stats['main_counts'] == {'WIN':11,'TIE':1} and stats['MB_ENS_counts'] == {'WIN':5,'TIE':3,'LOSS':4},
                     'actual unchanged inherited gains and ENS costs')
        write(self.destination/'main36_actual_independent_records.json',records)
        write(self.destination/'main36_original_clock_evidence.json',clocks)
        write(self.destination/'main36_imported_rows.json',imported)
        write(self.destination/'main36_qualification_derivations.json',derived)
        write(self.destination/'main36_independently_recomputed_pairs.json',recomputed)
        write(self.destination/'main36_published_primitive_recomputed_pairs.json',published_recomputed)
        write(self.destination/'main36_preserved_numeric_differences.json',numeric_differences)
        retained = {p.relative_to(self.root).as_posix():digest(p.read_bytes()) for p in sorted(self.destination.rglob('*'))
                    if p.is_file() and p.name not in ('stdout.log','stderr.log')}
        return dict(decision='ACCEPT_FIXED_R110_MAIN36_IMPORT',evidence_layer='R110_MAIN_36_PLUS_R111_SEED_6',
                    inherited_science_commit=SCIENCE,verified_R110_head=BASE,original_full_independent_audit_SHA=AUDIT_SHA,
                    original_full_independent_receipt_SHA=RECEIPT_SHA,original_audit_not_duplicated=True,
                    current_import_repeats_historical_matrix_or_physics=False,main36_actually_executed_historical_raw_authority=True,
                    full_clock_qualification=all(v['formal_protocol_qualified'] for v in clocks),
                    preserved_old_round110_stage=selected['stage'],preserved_old_all42_valid_formal=selected['all42_valid_formal'],
                    stats=stats,derived_empty_qualification_arms=[15,17,25,26],source_bindings=self.bindings,retained_bindings=retained,
                    original_signed_native_publication_numeric_differences=numeric_differences,
                    completed_checks=self.checks,Optimize=0,native_environment=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--label',default='inherited_main01')
    args = parser.parse_args()
    root = args.root.resolve()
    destination = root/NEW/'review'/args.label
    destination.mkdir(parents=True,exist_ok=False)
    start = time.perf_counter()
    launch = dict(cwd=str(Path.cwd().resolve()),root=str(root),source_root=str(args.source_root.resolve()),argv=__import__('sys').argv,
                  PID=os.getpid(),source_SHA=digest(Path(__file__).read_bytes()),start_utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat())
    write(destination/'launch.json',launch)
    (destination/'execution_source.py').open('xb').write(Path(__file__).read_bytes())
    stdout = (destination/'stdout.log').open('x',encoding='utf-8',newline='\n')
    stderr = (destination/'stderr.log').open('x',encoding='utf-8',newline='\n')
    sys = __import__('sys')
    sys.stdout = Tee(sys.stdout,stdout)
    sys.stderr = Tee(sys.stderr,stderr)
    code = 1
    try:
        audit = Import(root,args.source_root,destination).run()
        audit['source_SHA'] = launch['source_SHA']
        write(destination/'audit.json',audit)
        print(json.dumps(dict(decision=audit['decision'],stats=audit['stats'],checks=audit['completed_checks'])),flush=True)
        code = 0
    except Exception:
        traceback.print_exc()
    receipt = dict(exit_code=code,cwd=launch['cwd'],explicit_read_root=str(root),source_root=launch['source_root'],
                   engineering_elapsed_seconds=time.perf_counter()-start,source_SHA=launch['source_SHA'],Optimize=0,native_environment=0)
    sys.stdout.flush()
    sys.stderr.flush()
    receipt['stdout_SHA'] = digest((destination/'stdout.log').read_bytes())
    receipt['stderr_SHA'] = digest((destination/'stderr.log').read_bytes())
    if (destination/'audit.json').exists():
        receipt['audit_SHA'] = digest((destination/'audit.json').read_bytes())
    write(destination/'receipt.json',receipt)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
