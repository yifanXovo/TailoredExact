"""Bounded, zero-native verification of the current paper entry and R135 identity."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
BASE = '25800aa6b51bf7607b51e5df14a10a5ca4571889'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-c', 'maintenance.auto=false', '-c', 'gc.auto=0', *args], cwd=ROOT)


def verify():
    spec = importlib.util.spec_from_file_location('paper_s2', ROOT/'scripts/paper_s2.py')
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    config = read(ROOT/'config/paper_s2.json')
    rows = [g for stage in ('C', 'D') for g in read(ROOT/f'results/unified_exact_round135/{stage}_matrix_frozen.json')['groups']]
    rows = [g for g in rows if g['launch']['variant'] == 'S2']
    assert len(rows) == 16
    checks = []
    dry_root = Path('E:/codes/ExactEBRP-work/temp/round136/argv-only')
    for row in rows:
        launch = row['launch']
        panel = launch['panel']
        assert launcher.normalize(launch['command'], config) == config['argv']
        output = dry_root / launch['arm_id']
        assert not output.exists()
        args = [sys.executable, '-B', str(ROOT/'scripts/paper_s2.py'),
                '--input', str(ROOT/panel['input_path']), '--out-dir', str(output),
                '--T', str(panel['T_seconds']), '--pickup-time', str(panel['pickup_seconds']),
                '--drop-time', str(panel['drop_seconds']), '--lambda', str(panel['lambda']),
                '--cap', str(launch['cap_seconds']), '--seed', str(launch['seed']), '--json']
        actual = json.loads(subprocess.check_output(args, cwd=ROOT))
        assert actual['dry_run'] and not output.exists()
        assert actual['matches_verified_PE'] and actual['matches_verified_DLL']
        assert launcher.normalize(actual['command'], config) == config['argv']
        fixed = lambda argv, flag: argv[argv.index(flag)+1]
        for flag in ['--T', '--pickup-time', '--drop-time', '--lambda', '--time-limit',
                     '--process-wall-time-limit', '--gurobi-seed']:
            assert float(fixed(actual['command'], flag)) == float(fixed(launch['command'], flag))
        assert actual['input_SHA256'] == panel['input_sha256']
        assert '--round135-aggregate-penalty' not in actual['command']
        checks.append(dict(arm=launch['arm_id'],tokens=len(actual['command']),
                           whole_vector_equal_after_allowed_normalization=True,
                           physical_and_experiment_values_equal=True,input_SHA256=actual['input_SHA256']))
    example = [sys.executable, '-B', str(ROOT/'scripts/paper_s2.py'), '--input',
               str(ROOT/'results/unified_exact_round130/inputs/UC-B20-B.txt'), '--out-dir',
               str(dry_root/'refusal'), '--T', '7200', '--cap', '600', '--seed', '0']
    refusal_checks = []
    for label, extra in [('existing_output',['--out-dir', str(ROOT)]),
                         ('insufficient_cap',['--cap','36']),('negative_seed',['--seed','-1']),
                         ('nonfinite_weight',['--lambda','nan']),
                         ('algorithm_override',['--round135-aggregate-penalty'])]:
        result = subprocess.run([*example,*extra], cwd=ROOT, capture_output=True)
        assert result.returncode != 0 and not (dry_root/'refusal').exists()
        refusal_checks.append(dict(case=label,rejected=True,no_output_created=True))
    manifest = read(ROOT/'results/unified_exact_round135/candidate_manifest.json')
    source_checks = {p: sha(ROOT/p) == h for p,h in manifest['source_hashes'].items()}
    assert all(source_checks.values())
    assert git('diff','--name-only',BASE,'--','src','include').strip() == b''
    immutable = ['manuscript.md','manuscript.pdf','paper_body.md','model_and_algorithm_appendices.md',
                 'supplement.md','references.bib','candidate_decision.json','C_matrix_frozen.json','D_matrix_frozen.json']
    unchanged = {}
    for name in immutable:
        path='results/unified_exact_round135/'+name
        old=git('show',BASE+':'+path)
        assert (ROOT/path).read_bytes() == old
        unchanged[path]=hashlib.sha256(old).hexdigest()
    baseline = read(ROOT/'results/unified_exact_round135/baseline.json')
    protected={str(Path('E:/codes/ExactEBRP')/p):h for p,h in baseline['protected_dirty'].items()}
    protected.update(baseline['protected_assets'])
    protected[config['default_executable']]=config['verified_PE_SHA256']
    protection = {p:dict(expected=h,observed=sha(p)) for p,h in protected.items()}
    assert all(x['expected']==x['observed'] for x in protection.values())
    original_head=git('-C','E:/codes/ExactEBRP','rev-parse','HEAD').decode().strip()
    assert original_head==baseline['original_tree_head']
    restore=Path('E:/codes/ExactEBRP-work/restore/round135-public-2b27711484d8')
    assert restore.is_dir()
    return dict(status='PASS_BOUNDED_ZERO_NATIVE_ENTRY_CHECK',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                source='R135 frozen full S2 launch records',all_S2_launches=checks,refusal_checks=refusal_checks,
                production_sources_checked=len(source_checks),production_sources_unchanged=True,
                immutable_R135_bytes=unchanged,protected=protection,original_HEAD=original_head,
                passed_public_restore_retained=True,new_native_seconds=0,new_Optimize=0,recompile=0,
                formal_performance_samples_added=0,scope='full argv/config dry runs, current source/PE/DLL and paper identities only; not another native reproduction')


if __name__ == '__main__':
    value=verify()
    if len(sys.argv)>1:
        target=Path(sys.argv[1])
        if target.exists():raise SystemExit('refuse to overwrite verification receipt: '+str(target))
        target.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=value['status'],S2_launches=len(value['all_S2_launches']),
                          sources=value['production_sources_checked'],native_seconds=0)))
