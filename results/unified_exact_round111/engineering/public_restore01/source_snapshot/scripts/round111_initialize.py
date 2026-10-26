"""Freeze the finite replay set before implementing the audit optimization."""
from round111_common import *
import shutil

def initialize():
    OUT.mkdir(exist_ok=False)
    goal=Path('C:/Users/Administrator/.codex/attachments/84f04e7f-da31-492a-b8a0-10e0955f2059/已粘贴的文本.txt')
    shutil.copyfile(goal,OUT/'goal.md')
    for name in ['production_identity.json','input_manifest.json']:
        shutil.copyfile(OLD_ROOT/OLD/name,OUT/name)
    PE.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(OLD_ROOT/'build/research/round110-entry-v1/ExactEBRP.exe',PE)
    check_identity()
    old=read(OLD_ROOT/OLD/'protocol.json')
    policy=dict(version='round111-fixed-seed-block-v1',evidence_layer='R110_MAIN_36_PLUS_R111_SEED_6',
        inherited_main_commit=SCIENCE,base=BASE,maximum_starts=24,maximum_outer_seconds=18000,
        qualification_maximum_starts=8,qualification_maximum_outer_seconds=600,
        formal_arms=6,nominal_seconds=12600,planned_formal_starts=9,shutdown_margin_seconds=30,
        common_parameters=old['common_parameters'],materiality=old['materiality'],severity=old['severity'],
        closure_tolerance=old['closure_tolerance'],zero_objective_tolerance=old['zero_objective_tolerance'],
        engineering_postexit_maximum_seconds=15,seed_checks=old['seed_checks'],
        original_protocol_SHA=sha(OLD_ROOT/OLD/'protocol.json'),
        numerical_policy_SHA=sha(OLD_ROOT/OLD/'evidence_policy.json'),
        stages=['CONFIRMATION_SUPPORT','CONFIRMATION_NOT_SUPPORTED','BLOCKED'],
        no_cross_arm_cache=True,no_performance_retry=True,no_clock_forgiveness=True)
    write(OUT/'protocol.json',policy)
    (OUT/'research_decision.md').write_text('''# Round111 research decision before implementation

Only an equivalent outer audit execution is changed. The production PE, 205
production bindings, input bytes, models, native argv, algorithm, parameters,
and the 30-second reserve remain R110. Main evidence is the immutable R110
36 arms; the supplementary evidence is a prospectively fixed complete R111
six-arm Seed1 block, in the original order. Evidence layer:
R110_MAIN_36_PLUS_R111_SEED_6.

Two-arm technical recovery was possible. This task deliberately pays another
5400 nominal seconds so all three Seed judgments use one new wrapper and
admission. Seen roles and repeated Seeds add no independent sample count.
R110 remains BLOCKED, all42_valid_formal=false; old arm42 and its pair retain
their invalid clock/UNEVALUABLE status. No best-of-old-and-new selection,
cross-wrapper exact speedup, default change, new mechanism, or 42-arm rerun.

The finite old-raw set, exact-field equivalence and nonmathematical whitelist
are frozen before optimizing. All decisive predicates and old clocks remain
equal. Each measured fresh-process postexit must be <=15 seconds, then two
fixed H100 Seed1 functional CLIs and independent admission precede formal
arm1. This empirical envelope is not a worst-case Windows/IO guarantee.
Final stage is SUPPORT, NOT_SUPPORTED or genuine BLOCKED under the task's
fixed rules. Normal positive and negative performance completes all six.
''',encoding='utf-8')
    samples=[]
    for camp,nums in [('campaign',range(37,43)),('qualification/cli01',[4,5])]:
        ident=read(OLD_ROOT/OLD/camp/'identity.json')
        for num in nums:
            launch=ident['launches'][num-1];d=Path(launch['destination'])
            assert d.is_dir()
            files=[dict(path=f.relative_to(OLD_ROOT).as_posix(),SHA=sha(f),bytes=f.stat().st_size)
                for f in sorted(d.rglob('*')) if f.is_file() and '__pycache__' not in f.parts]
            samples.append(dict(campaign=camp,number=num,launch=launch,identity_path=f'{OLD}/{camp}/identity.json',
                identity_SHA=sha(OLD_ROOT/OLD/camp/'identity.json'),files=files))
    write(OUT/'replay_plan.json',dict(frozen_before_optimization=True,samples=samples,
        new_fresh_process_order=[37,38,39,40,41,42,42,42],old_profile_order=[42],
        equivalence_whitelist=['/offline_audit_seconds'],
        whitelist_scope='Wrapper-added replay timing only. Adapter mathematical outputs including unknown fields compare exactly; no clock or eligibility is waived.',
        numerical_regression_roles=[15,17,25,26],old_raw_read_only=True,Optimize=0,
        old_helper_hashes={f'scripts/{n}':sha(ROOT/'scripts'/n) for n in ['round108_reader.py','round109_seed_scope.py','round109_seed_audit.py','round100_campaign.py']},
        R110_native_audit_whole_clocks_and_qualification_never_recomputed=True))
    write(OUT/'initial_identity.json',dict(base=BASE,science=SCIENCE,PE_SHA=sha(PE),DLL_SHA=sha(DLL),
        production_bindings_SHA=sha(OUT/'production_identity.json'),raw_manifest_SHA=sha(OUT/'replay_plan.json'),
        applicable_AGENTS=[],no_initial_native_process=True,managed_worktree_creation_failed='C disk space; recovered with E sparse worktree'))
    print('frozen finite replay plan; same PE/DLL/205 bindings; zero native')

if __name__=='__main__':initialize()
