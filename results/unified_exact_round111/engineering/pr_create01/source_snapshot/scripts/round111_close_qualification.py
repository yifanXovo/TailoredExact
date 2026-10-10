"""Freeze final performance bindings and disclose finite wrapper closure."""
from round111_common import *
import round111_campaign as campaign
import shutil

def main():
    assert not (OUT/'qualification/final_wrapper_closure.json').exists()
    dest=OUT/'qualification/final_wrapper_sources';dest.mkdir(parents=True,exist_ok=True)
    originals=OUT/'qualification/preclosure_identities';originals.mkdir(exist_ok=True)
    for relative in ('campaign/identity.json','candidate_identity.json'):
        target=originals/relative;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert sha(target)==sha(OUT/relative)
        else:shutil.copyfile(OUT/relative,target)
    formal=read(OUT/'campaign/identity.json');formal.update(helpers=campaign.helpers(),runner_sha256=sha(campaign.__file__))
    (OUT/'campaign/identity.json').write_text(json.dumps(formal,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    candidate=read(OUT/'candidate_identity.json');candidate.update(helpers=campaign.helpers(),campaign_identity_SHA=sha(OUT/'campaign/identity.json'))
    (OUT/'candidate_identity.json').write_text(json.dumps(candidate,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    paths={}
    for path in ('scripts/round111_campaign.py','scripts/round111_common.py','scripts/round111_seed_audit.py'):
        target=dest/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target);paths[path]=sha(target)
    samples=[]
    for name,engineering in [('wrapper_replay_normal_02','wrapper_normal02'),('wrapper_replay_trailer_failure_01','wrapper_trailer_failure01')]:
        p=OUT/'qualification'/name;value=read(p/'audit.json')
        samples.append(dict(path=p.relative_to(ROOT).as_posix(),audit_SHA=sha(p/'audit.json'),
            receipt_SHA=sha(p/'fees/retained_wrapper/receipt.json'),engineering_receipt=(OUT/'engineering'/engineering/'receipt.json').relative_to(ROOT).as_posix(),
            engineering_receipt_SHA=sha(OUT/'engineering'/engineering/'receipt.json'),mode=value['mode'],
            actual_native_processes=0,Optimize=0,maximum_required_metadata_write_seconds=value['maximum_required_metadata_write_seconds']))
    metadata=max(p['maximum_required_metadata_write_seconds'] for p in samples)
    envelope=read(OUT/'qualification/envelope.json')
    assert envelope['maximum_necessary_postexit_seconds']+metadata<=15
    qual=read(OUT/'qualification/cli01/identity.json')
    closure=dict(passed=True,actual_CLI_helper_bindings=qual['helpers'],final_helper_bindings=campaign.helpers(),
        original_cli_identity_SHA=sha(OUT/'qualification/cli01/identity.json'),actual_qualification_identity_SHA=sha(OUT/'qualification/identity.json'),
        final_sources=paths,diff_SHA={name:sha(OUT/'qualification/wrapper_replay_normal_02'/(name+'.diff')) for name in ('round111_campaign.py','round111_common.py')},
        wrapper_replay=samples,corrected_qualification_outer_interval=read(OUT/'fees/qualification_cli02/outer_accounting_interval.json'),
        added_required_metadata_cost_seconds=metadata,all_empirical_postexit_with_added_metadata_seconds=[v['necessary_postexit_seconds']+metadata for v in envelope['observations']],
        actual_native_qualification_not_rerun=True,limited_wrapper_boundary_closure_not_byte_identical_CLI=True,
        identical_supervisor_native_argv_math_adapter=True,original_CLI_fee_receipt_SHA=sha(OUT/'fees/qualification_cli02/receipt.json'),
        current_budget=budget(),Optimize=0)
    write(OUT/'qualification/final_wrapper_closure.json',closure)
    print(json.dumps(dict(final_helpers=campaign.helpers(),metadata_seconds=metadata,budget=budget())),flush=True)

if __name__=='__main__':main()
