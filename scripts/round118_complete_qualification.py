"""Reviewable once-only M-B completion after explicit additional authorization.

The already sealed P-S is rechecked offline; its PE is never restarted. This
wrapper holds finite replay, one M-B child, both postchecks and final admission.
"""
from round118_common import *
import copy,shutil,traceback
import round118_campaign as campaign
from round118_verify import verify
import read_round118 as reader
import round112_audit as start
from round100_idle import ensure_idle

def run():
    auth=read(OUT/'budget_authorization_13.json')
    assert auth['qualification_starts_new']==13 and auth['reuse_sealed_PS_with_corrected_readonly_verifier']
    fee,tick=fee_begin('cli03',1,450,True);code=1;actual=0
    try:
        ensure_idle();check_identity()
        frozen=read(OUT/'qualification/final/identity.json')
        assert frozen['helpers']==helpers() and not (OUT/'qualification/cli03').exists()
        from qualify_round118 import qualify_in_process
        qualify_in_process('finite06')
        ps,mb=frozen['launches'];assert ps['arm']=='P-S' and mb['arm']=='M-B'
        # This work reads the closed result/model/Start/journal only. It supplies
        # no new U/bound/Start and retains the original P-S producer timestamps.
        verify(ps,frozen)
        camp=OUT/'qualification/cli03';camp.mkdir(parents=True)
        ref=camp/'reference/H100';ref.mkdir(parents=True)
        for n in ['original.lp','build.json']:shutil.copyfile(OUT/'qualification/reference/H100'/n,ref/n)
        check_identity();assert sha(ROOT/mb['panel']['input_path'])==mb['panel']['input_sha256']
        campaign.supervised(mb,frozen,tick);campaign.finish_producer(mb,tick,read(fee/'launch.json')['wrapper_creation_unix'])
        verify(mb,frozen)
        post=OUT/'qualification/post03';post.mkdir()
        core=reader.rebuild(ROOT,post/'reconstructed',True,'qualification/final')
        assert len(core['arms'])==2 and all(a['formal_protocol_qualified'] for a in core['arms'])
        assert len(core['same_H'])==1 and core['same_H'][0]['qualified']
        write(post/'actual_Start.json',start.start_audit(ROOT,ps['panel'],Path(ps['destination'])))
        write(post/'summary.json',dict(passed=True,actual_PS_Optimize=1,actual_MB_Optimize=read(Path(mb['destination'])/'result.json')['external_gini_tree_optimize_count'],
            original_PS_producer_seal_unchanged=True,complete_same_H=True,full_original_Start=True,helpers=helpers(),
            final_verifier_after_seal=True,new_native_PS_starts=0,driver_processes=0,holder='charged cli03 wrapper'))
        write(OUT/'review/performance_admission.json',dict(decision='ACCEPT',candidate_identity_SHA=sha(OUT/'candidate_identity.json'),helpers=helpers(),
            fixed_manifest_SHA=sha(OUT/'fixed_manifest.json'),campaign_identity_SHA=sha(OUT/'campaign/identity.json'),production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,source=SOURCE,
            input_SHA=read(OUT/'input_manifest.json')['roles'][0]['input_sha256'],finite_replay_SHA=sha(OUT/'qualification/finite06/summary.json'),
            H100_post_SHA=sha(post/'summary.json'),H100_fee_launch_SHA=sha(fee/'launch.json'),H100_fee_label='cli03',
            H100_actual_wrapper_exit_pending=True,qualification_campaign='qualification/final',
            reused_PS_producer_receipt_SHA=sha(Path(ps['destination'])/'producer_receipt.json'),
            explicit_postverifier_identity_exception_authorization_SHA=sha(OUT/'budget_authorization_13.json'),
            original_PS_actual_launch_identity_SHA=sha(OUT/'qualification/cli02/identity.json'),
            numerical_tolerance=1e-7,measurement_policy_SHA=sha(OUT/'measurement_policy_v2.md'),frozen_UTC=utc(),
            scope='one V40 formal group; no V40 H pilot or guarantee of all future epochs',authorized_qualification_maximum_starts=13,
            qualification_maximum_outer_seconds=1200,total_maximum_starts=20,total_maximum_outer_seconds=28000))
        assert time.perf_counter()-tick<=450;code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        actual=int((OUT/'qualification/cli03/raw/01_H100_S0_M-B/affinity.json').is_file())
        fee_pending(fee,tick,True,code,actual)

if __name__=='__main__':run()
