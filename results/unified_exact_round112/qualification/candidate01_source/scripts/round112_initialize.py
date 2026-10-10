from round112_common import *
import hashlib, shutil, struct

ROLES=[]
for no,(id,path,digest,v,m,q,T,cap,order) in enumerate([
 ('F2','round86_unadapted_confirmation/F2.txt','ebdf99e77dc9dcc57946970fa6d7e1cdf2defdcd277562a454d4889c716b645e',20,2,[30,30],3600,1200,['P-GRB','P-S','ENS-C','M-B']),
 ('R98-C2','round98_confirmation/C2.txt','07d0964c87b534254e6bf2957911859a6a2bd73e377211728b7e65f44294fc76',30,3,[20,25,30],7200,1800,['P-S','M-B','P-GRB','ENS-C']),
 ('R108-L48','round108_confirmation/L48.txt','8ce2bceb8de415a1ff62ea78790456ee54e3542ce57714a7a53505d30ea54755',48,4,[30]*4,18000,1800,['ENS-C','P-GRB','M-B','P-S']),
 ('G50-C1','round109_geographic/G50-C1.txt','5740d09bf218cf6921cee6e60198f673151d6426fbcb0840259647129f3c4ed5',50,4,[30]*4,7200,1800,['M-B','ENS-C','P-S','P-GRB']),
 ('G100-R2','round109_geographic/G100-R2.txt','b3f3a1270f062e9f3af64d5b00392f51821bb775818edc6cd383fcd62550618f',100,8,[30]*8,18000,3600,['P-GRB','ENS-C','P-S','M-B'])],1):
    ROLES.append(dict(number=no,id=id,input_path='reference/'+path,input_sha256=digest,V=v,M=m,Q_vector=q,T_seconds=T,
        cap_seconds=cap,method_order=order,pickup_seconds=60,drop_seconds=60,**{'lambda':.15},gurobi_seed=0,panel_kind='main'))

def initialize():
    OUT.mkdir(parents=True,exist_ok=True)
    for p in ROLES:
        assert sha(ROOT/p['input_path'])==p['input_sha256'];p['input_bytes']=(ROOT/p['input_path']).stat().st_size
    h=dict(id='H100',input_path='reference/round100_confirmation/H100.txt',input_sha256='04cfc75a36585eddea81693964eed9ef4c207e62b687e955e63fd4fb00d7bf71',
        V=20,M=2,Q_vector=[13,21],T_seconds=5100,cap_seconds=120,method_order=['P-GRB','P-S','ENS-C','M-B'],pickup_seconds=60,drop_seconds=60,**{'lambda':.15},gurobi_seed=0,panel_kind='qualification')
    micros=[]
    for id,path,T,pick,drop in [('positive5over24','tests/data/round59_tiny.txt',3,0,0),('ownzero','tests/data/round24_toy_V2_M1.txt',60,60,60)]:
        micros.append(dict(id=id,input_path=path,input_sha256=sha(ROOT/path),V=3 if id.startswith('positive') else 2,M=1,
            Q_vector=[3] if id.startswith('positive') else [1],T_seconds=T,cap_seconds=60,method_order=['P-GRB','P-S'] if id.startswith('positive') else ['P-S'],
            pickup_seconds=pick,drop_seconds=drop,**{'lambda':.15},gurobi_seed=0,panel_kind='qualification'))
    assert sha(ROOT/h['input_path'])==h['input_sha256']
    write(OUT/'input_manifest.json',dict(roles=ROLES,qualification_roles=[h]+micros,geographies_added=0,seeds_added=0))
    from round109_prepare import COMMON
    write(OUT/'protocol.json',dict(round=112,base=BASE,roles=ROLES,common=COMMON,formal_arms=20,formal_nominal_seconds=40800,
        total_start_limit=56,total_outer_seconds_limit=48000,qualification_start_limit=20,qualification_outer_seconds_limit=1800,
        group_outer_administrative_reserve=120,primary_benchmark='cold P-GRB',default='ENS-C',
        pairs=[['ENS-C','P-GRB'],['M-B','P-GRB'],['P-S','P-GRB'],['ENS-C','P-S'],['M-B','P-S'],['M-B','ENS-C']],
        comparison_policy='unchanged R111 materiality/severity, signed gap, full clocks; no new adoption gate',
        attribution_rules=['INCOMPLETE_ATTRIBUTION','POSITIVE_ONLY_OBSERVED','NO_POSITIVE_INCREMENT_OBSERVED','MIXED_INCREMENT_OBSERVED'],
        backend_exposure_required=True,zero_backend_not_exposed=True,zero_tolerance=1e-7,cover_tolerance=1e-7,
        full_goal_SHA=sha(OUT/'goal.md'),startup_semantic_fields=['seed','logical steps','accepted actions','integer operations','original inventory','complete capacity-assigned fleet'],
        startup_metadata_exclusions=['timestamps and elapsed durations','file paths','method identity labels','witness hashes binding those labels'],
        no_formal_retry=True,no_new_geography_lambda_seed_grid=True))
    q=OUT/'qualification';q.mkdir(exist_ok=True)
    lines=[]
    for p in ROLES+[h]+micros:
        lines.append('\t'.join(map(str,[p['input_path'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],q/'reference'/p['id']])))
    (q/'reference_batch.tsv').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    write(q/'plan.json',dict(planned_starts=12,reference_wrapper_and_child=2,H100_wrapper_and_children=5,micro_positive_wrapper_and_children=3,zero_wrapper_and_child=2,
        remaining_qualification_reserve_starts=8,nominal_CLI_seconds=660,reference_outer_cap=180,CLI_groups_outer_reserve=120,
        positive_micro_expected_objective=5/24,positive_micro_zero_handling_is_not_zero_objective=True,zero_micro_initial_Y_equals_D=True))
    print('five roles, physical micros and budget preregistered; native launches=0')

def freeze():
    old=read(ROOT/'results/unified_exact_round111/production_identity.json')
    b=bindings();changes={p:dict(old=h,new=b.get(p)) for p,h in old['source_bindings'].items() if b.get(p)!=h}
    binary=PE.read_bytes();pos=struct.unpack_from('<I',binary,0x3c)[0];optional=pos+24
    compiler=Path('D:/msys64/ucrt64/bin/g++.exe')
    write(OUT/'production_identity.json',dict(production_PE_SHA=sha(PE),DLL_SHA=sha(DLL),source_bindings=b,compiler=str(compiler),compiler_SHA=sha(compiler),
        inherited_PE_SHA=old['production_PE_SHA'],inherited_source_changes=changes,additional_sources={p:h for p,h in b.items() if p not in old['source_bindings']},
        build_type='',CXX_flags='',stack_reserve=struct.unpack_from('<Q',binary,optional+72)[0],stack_commit=struct.unpack_from('<Q',binary,optional+80)[0],
        all_four_methods_same_PE=True,measured_source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()))
    print('final candidate source/PE/DLL frozen')

if __name__=='__main__':{'initialize':initialize,'freeze':freeze}[sys.argv[1]]()
