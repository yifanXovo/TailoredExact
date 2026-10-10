"""Close the one finite empirical audit envelope; never authorize native by itself."""
from round111_common import *
import shutil
import round111_seed_audit as audit

def run():
    plan=read(OUT/'replay_plan.json');replays=[]
    for number in range(37,43):
        labels=[f'new_arm{number}_replay01']+([f'new_arm42_replay{i:02d}' for i in [2,3]] if number==42 else [])
        for label in labels:
            d=OUT/'qualification/replays'/label;r=read(d/'receipt.json')
            assert r['comparison']['exact_recursive_equal'] and r['error'] is None
            assert r['necessary_postexit_seconds']<=15
            assert r['optimized_phase_metrics']['cached_models_after_clear']==0
            replays.append(dict(label=label,receipt_SHA=sha(d/'receipt.json'),**r))
    for label in ['new_H100_P_replay01','new_H100_MB_replay01']:
        r=read(OUT/'qualification/replays'/label/'receipt.json');assert r['comparison']['exact_recursive_equal']
    assert read(OUT/'qualification/counterexamples01/audit.json')['passed']
    observation=[]
    for s in plan['samples']:
        # All frozen bytes, including original clocks/flags, remain untouched.
        for f in s['files']:assert sha(OLD_ROOT/f['path'])==f['SHA'],f['path']
        if s['campaign']=='campaign':
            d=Path(s['launch']['destination']);c=read(d/'completion.json');n=read(d/'native_end_receipt.json')
            observation.append(dict(number=s['number'],native_end=n['complete_seconds_until_native_end'],
                supervisor_observed=c['fully_observed_end_to_end_seconds'],postexit_drain_and_restore=c['postexit_drain_and_restore_seconds'],
                combined_original_preentry_and_exit_offset=n['complete_seconds_until_native_end']-c['fully_observed_end_to_end_seconds'],
                original_whole=read(d/'whole_arm_receipt.json')['complete_seconds'],cap=s['launch']['cap_seconds']))
    for role in ['G20-C2','G50-R1','G100-R2','H100']:
        dest=ROOT/OLD/'qualification/reference'/role;dest.mkdir(parents=True,exist_ok=True)
        for name in ['original.lp','build.json']:
            source=OLD_ROOT/OLD/'qualification/reference'/role/name
            if not (dest/name).exists():shutil.copyfile(source,dest/name)
            assert sha(source)==sha(dest/name)
    inherited=[]
    for name in ['qualification/parser_equivalence_receipt.json','qualification/main_entry_receipt.json','qualification/identity.json','repair_evidence.json','candidate_contract_freeze.json']:
        src=OLD_ROOT/OLD/name;dest=OUT/'inherited_qualification'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,dest);inherited.append(dict(original_path=f'{OLD}/{name}',path=dest.relative_to(ROOT).as_posix(),SHA=sha(dest)))
    maximum=max(r['necessary_postexit_seconds'] for r in replays);entry=max(r['necessary_admission_identity_seconds'] for r in replays)
    known=max(v['combined_original_preentry_and_exit_offset'] for v in observation)
    value=dict(passed=True,helper_SHA=sha(audit.__file__),replay_plan_SHA=sha(OUT/'replay_plan.json'),
        counterexamples_SHA=sha(OUT/'qualification/counterexamples01/audit.json'),observations=replays,
        maximum_necessary_postexit_seconds=maximum,maximum_measured_identity_entry_seconds=entry,
        original_native_observation_exit_costs=observation,maximum_original_combined_preentry_exit_seconds=known,
        shutdown_reserve_seconds=30,conservative_empirical_remaining_seconds=30-maximum-entry-known,
        not_hard_realtime_bound=True,no_runtime_switch=True,current_dynamic_checks_in_cap=True,
        R110_arm42_still_invalid=True,old_raw_rehashed_unchanged=True,inherited_entry_evidence=inherited,
        note='Old arm42 is the second arm of its group. Its audit is not attributed to historical first-arm admission. cProfile old replay is instrumented, not a new performance clock.')
    write(OUT/'qualification/envelope.json',value)
    profile=read(OUT/'qualification/replays/old_arm42_profile03/receipt.json')
    lines=['# Actual audit cost profile and empirical envelope','',
        'The old arm42 original necessary audit was 29.69575260009151s. Its old native/audit/whole clocks and invalid eligibility remain immutable.',
        'An unchanged old adapter was profiled with cProfile and stage timers: 60.2785013000248s inclusive. Instrumentation overhead prevents treating this as an uninstrumented speed ratio.',
        'Nested times below overlap and must not be summed. The two earlier old-only comparison failures exposed only the nested neutral-exchange replay timer; their actual exits and complete measured adapter costs are retained. The timer whitelist correction preceded every new audit replay.','',
        '|Old measured stage|Seconds|','|---|---:|']
    lines += [f'|{k}|{v:.6f}|' for k,v in profile['phases'].items()]
    lines += ['', 'cProfile additionally measures Seed proof 48.954s inclusive, original adapter 10.924s inclusive, neutral exchange/closure physical oracle 10.616s inclusive and native physical/journal audit .263s inclusive. No separate return-only timer exists; it stays inside Seed/native scope. Writes are included by replay receipts.','',
        '|Fresh new replay|Necessary postexit seconds|','|---|---:|']
    lines += [f'|{r["label"]}|{r["necessary_postexit_seconds"]:.9f}|' for r in replays]
    lines += ['',f'Maximum postexit {maximum:.9f}s; measured identity admission {entry:.9f}s. Original combined preentry/exit offset upper observation {known:.9f}s (includes its recorded admission); empirical 30s reserve remainder {30-maximum-entry-known:.9f}s.',
        'These finite observations qualify the fixed machine envelope, not a Windows/IO worst-case guarantee. New CLI and every formal arm retain actual native_end, audit_end and whole receipts. No necessary check is moved outside cap.']
    (OUT/'audit_cost_profile.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,max_postexit=maximum,empirical_reserve_remaining=value['conservative_empirical_remaining_seconds'])))

if __name__=='__main__':run()
