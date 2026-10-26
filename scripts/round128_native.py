"""Finite preformal native qualification, all starts and failures retained."""
from round128_common import *
from round128_campaign import prepare_group,execute
from round127_data import TRAIN
import copy,types
import round127_boundaries as boundary

def prepare():
    plans=[]
    for p0 in [TRAIN[0],TRAIN[2]]:
        for layer in ['E1','E2']:
            p=copy.deepcopy(p0);p.update(cap_seconds=90,pickup_seconds=60,drop_seconds=60,**{'lambda':.15},source='qualification',inventory='unspecified')
            name=f'qualification/native_{p["id"]}_{layer}'+('_final' if layer=='E2' else '')
            methods=['MB','P','MS2']+(['MD-R'] if p['id']=='S12' and layer=='E2' else [])
            if not (OUT/name/'identity.json').exists():prepare_group(name,layer,p,methods,0)
            plans.append(name)
    for case_name in ['zero_S_duration60','zero_S_duration3600']:
        p=dict(id=case_name,V=2,M=1,Q_vector=[1],T_seconds=60 if case_name.endswith('60') else 3600,
            cap_seconds=90,pickup_seconds=60,drop_seconds=60,**{'lambda':.15},source='qualification',inventory='unspecified',
            input_path=f'results/unified_exact_round128/qualification/boundaries/{case_name}/input.txt')
        p['input_sha256']=sha(ROOT/p['input_path']);name='qualification/native_'+case_name
        if not (OUT/name/'identity.json').exists():prepare_group(name,'E2',p,['MD-R'],0)
        plans.append(name)
    # The reviewer-found numerical relevance edge is a qualification toy,
    # never a formal role or a changed physical parameter in the panel.
    case=types.FunctionType(boundary.case.__code__,dict(vars(boundary),ROOT=ROOT,OUT=OUT),'case')
    path=OUT/'qualification/boundaries/tiny_positive_U/input.txt'
    if not path.exists():
        case('tiny_positive_U',[0,0],[1,1],[1],60)
        text=path.read_text().replace('weights = [0, 1, 1]','weights = [0, 1e-08, 1e-08]')
        path.write_text(text,encoding='utf-8')
    p=dict(id='tiny_positive_U',V=2,M=1,Q_vector=[1],T_seconds=60,pickup_seconds=60,drop_seconds=60,**{'lambda':.15},
        input_path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),cap_seconds=90,source='qualification',inventory='unspecified')
    name='qualification/native_tiny_positive_U'
    if not (OUT/name/'identity.json').exists():prepare_group(name,'E2',p,['MD-R'],0)
    plans.append(name)
    p=copy.deepcopy(TRAIN[2]);p.update(cap_seconds=90,pickup_seconds=60,drop_seconds=60,**{'lambda':.15},source='qualification',inventory='unspecified')
    name='qualification/native_R98-C2_MD_R_open_final'
    if not (OUT/name/'identity.json').exists():prepare_group(name,'E2',p,['MD-R'],0)
    plans.append(name)
    write(OUT/'qualification/native_plan.json',dict(groups=plans,formal_performance=False,no_new_evaluation_inputs=True,
        nominal_upper_seconds=17*90,qualification_soft=1200,authorized_limit=3000,
        extra_medium_MD_R='Finite native return-contract smoke for a possibly time-limited open root after the independent review found the near-equality closure hazard; no performance selection'))
    print(json.dumps(dict(prepared=plans)))

def run():
    for name in read(OUT/'qualification/native_plan.json')['groups']:
        if (OUT/name/'reconstructed.json').exists():continue
        label=name.replace('/','_');attempt=len(list((OUT/'fees').glob(label+'*')))+1
        assert metered(label+f'_{attempt:02d}','qualification',[PYTHON,ROOT/'scripts/round128_campaign.py',name],reservation=15600+1800)==0
    print('NATIVE_QUALIFICATION_SEALED')

if __name__=='__main__':{'prepare':prepare,'run':run}[sys.argv[1]]()
