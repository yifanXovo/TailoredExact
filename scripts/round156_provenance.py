"""Bind only the old inputs/evidence actually used, without old archive I/O.

Run after the complete panel, through the serial outer meter. Large historical
Q/pool carriers are neither downloaded nor repacked. Fixed Git metadata and
selected member indexes resolve the retained scientific source chain.
"""
import ast,gzip
from round156_common import *

SCIENCE137='e735c3447eb1443713c700942d873de1783a4a26'

def run():
    from round100_idle import ensure_idle
    configure();ensure_idle();own=os.environ['ROUND140_METERED_PARENT_LABEL']
    assert [v['label'] for v in budget()['unclosed']]==[own]
    dependencies={};providers={};archives={};indexes={}

    def relative(path):
        path=Path(path)
        if path.is_absolute():
            for tree in [ROOT,PRIOR]:
                if path.is_relative_to(tree):return path.relative_to(tree).as_posix(),path
            raise AssertionError(('outside known trees',str(path)))
        return path.as_posix(),ROOT/path

    def raw_git(commit,name):
        return subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=ROOT)

    def attach(item,actual,why,allow_eol=False):
        name=item['member'];data=actual.read_bytes();digest=hashlib.sha256(data).hexdigest()
        if digest!=item['SHA256']:
            assert item['resolution']=='fixed Git file' and allow_eol,(name,digest,item['SHA256'])
            raw=raw_git(item['commit'],name)
            if raw.replace(b'\n',b'\r\n')==data:transform='LF_to_CRLF'
            elif raw.replace(b'\r\n',b'\n')==data:transform='CRLF_to_LF'
            else:raise AssertionError((name,'unexplained source bytes'))
        else:
            assert len(data)==item['bytes'];transform='identity'
        item=dict(item,working_SHA256=digest,working_bytes=len(data),checkout_transform=transform)
        if name in dependencies:
            assert dependencies[name]['SHA256']==item['SHA256'] and dependencies[name]['working_SHA256']==digest
            if why not in dependencies[name]['used_for']:dependencies[name]['used_for'].append(why)
        else:dependencies[name]=dict(item,used_for=[why])
        return dependencies[name]

    def fixed(path,commit,why,allow_eol=False):
        name,actual=relative(path);raw=raw_git(commit,name)
        item=dict(member=name,SHA256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),commit=commit,resolution='fixed Git file')
        return attach(item,actual,why,allow_eol)

    for number,commit in [(137,SCIENCE137),(154,SCIENCE154),(155,SCIENCE155)]:
        name=f'results/unified_exact_round{number}/'+('raw_archive_manifest.json' if number==137 else 'public_manifest.json')
        raw=raw_git(commit,name);manifest=json.loads(raw)
        providers[number]=dict(commit=commit,path=name,SHA256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
        for archive in manifest['archives']:archives[(number,archive['name'])]=dict(commit=commit,**archive)
        for p in manifest.get('files',[]):
            indexes[(number,p['path'])]=dict(member=p['path'],SHA256=p['SHA256'],bytes=p['bytes'],commit=commit,resolution='fixed Git file')

    used_archives=set()
    def old(path,number,why):
        name,actual=relative(path);key=(number,name)
        if key not in indexes:
            parts=Path(name).parts
            campaign='campaign' if number==137 else 'campaign_confirmation'
            assert campaign in parts,(number,name)
            position=parts[parts.index(campaign)+1]
            label=('campaign_' if number==137 else 'complete_arm_')+position+'.zip'
            archive=archives[(number,label)];used_archives.add((number,label))
            index=archive['member_index'];raw=raw_git(archive['commit'],index['path'])
            assert hashlib.sha256(raw).hexdigest()==index['SHA256'] and len(raw)==index['bytes']
            for member in json.loads(gzip.decompress(raw)):
                membername=member.get('member',member.get('path'))
                indexes[(number,membername)]=dict(member=membername,SHA256=member['SHA256'],bytes=member['bytes'],
                    commit=archive['commit'],resolution='fixed archive member',archive_reference=f'round{number}/{label}')
        assert key in indexes,(number,name)
        item=indexes[key]
        if 'archive_reference' in item:used_archives.add((number,item['archive_reference'].split('/',1)[1]))
        return attach(item,actual,why,allow_eol=item['resolution']=='fixed Git file')

    starts=read(OUT/'starting_inventory.json')
    for role,record in starts.items():
        number=record['prior_round'];why=role+' saved original-objective starting scope/interval/true stocks'
        for name in ['source','pricing','helper_result']:old(record[name],number,why)
        folder=Path(record['helper_result']).parent
        old(folder/'source.json',number,why+' and source binding')
        old(folder/'pricing/call.json',number,why+' and original RN stop/settings')
        fixed(record['input'],SCIENCE137,role+' original physical input')
    for number,commit in [(154,SCIENCE154),(155,SCIENCE155)]:
        for name in ['confirmation_matrix.json','source_manifest.json','reuse_index.json','candidate_manifest.json','helper_manifest.json']:
            fixed(PRIOR/f'results/unified_exact_round{number}'/name,commit,'inherited identity/recovery chain',True)
    fixed(PRIOR/'results/unified_exact_round155/reports/common_checkpoints.json',SCIENCE155,'unaltered prior checkpoint export',True)
    for group in read(PRIOR/'results/unified_exact_round155/confirmation_matrix.json')['groups']:
        dest=Path(group['launch']['destination']);why=group['launch']['arm_id']+' exact time-origin correction'
        names=['process_start_marker.json','producer_receipt.json','observations.json','round154_endpoint.json',
               'round153_control_audit.json','audit.json']
        if group['launch']['R154_method']=='E':names.append('round154_control_audit.json')
        for name in names:
            old(dest/name,155,why)
    k=read(OUT/'producer_checks/fresh_K20_v1/source_identity.json')
    old(k['source'],137,'preselected K20 first actual Native root scope')
    old(Path(k['original_launch']['destination'])/'observations.json',137,'K20 saved first actual Native call and chronological root identity')
    fixed('results/unified_exact_round132/inputs/K-20-S.txt',SCIENCE137,'preselected historical CITI K20 input')
    fixed(PRIOR/'results/unified_exact_round137/matrix_frozen.json',SCIENCE137,'K20 original physical role and own-H identity',True)
    fixed('results/unified_exact_round94/preregistration.json',BASE,'read-only inherited import prerequisite',True)

    pending=list((ROOT/'scripts').glob('round156*.py'));seen=set();fixed_python={}
    while pending:
        path=pending.pop();name=path.relative_to(ROOT).as_posix()
        if name in seen:continue
        seen.add(name)
        if not path.name.startswith('round156'):
            ref=fixed(path,BASE,'static Python dependency of Round156 source',True)
            fixed_python[name]=dict(commit=BASE,SHA256=sha(path),reference_SHA256=ref['SHA256'],checkout_transform=ref['checkout_transform'])
        tree=ast.parse(path.read_text(encoding='utf-8-sig'),filename=str(path))
        for node in ast.walk(tree):
            names=[v.name for v in node.names] if isinstance(node,ast.Import) else ([node.module] if isinstance(node,ast.ImportFrom) and node.module else [])
            for module in names:
                base=module.split('.')[0]
                if (ROOT/'scripts'/(base+'.py')).is_file():pending.append(ROOT/'scripts'/(base+'.py'))
    identity=read(OUT/'candidate_manifest.json');measured=identity['source_commit']
    assert sha(identity['production_PE'])==identity['production_PE_SHA'] and sha(DLL)==DLL_SHA
    for name,digest in identity['source_hashes'].items():
        assert sha(ROOT/name)==digest and hashlib.sha256(raw_git(measured,name)).hexdigest()==digest
    for method in ['E','Eplus']:
        manifest=read(OUT/f'helper_manifest_{method}.json')
        assert manifest['source_commit']==measured
        for name,digest in manifest['helper_dependencies'].items():
            assert sha(ROOT/name)==digest
            if not Path(name).name.startswith('round156') and name not in fixed_python:
                ref=fixed(name,BASE,'declared exact helper dependency',True)
                fixed_python[name]=dict(commit=BASE,SHA256=digest,reference_SHA256=ref['SHA256'],checkout_transform=ref['checkout_transform'])
    snapshots=[]
    for path in sorted((OUT/'engineering/source_snapshots').glob('*.json')):
        snapshot=read(path)
        for digest in snapshot['files'].values():assert sha(OUT/'engineering/source_bytes'/f'{digest}.txt')==digest
        snapshots.append(dict(label=path.stem,path=path.relative_to(ROOT).as_posix(),SHA256=sha(path),files=snapshot['files']))
    write(OUT/'reuse_index.json',dict(UTC=utc(),providers=providers,dependencies=[dependencies[k] for k in sorted(dependencies)],
        archives={f'round{n}/{label}':archives[(n,label)] for n,label in sorted(used_archives)},
        scope='Only actual starting prices, complete inputs, original time-chain evidence and source dependencies.',
        fixed_R137_science=SCIENCE137,fixed_R154_science=SCIENCE154,fixed_R155_science=SCIENCE155,
        old_carriers_downloaded=0,old_carriers_repacked=0,old_producers_run=0,
        transitive_resolution='Other prior paths resolve through the fixed provider manifests and their fixed reuse indexes.'))
    write(OUT/'source_manifest.json',dict(UTC=utc(),production_measured_source_commit=measured,
        candidate_manifest_SHA=sha(OUT/'candidate_manifest.json'),PE=identity['production_PE'],PE_SHA256=identity['production_PE_SHA'],
        DLL=str(DLL),DLL_SHA256=DLL_SHA,production_build_manifest=identity,
        source_base=BASE,python=str(PYTHON),python_SHA=sha(PYTHON),
        current_new_sources={p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT/'scripts').glob('round156*.py'))},
        executed_new_source_snapshots=snapshots,fixed_python_dependencies=fixed_python,
        snapshot_enumeration_scope='All launch snapshots present at this provenance pass, including its own. Any later bounded reader keeps an additional immutable per-label snapshot in engineering/source_snapshots; the final review names its own snapshot.',
        inherited_python_scope='Static local imports reachable from Round156 modules plus exact declared helper dependencies; actual bytes and EOL transforms, not an arbitrary dynamic import trace.',
        prebuild_helpers='Actual dependency bytes and per-launch source snapshots bind the precommit checks; their exact manifests are preserved beside each successful check.',
        latest_source_not_relabelled_as_every_measured_version=True,source_bytes_immutable_per_measured_launch=True,
        public_runtime_policy='Exact new PE retained locally with build/source identity. Commercial DLL and existing interpreters are read-only references, not redistributed.',
        outer_meter_label=own))
    print(json.dumps(dict(dependencies=len(dependencies),referenced_old_archives=len(used_archives),
        fixed_python_dependencies=len(fixed_python),executed_snapshots=len(snapshots),old_carrier_downloads=0)),flush=True)

if __name__=='__main__':run()
