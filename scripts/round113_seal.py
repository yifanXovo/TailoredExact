"""Offline identity seal before actual four CLI qualification; no native work."""
from round113_common import *
from round113_campaign import helpers
import shutil

def seal():
    assert not list((OUT/'qualification/cli01/raw').glob('*'))
    assert not (OUT/'campaign/summary.jsonl').exists()
    d=OUT/'engineering/pre_CLI_seal01';d.mkdir(parents=True,exist_ok=False)
    paths=['campaign/identity.json','qualification/cli01/identity.json','candidate_identity.json','fixed_manifest.json']
    prior={}
    for path in paths:
        p=OUT/path;prior[path]=read(p);shutil.copyfile(p,d/path.replace('/','_'))
    for path in paths[:2]:
        p=OUT/path;value=dict(prior[path],helpers=helpers())
        assert value['launches']==prior[path]['launches'] and value['source_hashes']==bindings()
        p.unlink();write(p,value)
    c=dict(prior['candidate_identity.json'],helpers=helpers(),campaign_identity_SHA=sha(OUT/'campaign/identity.json'),
        qualification_campaign_identity_SHA=sha(OUT/'qualification/cli01/identity.json'),
        qualification_test_SHA=sha(ROOT/'scripts/qualify_round113.py'),offline_reader_SHA=sha(ROOT/'scripts/read_round113.py'))
    (OUT/'candidate_identity.json').unlink();write(OUT/'candidate_identity.json',c)
    (OUT/'fixed_manifest.json').unlink();write(OUT/'fixed_manifest.json',read(OUT/'campaign/identity.json'))
    write(d/'receipt.json',dict(performance_not_started=True,production_unchanged=True,all_argv_unchanged=True,
        prior_candidate_SHA=sha(d/'candidate_identity.json'),final_candidate_SHA=sha(OUT/'candidate_identity.json'),
        helper_changes={p:dict(before=prior['candidate_identity.json']['helpers'].get(p),after=h) for p,h in helpers().items()
            if prior['candidate_identity.json']['helpers'].get(p)!=h},budget=budget(),Optimize=0))
    print('pre-CLI identity sealed; production and all8 formal argv unchanged')

if __name__=='__main__':seal()
