"""One-time pre-development recipe and inputs; reads no solver feedback."""
from round106_common import *
import round96_prepare as generation

VERSION='round106-structural-candidate-confirmation-v1'
NEW=[dict(id='N36',V=36,M=3,Q_vector=[24,30,36],geometry='three_clusters',inventory='shortage',T_seconds=7200,cap_seconds=5400),
     dict(id='S12',V=12,M=2,Q_vector=[8,12],geometry='bent_corridor',inventory='surplus',T_seconds=3600,cap_seconds=900)]
def run():
    recipe=dict(version=VERSION,roles=NEW,seed='SHA256(version|id|field), first8 bytes /2^64',
        generator_SHA=sha(generation.__file__),writer_SHA=sha(generation.citi.__file__),source_SHA=sha(__file__),
        retained_tail=dict(id='F5',input_path='reference/round86_unadapted_confirmation/F5.txt',
            V=50,M=4,Q_vector=[30]*4,T_seconds=7200,cap_seconds=5400),
        no_reseed_replace_resize_or_T_adjustment=True,Optimize_calls=0,generated_before_development_feedback=True)
    write(OUT/'confirmation_generation_recipe.json',recipe)
    data=ROOT/'reference/round106_confirmation';data.mkdir(exist_ok=False);generation.VERSION=VERSION;roles=[]
    for r in NEW:
        obj=generation.landscape(r);p=data/(r['id']+'.txt');lines=generation.citi.instance_text(obj,r['M'],r['Q_vector'][0]).splitlines()
        lines[0]=f'{r["V"]} {r["M"]} {r["Q_vector"]}'
        with p.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines)+'\n')
        parsed=generation.citi.parse_instance_mirror(p);assert parsed['Q']==r['Q_vector']
        assert all(0<=b<=c and 0<d<=c for b,d,c in zip(obj['initial'],obj['target'],obj['capacities']))
        roles.append(dict(r,input_path=p.relative_to(ROOT).as_posix(),input_sha256=sha(p),scenario_id=VERSION+'-'+r['id']))
    tail=recipe['retained_tail'];roles.insert(0,dict(tail,input_sha256=sha(ROOT/tail['input_path']),scenario_id='round86-unadapted-varied-structures-v1_F5'))
    for i,r in enumerate(roles):r.update(pickup_seconds=60,drop_seconds=60,**{'lambda':.15},method_order=[['P-GRB','ENS-C','EVENT-STRUCT'],['ENS-C','EVENT-STRUCT','P-GRB'],['EVENT-STRUCT','P-GRB','ENS-C']][i])
    write(OUT/'confirmation_protocol.json',dict(roles=roles,process_shutdown_margin_seconds=30,
        recipe_SHA=sha(OUT/'confirmation_generation_recipe.json'),nominal_seconds=35100,maximum_formal_children=9,
        status='SEALED_NOT_ADMITTED_NOT_EXECUTED',Optimize_calls=0,
        admission='Complete eight-arm development required. At least one complete original-problem certificate with credible cost benefit/tradeoff relative to P/ENS, actual new mechanism exposure, no important protected-certificate loss without measured compensation. LB/cuts/gap alone never suffice.',
        retention='All generated inputs kept; no feedback-based redraw; started matched groups completed even if negative.',
        cancellation='Sufficient complete narrow negative development may cancel all unstarted confirmation groups. Cancellation is untested scope, never a confirmation result.'))
    old=read(ROOT/'results/unified_exact_round105/control01_protocol.json')['roles'];dev=[]
    for r in old:
        q=dict(r);q['method_order']=['P-GRB','ENS-C','EVENT-STRUCT'] if q['id']=='F2' else ['ENS-C','EVENT-FULL','EVENT-CORE','P-GRB','EVENT-STRUCT'];dev.append(q)
    write(OUT/'development_protocol.json',dict(roles=dev,phase='eight complete serial development arms after independent admission',
        process_shutdown_margin_seconds=30,nominal_seconds=12600,maximum_formal_children=8,
        runtime_policy='uniform single MIPSOL/lazy master; no AM for EVENT; FULL/CORE new A/B disabled; STRUCT new A/B enabled, native fallback FULL; fixed car order; one monotonic startup deadline; no instance/size/stagnation dispatch',
        master='R105 global VD-P/F0, all necessary rows retained, only x/load integer types relaxed, self-paid non-strict U0 domain',
        confirmation_protocol_SHA=sha(OUT/'confirmation_protocol.json'),decision_after_all_eight=True,
        allow_one_evidence_based_substantive_revision=True))
    print(json.dumps(dict(generated_once=[r['id'] for r in NEW],Optimize_calls=0)))

if __name__=='__main__':run()
