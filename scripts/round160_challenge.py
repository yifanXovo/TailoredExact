"""One fixed late-parent challenge and one finite C++ semantic bridge."""
from round160_common import *
from round157_fleet import verify

def run():
    role='N-B35-S';source=read(OUT/'inputs'/role/'source.json');p=source['panel']
    family=read(WORK/'worktrees/round157/results/unified_exact_round157/inventory_families.json')[role]
    witness=family['positive_control']['witness'];checked=verify(source['data'],witness);assert checked['original_T_feasible']
    target=OUT/'qualification/late_parent';target.mkdir(parents=True,exist_ok=False);write(target/'parent.json',witness)
    lines=[str(len(witness['routes']))]
    for r in witness['routes']:
        ops={o['station']:o for o in r['operations']}
        lines.append(' '.join(map(str,[r['vehicle'],len(r['nodes']),*r['nodes']])))
        lines.append(' '.join(str(ops[i]['pickup']-ops[i]['drop']) for i in r['nodes'][1:-1]))
    (target/'parent.txt').write_text('\n'.join(lines)+'\n')
    chosen=next(r['selected_owner_event'] for r in read(OUT/'trajectory_analysis_v1.json')['sources'] if r['role']==role)
    records=[]
    for label,parent in [('late',target/'parent.txt'),('bridge',Path(str(ROOT/chosen['parent_path'])+'.txt'))]:
        out=target/label;command=[PE,OUT/'inputs'/role/'instance.txt',p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],
                                parent,out,300,512,1,'joint',*chosen['B']]
        subprocess.run(list(map(str,command)),env=meter.environment(),check=True)
        result=read(out/'final.json');v=verify(source['data'],result);assert v['original_T_feasible']
        records.append(dict(kind=label,summary=read(out/'summary.json'),physical=v,command=list(map(str,command))))
    original=read((ROOT/chosen['parent_path']).parent/'positive/result.json')
    assert abs(records[1]['summary']['J']-original['best_J'])<1e-12
    write(target/'result.json',dict(PASS=True,role=role,B=chosen['B'],original_late_J=checked['J'],
        source='R157 positive_control / R159 same physical reference',source_witness_SHA=family['positive_control']['SHA'],
        fixed_science='9889473a9b64c749ea8841bac1d38fec8be21d96',records=records,
        semantic_bridge_same_block_best_J=True,not_complete_method_samples=True))

if __name__=='__main__':run()
