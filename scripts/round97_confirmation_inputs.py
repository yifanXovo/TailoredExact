"""One-shot deterministic reservation, no optimizer and no outcome-based redraw."""
import time
import round96_prepare as generator
from round96_prepare import ROOT,read,write,sha,citi
from round97_build import OUT
ROLES=[
    dict(id='C1',V=20,M=2,Q=25,geometry='offset_annulus',inventory='shortage',T_seconds=5400,cap_seconds=900,method_order=['P-GRB','FEEDBACK','OFF']),
    dict(id='C2',V=30,M=4,Q=15,geometry='bent_corridor',inventory='surplus',T_seconds=5400,cap_seconds=1800,method_order=['OFF','P-GRB','FEEDBACK']),
    dict(id='C3',V=50,M=4,Q=25,geometry='anisotropic_cloud',inventory='shortage',T_seconds=7200,cap_seconds=3600,method_order=['FEEDBACK','OFF','P-GRB']),
]
def main():
    started=time.perf_counter();dest=ROOT/'reference/round97_confirmation';assert not dest.exists()
    version='round97-native-confirmation-v1'
    recipe=dict(version=version,roles=ROLES,source_sha256=sha(__file__),inherited_generator_sha256=sha(generator.__file__),
        writer_sha256=sha(citi.__file__),reservation_sha256=sha(OUT/'confirmation_reservation.md'),optimizer_calls=0,
        policy='Retain all three inputs and outcomes. Never optimized before candidate freeze. No replacement, resizing, T changes or threshold fitting.')
    write(OUT/'confirmation_recipe.json',recipe);dest.mkdir();generator.VERSION=version;rows=[]
    for role in ROLES:
        obj=generator.landscape(role);path=dest/(role['id']+'.txt')
        with path.open('x',encoding='utf-8',newline='\n') as f:f.write(citi.instance_text(obj,role['M'],role['Q']))
        parsed=citi.parse_instance_mirror(path)
        assert parsed['M']==role['M'] and parsed['V']==role['V']
        total_initial=sum(obj['initial']);total_target=sum(obj['target'])
        if role['inventory']=='shortage':assert total_initial<total_target
        rows.append(dict(role,input_path=path.relative_to(ROOT).as_posix(),instance_path=path.relative_to(ROOT).as_posix(),
            input_sha256=sha(path),scenario_id=version+'-'+role['id'],pickup_seconds=60,drop_seconds=60,
            **{'lambda':.15},total_initial=total_initial,total_target=total_target))
    write(OUT/'confirmation_inputs.json',dict(roles=rows,recipe_sha256=sha(OUT/'confirmation_recipe.json'),
        optimizer_calls=0,wall_seconds=time.perf_counter()-started,status='All reserved, no confirmation Optimize yet.'))
    print('Generated and retained C1/C2/C3; zero Optimize')
if __name__=='__main__':main()
