"""One bounded production qualification, not a complete performance comparison."""
import copy,ast
import round133_campaign as inherited
from round121_campaign import finish_producer
from round151_read import verify,cap_contract
from round151_common import *
def arm():
    configure();group=read(OUT/'confirmation_matrix.json')['groups'][1]
    identity=copy.deepcopy(read(OUT/group['group']/'identity.json'));launch=identity['launches'][0]
    old=launch['destination'];destination=OUT/'campaign_qualification/raw/R151_qualification_NB35_C'
    launch.update(destination=str(destination),cap_seconds=80,hard_stop_seconds=78,arm_id='R151_qualification_NB35_C',
        panel_kind='qualification',stage='qualification')
    launch['panel']['cap_seconds']=80
    command=[v.replace(old,str(destination)) for v in launch['command']]
    for flag,value in [('--time-limit','74'),('--process-wall-time-limit','80')]:command[command.index(flag)+1]=value
    launch['command']=command;identity['stage']='qualification';write(OUT/'campaign_qualification/identity.json',identity)
    assert not destination.exists()
    tick,creation=inherited.inherited.process_origin();inherited.supervised(launch,identity,tick);finish_producer(launch,tick,creation)
    result=verify(launch,identity);write(OUT/'qualification_production.json',dict(PASS=True,
        qualified=result['arm'],identity_SHA=sha(OUT/'campaign_qualification/identity.json'),
        not_a_complete_performance_arm=True,cap=80,own_H=True,same_production_PE=True))
def no_model_and_entry():
    import paper_s2 as base
    configure();facts=[]
    for mode in ['off','uniform','conditional']:
        folder=TEMP/'no_model'/mode;(folder/'external/models').mkdir(parents=True,exist_ok=False)
        if mode!='off':write(folder/'round151_parameters.json',dict(mode=mode,GD=False,root_once=True,
            proof_root_unchanged=True,extra_root_LP=0,source_solves=0,new_columns=0))
        facts.append(dict(mode=mode,no_model_contract=cap_contract(folder,mode)['PASS']))
        out=TEMP/('dry_entry_'+mode)
        cmd=[PYTHON,'-B',ROOT/'scripts/paper_s2_penalty_propagation.py','--input',ROOT/'results/unified_exact_round137/inputs/N-B35-S.txt',
            '--out-dir',out,'--T','7200','--lambda','.15','--cap','2400','--seed','0','--json','--propagation',mode]
        p=subprocess.run(list(map(str,cmd)),env=environment(),capture_output=True,text=True,timeout=30)
        assert p.returncode==0,p.stderr;launch=json.loads(p.stdout)
        assert launch['dry_run'] and not out.exists() and not launch['GD'] and launch['matches_verified_PE'] and launch['matches_verified_DLL']
        expected=read(OUT/'confirmation_matrix.json')['groups'][0 if mode=='off' else 1]['launch']['command']
        if mode=='uniform':expected=expected[:-1]+['uniform']
        profile=read(ROOT/'config/gi_tbc_penalty_propagation_round151.json')
        assert base.normalize(launch['command'],profile)==base.normalize(expected,profile)
    for path in list((ROOT/'scripts').glob('round151*.py'))+[ROOT/'scripts/paper_s2_penalty_propagation.py']:
        ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    write(OUT/'qualification_entry.json',dict(PASS=True,facts=facts,actual_CLI_dry=True,
        no_model_own_H_completion_supported=True,syntax=True,Optimize=0,Native_load=0))
if __name__=='__main__':
    configure()
    if sys.argv[1]=='run':assert metered('qualification_production','diagnostic',[PYTHON,'-B',__file__,'arm'],200,600)==0
    elif sys.argv[1]=='entry':assert metered('qualification_entry','diagnostic',[PYTHON,'-B',__file__,'no_model_and_entry'],60,120)==0
    else:globals()[sys.argv[1]]()
