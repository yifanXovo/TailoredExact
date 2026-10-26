"""Prospective first complete F5 comparison, including late native opportunities."""
import argparse,json,subprocess
from pathlib import Path
import round97_campaign as campaign
from round97_campaign import ROOT,OUT,BUILD,read,write,sha,ext,r90

def prepare():
    ext.ensure_idle();camp=OUT/'development01';assert not camp.exists()
    qualified=[json.loads(s) for s in (OUT/'qualification02/summary.jsonl').read_text().splitlines()]
    assert len(qualified)==3 and all(x['audit_passed'] for x in qualified)
    q=read(OUT/'qualification02/identity.json');assert q['source_hashes']==campaign.bindings()
    assert q['candidate_binary_sha256']==sha(BUILD/'ExactEBRP.exe')
    prior=read(ROOT/'results/unified_exact_round96/primal/identity.json')
    panel=dict(next(x['panel'] for x in prior['launches'] if x['id']=='F5'))
    panel['cap_seconds']=3600;panel['instance_path']=panel['input_path']
    assert sha(ROOT/panel['input_path'])==panel['input_sha256']
    prereg=q['prereg'];launches=[]
    for arm in ['SHADOW','FEEDBACK','OFF','P-GRB']:
        number=len(launches)+1;mode={'OFF':'observe','SHADOW':'shadow','FEEDBACK':'feedback','P-GRB':'off'}[arm]
        dest=camp/'raw'/f'{number:02d}_F5_{arm}'
        command=(r90.audited_runner_utilities.command_for(prereg,panel,arm,dest) if arm=='P-GRB'
                 else r90.command_for(prereg,panel,'ENS-C',dest)+['--round97-native-closure',mode])
        launches.append(dict(number=number,id='F5',arm=arm,mode=mode,panel=panel,destination=str(dest),
            stage='complete_development_long_window',cap_seconds=3600,hard_stop_seconds=3598,command=command))
    write(camp/'identity.json',dict(q,source_ref=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        schema='round97-first-complete-development-v1',launches=launches,maximum_starts=4,maximum_process_seconds=14400,
        runner_sha256=sha(campaign.__file__),development_runner_sha256=sha(__file__),
        qualification_identity_sha256=sha(OUT/'qualification02/identity.json'),
        qualification_summary_sha256=sha(OUT/'qualification02/summary.jsonl'),
        question='Separate candidate quality/cost from feedback effect on complete original proof, with unchanged startup. F5 prior original log has later improvements only after terminal-MIP469s. Four common3600s windows, fixed before any long-arm outcome; counts once as the development long window.'))
    print('Prepared four complete F5 arms, maximum14400 seconds')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);p.add_argument('--number',type=int);a=p.parse_args()
    if a.action=='prepare':prepare()
    else:
        identity=read(OUT/'development01/identity.json');assert identity['development_runner_sha256']==sha(__file__)
        campaign.run('development01',a.number)
