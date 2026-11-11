"""Recover only the two predeclared small-role own-H inlets, no old solver."""
from round162_common import *
import zipfile,shutil

def prepare():
    prior=WORK/'worktrees/round160/results/unified_exact_round160'
    matrix=read(prior/'confirmation_matrix.json');carrier=read(prior/'carrier_manifest.json')
    receipts=[]
    for pos in (5,7):
        launch=matrix['groups'][pos-1]['launch'];role=launch['id'];panel=launch['panel']
        assert role in ('K-20-S','R-X20-S-T1') and launch['R160_method']=='Eplus'
        dest=OUT/'inputs'/role;dest.mkdir(parents=True,exist_ok=True)
        source=prior/'inputs'/role/'instance.txt';shutil.copyfile(source,dest/'instance.txt')
        assert sha(dest/'instance.txt')==panel['input_sha256']
        archive=prior/'artifacts'/f'complete_{pos:03}.zip'
        expected=next(v for v in carrier['archives'] if v['path'].endswith(archive.name));assert sha(archive)==expected['SHA256']
        index=read(archive.with_name(archive.stem+'.members.json'));by={r['member']:r for r in index}
        prefix=f'results/unified_exact_round160/campaign_confirmation/{pos:03}/raw/'+launch['arm_id']
        members=[prefix+'/external/initial_witness.json',prefix+'/hga.csv.exchange/final.json',
                 f'results/unified_exact_round160/campaign_confirmation/{pos:03}/identity.json']
        values=[]
        with zipfile.ZipFile(archive) as z:
            for member in members:
                raw=z.read(member);assert hashlib.sha256(raw).hexdigest()==by[member]['SHA256']
                values.append(json.loads(raw))
        witness,exchange,identity=values
        assert abs(exchange['F']-witness['objective'])<1e-12
        assert [r['nodes'] for r in exchange['routes']]==[r['nodes'] for r in witness['routes']]
        lines=[str(len(witness['routes']))]
        for r in witness['routes']:
            ops={o['station']:o for o in r['operations']}
            lines.append(' '.join(map(str,[r['vehicle'],len(r['nodes']),*r['nodes']])))
            lines.append(' '.join(str(ops[i]['pickup']-ops[i]['drop']) for i in r['nodes'][1:-1]))
        (dest/'parent.txt').write_text('\n'.join(lines)+'\n',encoding='ascii');write(dest/'parent.json',witness)
        ref=dict(role=role,panel=panel,parent_J=witness['objective'],parent_stage='own H + R83, before root scope/helper; R160 Eplus control',
            parent_SHA256=sha(dest/'parent.txt'),H_seed=20260626,production_PE_SHA256=identity['candidate_binary_sha256'],
            fixed_commit='695ea68caad088a54ebed45b7d49360d12bd0e8d',delivery_commit='53e5c62fbcf6bc24898b7d5d3ecb755e4331ab0b',
            archive=expected,members=[by[m] for m in members],offline_development_only=True,old_producers=0)
        write(dest/'source.json',ref);receipts.append(ref)
    write(OUT/'small_input_manifest.json',dict(roles=receipts,old_producers=0,full_archive_extractions=0))
    print(json.dumps(dict(recovered=[r['role'] for r in receipts],old_Optimize=0)))

if __name__=='__main__':prepare()
