"""Prepare the finite R85 protocol and inherited audit tools; never optimize."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round85'
IDS=['E7','S12','D3','C2','C6','C8','D6']
CAPS=dict(E7=120,S12=120,D3=300,C2=300,C6=600,C8=600,D6=3600)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,d):
    (ROOT/p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def changed(text,old,new):
    assert old in text,old
    return text.replace(old,new)
def clone(name,replacements):
    target=ROOT/('scripts/round85_'+name+'.py');assert not target.exists()
    text=(ROOT/('scripts/round84_'+name+'.py')).read_text(encoding='utf-8')
    for old,new in replacements:text=changed(text,old,new)
    target.write_text(text,encoding='utf-8')

def main():
    assert not (OUT/'protocol.json').exists()
    OUT.mkdir(exist_ok=True)
    origins=dict(small='results/unified_exact_round79/campaign/identity.json',
        short='results/gf_budgeted_proof_round65/protocol.json',
        repeat='results/unified_exact_round84/protocol.json')
    small={r['panel']['id']:r['panel'] for r in read(origins['small'])['launches'] if r['arm']=='P-GRB'}
    short={r['id']:r for r in read(origins['short'])['panel']}
    repeat=read(origins['repeat'])
    source={**{i:small[i] for i in ['E7','S12','D3','C2']},**{i:short[i] for i in ['C6','C8']},
        'D6':next(r for r in repeat['panel'] if r['id']=='D6')}
    panel=[]
    for identity in IDS:
        p=dict(source[identity]);assert sha(p['instance_path'])==p['input_sha256']
        p.update(cap=CAPS[identity],stage='exposed_development',role='R85 frozen remaining protection / D6 finite repeat; see plan.md')
        panel.append(p)
    write('results/unified_exact_round85/protocol.json',dict(panel=panel,order=IDS,
        arms=['P-GRB','ENS-C','K1-R'],all_inputs_exposed=True,
        source=origins,source_hashes={k:sha(v) for k,v in origins.items()},
        prior_bindings={'D6':repeat['prior_bindings']['D6']},
        prior_D6_campaign_identity_sha256=sha('results/unified_exact_round84/campaign/identity.json'),
        prior_D6_endpoints_sha256=sha('results/unified_exact_round84/campaign/endpoint_checks.json'),
        checkpoints={'120':[30,60,120],'300':[60,120,180,300],'600':[60,120,300,600],
            '3600':[300,600,1200,1800,2400,3600]},maximum_process_seconds=16920))
    clone('research',[
        ('Round84 frozen ENS-C long protection and finite same-build repetition.','Round85 frozen remaining ENS-C protection and one D6 repetition.'),
        ('unified_exact_round84','unified_exact_round85'),
        ("ROLE_IDS=['D6','D7','U6']",'ROLE_IDS='+repr(IDS)),
        ('CAPS={i:3600 for i in ROLE_IDS}','CAPS='+repr(CAPS)),
        ('codex/round84-ensc-long-protection-replication','codex/round85-ensc-remaining-protection-replication'),
        ("assert read(STAGE/'base_publication.json')['head_sha']=='131d09280a1563243d0201e68367b26baf5079c3'", "assert read(STAGE/'base_publication.json')['head_sha']=='ed0cd977ac2ea1cf7a7bf1236a15dd845a3ed948'\n    prior_stage=ROOT/'results/unified_exact_round84'\n    assert read(prior_stage/'campaign/driver_completion.json')['all_valid']\n    assert read(prior_stage/'campaign/audit.json')['all_checks_passed']\n    assert read(prior_stage/'campaign/mechanism_audit.json')['all_checks_passed']\n    assert read(prior_stage/'campaign/replication_audit.json')['all_checks_passed']\n    assert not (prior_stage/'campaign/active_run.lock').exists()"),
        ('len(roles)==9 and sum(CAPS[p[\'id\']] for p,_,_ in roles)==32400','len(roles)==21 and sum(CAPS[p[\'id\']] for p,_,_ in roles)==16920'),
        ('maximum_process_seconds=32400','maximum_process_seconds=16920'),
        ('reference_builds=3','reference_builds=7'),
        ('planned=9','planned=21'),('len(records)==9','len(records)==21'),
        ("'scripts/round84_research.py'","'scripts/round85_research.py'")
    ])
    clone('analyze',[
        ('unified_exact_round84','unified_exact_round85'),('scripts/round84_research.py','scripts/round85_research.py'),
        ("3600:[300,600,1200,1800,2400,3600]","600:[60,120,300,600],3600:[300,600,1200,1800,2400,3600]"),
        ("summary['completed']==9","summary['completed']==21"),
        ("len(frozen['launches'])==9 and len(summary['records'])==9","len(frozen['launches'])==21 and len(summary['records'])==21"),
        ('len(all_checkpoints)==54 and len(endpoint_checks)==9','len(all_checkpoints)==84 and len(endpoint_checks)==21'),
        ("for identity in ['D6','D7','U6']:","for identity in "+repr(IDS)+":"),
        ('len(comparisons)==54 and len(protection)==18','len(comparisons)==84 and len(protection)==28'),
        ('completed=9','completed=21')
    ])
    clone('mechanism',[
        ('from round84_analyze','from round85_analyze'),('unified_exact_round84','unified_exact_round85'),
        ('len(traces)==3 and controls==6','len(traces)==7 and controls==14'),
        ("assert candidates,'Every declared R84 ENS arm has a frozen R83 startup binding'","if identity not in bindings:\n            assert not candidates, 'Available prior ENS startup must be explicitly bound'\n            continue\n        assert candidates,'Declared prior ENS startup binding missing'"),
        ('len(prior_pairs)==3','len(prior_pairs)==1')
    ])
    clone('replication',[
        ('One same-build U6 repetition','One same-build D6 repetition'),('from round84_analyze','from round85_analyze'),
        ('results/unified_exact_round83/campaign','results/unified_exact_round84/campaign'),
        ('prior_U6','prior_D6'),("'U6'","'D6'"),
        ("summary['completed']==9 and old_summary['completed']==13","summary['completed']==21 and old_summary['completed']==9"),
        ('prior_stage=83,current_stage=84','prior_stage=84,current_stage=85'),
        ('[(83,old_end),(84,new_end)]','[(84,old_end),(85,new_end)]'),
        ('dict(old,origin=83),dict(new,origin=84)','dict(old,origin=84),dict(new,origin=85)'),
        (',50)',',30)'),
        ('D6/D7 earlier R78-build long results are historical background, not this same-build repeat.','Other roles have fresh matched current-build controls; earlier-build rows remain historical context.')
    ])
    clone('package',[
        ('Nine new run trees','Twenty-one new run trees'),('unified_exact_round84','unified_exact_round85'),
        ("len(frozen['launches'])==9","len(frozen['launches'])==21"),('len(bundles)==10','len(bundles)==22'),
        ('All nine original complete-run trees and three original compact exports.','All twenty-one original complete-run trees and seven original compact exports.')
    ])
    clone('monitor',[('unified_exact_round84','unified_exact_round85')])
    print(json.dumps(dict(prepared=True,roles=IDS,full_runs=21,maximum_process_seconds=16920,optimizer_calls=0)))

if __name__=='__main__':main()
