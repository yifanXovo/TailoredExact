"""Predeclared bounded v3 stage; no implicit confirmation or retuning."""
import argparse
import json
import shutil
import time
import round62_research as r


def identity():
    checks=[]
    for role in ['D3','D4']:
        for mode in ['off','events','conflicts','projection','service','service-conflicts','projection-rlt']:
            fresh=r.RAW/'preflight_v3'/role/mode/'canonical_model.lp'
            old=r.RAW/'mip_v2'/role/mode/'canonical_model.lp'
            if not old.exists():old=r.RAW/'lp_v2'/role/mode/'canonical_model.lp'
            if old.exists():
                assert r.sha(fresh)==r.sha(old),(role,mode)
                checks.append(dict(id=role,mode=mode,sha256=r.sha(fresh),unchanged=True))
    assert len(checks)>=9
    r.write(r.OUT/'preflight_v3_identity.json',checks)
    saved=[]
    for exe in json.loads((r.OUT/'build_freeze_v3.json').read_text())['executables']:
        dest=r.RAW/'paired_executables'/exe['sha256']/exe['name']
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r.BUILD/exe['name'],dest)
        assert r.sha(dest)==exe['sha256'];saved.append(dict(**exe,path=str(dest.relative_to(r.ROOT))))
    r.write(r.OUT/'paired_executables_v3.json',saved)
    shutil.copyfile(r.BUILD/'tests.log',r.OUT/'tests_v3.log')


def screen():
    identity()
    r.fixed(['D4'],['off','projection','projection-service'],120,'screen_v3','solve')
    r.fixed(['D3'],['off','projection-service'],600,'screen_v3','solve')
    r.projection_audit(['D3','D4'],120,'projection_audit_v3')


def select():
    from analyze_round62 import performance
    from report_round62 import compare
    path=r.OUT/'selected_candidate.json'
    if path.exists():raise RuntimeError('selection already recorded')
    rows={(x['id'],x['arm']):x for x in performance() if x['stage']=='screen_v3' and x.get('scope') and x['performance_eligible']}
    comparisons=[compare(rows[(i,'off')],rows[(i,'projection-service')]) for i in ['D3','D4']]
    comparisons.append(compare(rows[('D4','projection')],rows[('D4','projection-service')]))
    losses={'certificate_loss','time_loss','gap_loss'};gains={'certificate_gain','time_gain','gap_gain'}
    accepted=not any(x['decision'] in losses for x in comparisons) and any(x['decision'] in gains for x in comparisons[:2])
    choice='projection-service' if accepted else 'projection'
    r.write(path,dict(selected_at_unix=time.time(),threshold_mode=choice,
        predeclared_rule='research_log.md B5; no material loss vs OFF D3/D4 or box D4; one meaningful gain vs OFF',
        service_projection_screen_passed=accepted,comparisons=comparisons,
        status='research candidate only; stable presets unchanged',
        fallback='box retains a D4 and C2 benefit but fails D3 protection; use as mixed-result comparator if B5 fails',
        protocol_sha256=r.sha(r.OUT/'protocol.json'),build_freeze_sha256=r.sha(r.OUT/'build_freeze_v3.json')))
    print('frozen development selection',choice,'service-projection screen passed',accepted,flush=True)


def development():
    selection=json.loads((r.OUT/'selected_candidate.json').read_text());mode=selection['threshold_mode']
    for threshold in ['off',mode]:r.full(['C2'],['off','passive-cert'],threshold,600,'k1_v3',True)
    r.reference('C2',600,'references_v3')


def confirmation():
    from verify_round62 import main as verify
    from report_round62 import coverage_audit
    selection=json.loads((r.OUT/'selected_candidate.json').read_text());mode=selection['threshold_mode']
    if (r.OUT/'confirmation_freeze.json').exists():raise RuntimeError('confirmation already frozen')
    entries=r.previous.entries()
    dev=[e for e in entries if e['stage'] in ['k1_v3','references_v3']]
    assert len(dev)==6
    for e in dev:
        done=json.loads((r.ROOT/e['destination']/'completion.json').read_text())
        assert done['returncode']==0 and done['within_budget'] and not done['watchdog']
    assert not any(e['id'] in ['C1','C3'] for e in entries)
    freeze=json.loads((r.OUT/'build_freeze_v3.json').read_text())
    assert all(r.sha(r.ROOT/n)==h for n,h in freeze['source_files'].items())
    verify();coverage_audit()
    r.write(r.OUT/'confirmation_freeze.json',dict(frozen_at_unix=time.time(),
        build_freeze='build_freeze_v3.json',build_sha256=r.sha(r.OUT/'build_freeze_v3.json'),
        execution_driver_sha256={str(p.relative_to(r.ROOT)):r.sha(p) for p in [r.ROOT/'scripts/round62_research.py',r.ROOT/'scripts/round62_v3_stage.py']},
        selection_sha256=r.sha(r.OUT/'selected_candidate.json'),protocol_sha256=r.sha(r.OUT/'protocol.json'),
        completed_development_launches=[e['charged_number'] for e in entries if e['charged']],
        roles=['C1','C3'],description='Previously public; no Round62 input parsing or optimization before this freeze',
        preset='research-round59-k1-s',cap_seconds=600,
        archive_modes=['off','passive-cert'],threshold_modes=['off',mode],
        policy='full two-by-two comparison; no post-confirmation tuning; keep all regressions',
        independent_development_proofs_and_witnesses_passed=True))
    print('confirmation frozen before first C1/C3 launch',flush=True)
    for role in ['C1','C3']:
        for threshold in ['off',mode]:r.full([role],['off','passive-cert'],threshold,600,'confirmation_v3',True)


def micro():
    source=next(e for e in r.previous.entries() if e['kind']=='native-micro')
    dest=r.RAW/'native_micro_v3'/'D1';cmd=source['command'][:]
    cmd[0]=r.BUILD/'Round62NativeMicro.exe';cmd[cmd.index('--out')+1]=dest
    r.execute(cmd,dest,r.panel()['D1'],'passive-native-stop','native_micro_v3',20,'native-micro',1)


def clean_repeat():
    p=r.panel()['D3'];dest=r.RAW/'screen_v3'/'D3'/'projection-service-clean-repeat'
    cmd=r.previous.fixed_command(p,dest,'off',600,False)
    cmd[cmd.index('--state-id')+1]='D3-F0-projection-service'
    cmd[cmd.index('--mode')+1]='solve';cmd+=['--round62-threshold-mode','projection-service']
    r.execute(cmd,dest,p,'projection-service','screen_v3',600)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['identity','screen','select','development','confirmation','micro','clean_repeat'])
    globals()[parser.parse_args().action]()


if __name__=='__main__':main()
