"""Generate the frozen single-role recipe exactly once, no optimizer."""
from round100_common import *
import round96_prepare as generation
def main():
    recipe=read(OUT/'holdout_generation_recipe.json');selected=read(OUT/'candidate_freeze.json')
    assert selected['selected_arm']=='M-B' and selected['source_bindings']==bindings()
    assert sha(OUT/'candidate_freeze.json')==recipe['candidate_freeze_sha256']
    assert sha(generation.__file__)==recipe['landscape_source_sha256'] and sha(generation.citi.__file__)==recipe['writer_sha256']
    generation.VERSION=recipe['version'];r=recipe['role'];obj=generation.landscape(r)
    data=ROOT/'reference/round100_confirmation';data.mkdir(exist_ok=False)
    path=data/(r['id']+'.txt');lines=generation.citi.instance_text(obj,r['M'],r['Q_vector'][0]).splitlines()
    lines[0]=f'{r["V"]} {r["M"]} {r["Q_vector"]}'
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines)+'\n')
    parsed=generation.citi.parse_instance_mirror(path)
    assert parsed['V']==r['V'] and parsed['M']==r['M'] and parsed['Q']==r['Q_vector']
    assert len(set(map(tuple,parsed['points'])))==r['V']+1
    assert all(0<=b<=c and 0<d<=c and w>0 for b,d,c,w in zip(obj['initial'],obj['target'],obj['capacities'],obj['weights']))
    assert sum(obj['initial'])<sum(obj['target']), 'zero objective must be excluded by stock shortage and positive weights'
    p=dict(r,method_order=recipe['method_order'],input_path=path.relative_to(ROOT).as_posix(),instance_path=path.relative_to(ROOT).as_posix(),
        input_sha256=sha(path),scenario_id=recipe['version']+'-'+r['id'],pickup_seconds=60,drop_seconds=60,**{'lambda':.15},
        total_initial=sum(obj['initial']),total_target=sum(obj['target']),zero_excluded_by_stock_shortage=True)
    write(OUT/'holdout_protocol01.json',dict(roles=[p],recipe_sha256=sha(OUT/'holdout_generation_recipe.json'),
        candidate_freeze_sha256=sha(OUT/'candidate_freeze.json'),phase='design-isolated confirmation',reference_billing='one_finite_batch',
        optimizer_calls=0,maximum_formal_starts=3,maximum_formal_seconds=5400,no_reseed_or_replacement=True))
    print('H100 generated once; no Optimize, no outcomes inspected')
if __name__=='__main__':main()
