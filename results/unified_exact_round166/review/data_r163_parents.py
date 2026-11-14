"""Recover the six historical B parents for offline qualification only."""
from pathlib import Path
import hashlib,json,zipfile
from data_recover import parse_input,physical,sha

ROOT=Path(__file__).resolve().parents[3]
DEST=ROOT/'results/unified_exact_round166/qualification/parents'
DEST.mkdir(parents=True,exist_ok=True)
out=ROOT/'results/unified_exact_round163'
arms=json.loads((out/'reports/complete_arms.json').read_text())
matrix=json.loads((out/'matrix_frozen.json').read_text())
manifest=json.loads((out/'carrier_manifest.json').read_text())
inputs=json.loads((out/'input_manifest.json').read_text())
carrier=manifest['archives'][0];archive=ROOT/carrier['path']
raw=archive.read_bytes();assert sha(raw)==carrier['SHA256']
records=[]
with zipfile.ZipFile(archive) as z:
 for ident in ['R163-C20-S','R163-B20-B','R163-X20-S','R163-C35-U','R163-B35-S','R163-X35-S']:
  arm=next(a for a in arms if a['id']==ident and a['R163_method']=='B')
  role=next(a for a in inputs['roles'] if a['id']==ident)
  rel=arm['destination'].replace('\\','/');rel=rel[rel.index('results/'):]
  member=rel+'/audit.json';b=z.read(member);audit=json.loads(b)
  assert sha(b)==arm['audit_SHA']
  assert audit['passed'] and audit['implementation_qualified'] and audit['evidence_complete']
  a,input_raw=parse_input(role);phys=physical(a,role,audit['physical']['routes'])
  assert phys['Y']==audit['physical']['Y'] and abs(phys['F']-arm['U'])<1e-12
  parts=[str(a['m'])]
  for rt in phys['routes']:
   parts.append(' '.join(map(str,[rt['vehicle'],len(rt['nodes']),*rt['nodes']])))
   ops={o['station']:o for o in rt['operations']}
   parts.append(' '.join(str(ops[i]['pickup']-ops[i]['drop']) for i in rt['nodes'][1:-1]))
  txt='\n'.join(parts)+'\n';p=DEST/(ident+'.txt');p.write_text(txt,encoding='utf-8')
  records.append(dict(id=ident,parent_path=p.relative_to(ROOT).as_posix(),parent_SHA256=sha(p.read_bytes()),input_path=role['input_path'],input_SHA256=sha(input_raw),lambda_value=role['lambda'],T_seconds=role['T_seconds'],U=arm['U'],physical_G=phys['G'],physical_P=phys['P'],source_arm_id=arm['arm_id'],source_method='B',source_seed=arm['seed'],source_archive=carrier['path'],source_archive_SHA256=sha(raw),source_member=member,source_member_SHA256=sha(b),physical_verified=True,full_fleet=phys,offline_only=True,formal_performance_start_forbidden=True))
(DEST/'source_manifest.json').write_text(json.dumps(dict(schema='round166-offline-parent-fleets-v1',format='M; for every vehicle: vehicle n node_0 ... node_(n-1), followed by pickup-minus-drop for each interior node (whitespace separated)',records=records,new_Optimize=0,offline_only=True),indent=2)+'\n')
print(json.dumps([{k:r[k] for k in ['id','U','parent_SHA256']} for r in records],indent=2))
