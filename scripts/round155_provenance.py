"""Build fixed-commit/member references without restoring old large archives.

Run this metadata/hash verification only when the serial experimental lane
is idle, through the normal outer meter. It never downloads or runs a producer.
"""
from round155_common import *
import ast

def diagnose_checkout(label='source_checkout_diagnostic_v1',name='scripts/round111_seed_audit.py'):
    configure();target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False)
    actual=(ROOT/name).read_bytes();fixed=subprocess.check_output(['git','show',f'{BASE}:{name}'],cwd=ROOT)
    result=dict(path=name,commit=BASE,working_SHA256=hashlib.sha256(actual).hexdigest(),
        fixed_SHA256=hashlib.sha256(fixed).hexdigest(),working_bytes=len(actual),fixed_bytes=len(fixed),
        working_CRLF=actual.count(b'\r\n'),fixed_CRLF=fixed.count(b'\r\n'),
        exact_bytes_equal=actual==fixed,
        exact_fixed_LF_to_CRLF_reconstruction=fixed.replace(b'\n',b'\r\n')==actual,
        exact_fixed_CRLF_to_LF_reconstruction=fixed.replace(b'\r\n',b'\n')==actual,
        source_SHA=sha(__file__),Optimize=0,Native_model_reads=0,
        files_changed=False,not_an_admission_of_unexplained_source_differences=True)
    write(target/'result.json',result);print(json.dumps(result),flush=True)


def run():
    from round100_idle import ensure_idle
    configure();ensure_idle();own=os.environ['ROUND140_METERED_PARENT_LABEL']
    assert [v['label'] for v in budget()['unclosed']]==[own]
    providers={};members={};archives={};dependencies={};transitive={}
    for round_name,commit in [('round153',SCIENCE153),('round154',SCIENCE154)]:
        manifest_path=f'results/unified_exact_{round_name}/public_manifest.json'
        raw=subprocess.check_output(['git','show',f'{commit}:{manifest_path}'],cwd=ROOT)
        manifest_file=ROOT/manifest_path
        assert hashlib.sha256(raw).hexdigest()==sha(manifest_file),(commit,manifest_path)
        manifest=read(manifest_file)
        providers[round_name]=dict(commit=commit,path=manifest_path,SHA256=sha(manifest_file))
        reuse_path=ROOT/f'results/unified_exact_{round_name}/reuse_index.json'
        reuse_SHA=sha(reuse_path)
        reuse_raw=subprocess.check_output(['git','show',f'{commit}:{reuse_path.relative_to(ROOT).as_posix()}'],cwd=ROOT)
        assert hashlib.sha256(reuse_raw).hexdigest()==reuse_SHA,(commit,str(reuse_path))
        for item in read(reuse_path)['dependencies']:
            member=item.get('member',item.get('path'));assert member
            transitive.setdefault(member,dict(item,transitive_reference_index=dict(
                path=reuse_path.relative_to(ROOT).as_posix(),SHA256=reuse_SHA,commit=commit)))
        for item in manifest['files']:
            members.setdefault((round_name,item['path']),dict(member=item['path'],SHA256=item['SHA256'],
                bytes=item['bytes'],commit=commit,resolution='fixed Git file'))
        for archive in manifest['archives']:
            index=ROOT/archive['member_index']['path'];assert sha(index)==archive['member_index']['SHA256']
            archive_id=round_name+'/'+archive['name']
            archives[archive_id]=dict(commit=commit,**archive)
            for item in load_gz(index):
                key=(round_name,item['member']);assert key not in members
                members[key]=dict(member=item['member'],SHA256=item['SHA256'],bytes=item['bytes'],commit=commit,
                    resolution='fixed archive member',archive_reference=archive_id)
    def existing(name,role):
        path=Path(name)
        if path.is_absolute():path=path.relative_to(ROOT)
        name=path.as_posix()
        if name.startswith('results/unified_exact_round155/'):return
        provider='round154' if name.startswith('results/unified_exact_round154/') else 'round153'
        key=(provider,name)
        item=dict(members[key]) if key in members else dict(transitive[name])
        assert item['commit'] and item['SHA256']
        actual=ROOT/name
        assert actual.is_file() and sha(actual)==item['SHA256'] and actual.stat().st_size==item['bytes'],name
        if name in dependencies:
            assert dependencies[name]['SHA256']==item['SHA256']
            if role not in dependencies[name]['used_for']:dependencies[name]['used_for'].append(role)
        else:dependencies[name]=dict(item,used_for=[role])
    def fixed_git(name,commit,role,allow_checkout_eol=False):
        path=Path(name)
        if path.is_absolute():path=path.relative_to(ROOT)
        name=path.as_posix();raw=subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=ROOT)
        digest=hashlib.sha256(raw).hexdigest();actual=(ROOT/name).read_bytes();transform='identity'
        if actual!=raw:
            assert allow_checkout_eol,(name,'working/fixed Git bytes differ')
            if raw.replace(b'\n',b'\r\n')==actual:transform='LF_to_CRLF'
            elif raw.replace(b'\r\n',b'\n')==actual:transform='CRLF_to_LF'
            else:raise AssertionError((name,'unexplained inherited source-byte difference'))
        dependencies[name]=dict(member=name,SHA256=digest,bytes=len(raw),commit=commit,
            resolution='fixed Git file',used_for=[role],checkout_transform=transform,
            working_SHA256=hashlib.sha256(actual).hexdigest(),working_bytes=len(actual))
        return dependencies[name]
    starts=read(OUT/'starting_pools.json')
    for role,start in starts.items():
        existing(start['result'],role+' starting full pool/supports/interval')
        existing(start['Q'],role+' complete original free Q')
        result=read(start['result'])
        for support in result['supports']:
            if support.get('price_path'):existing(support['price_path'],role+' inherited support price')
    # The complete prior manifests/reuse indexes resolve every transitive old
    # certificate/price/source reference. Only selected actual anchors are
    # repeated here; no historical archive bytes are packed or downloaded.
    for round_name,commit in [('round153',SCIENCE153),('round154',SCIENCE154)]:
        for name in ['reuse_index.json','source_manifest.json','candidate_manifest.json','candidate_decision.json']:
            existing(f'results/unified_exact_{round_name}/{name}','transitive inherited identity and proof references')
    existing('results/unified_exact_round154/qualification/goal_stop_v1/result.json','inherited oracle qualification')
    identity=read(OUT/'production_identity.json')
    existing(identity['helper_manifest'],'unchanged paid own-floor helper identity')
    for path in sorted((OUT/'qualification').glob('*/result.json')):
        record=read(path)
        for phase in record.get('phases',[]):
            witness=phase.get('upper_witness')
            if witness and witness.get('path'):existing(witness['path'],'actual retained upper witness')
    inputs={}
    for group in read(OUT/'confirmation_matrix.json')['groups']:
        command=group['launch']['command'];name=command[command.index('--input')+1]
        inputs[name]=group['launch']['id']
    for name,role in inputs.items():fixed_git(name,SCIENCE137,'original '+role+' complete-arm input')
    # Check actual working bytes of inherited project modules reached by
    # static imports. This is a bounded source read, not execution/restoration
    # of old producers or a claim to trace arbitrary dynamic Python imports.
    pending=list((ROOT/'scripts').glob('round155*.py'));seen=set();fixed_python={}
    while pending:
        path=pending.pop();name=path.relative_to(ROOT).as_posix()
        if name in seen:continue
        seen.add(name)
        if not path.name.startswith('round155'):
            reference=fixed_git(name,BASE,'static project Python dependency of current Round155 source',allow_checkout_eol=True)
            fixed_python[name]=dict(commit=BASE,SHA256=sha(path),bytes=path.stat().st_size,
                reference_SHA256=reference['SHA256'],reference_bytes=reference['bytes'],
                checkout_transform=reference['checkout_transform'])
        tree=ast.parse(path.read_text(encoding='utf-8-sig'),filename=str(path))
        for node in ast.walk(tree):
            names=[v.name for v in node.names] if isinstance(node,ast.Import) else (
                [node.module] if isinstance(node,ast.ImportFrom) and node.module else [])
            for module in names:
                base=module.split('.')[0]
                if not (base.startswith('round') or base.startswith('paper_s2')):continue
                imported=ROOT/'scripts'/(base+'.py')
                if imported.is_file():pending.append(imported)
    for name in ['reuse_index.json','source_manifest.json']:
        # These files can be metadata excluded from an older public manifest;
        # their explicit fixed-Git identity is still checked above when present.
        assert f'results/unified_exact_round154/{name}' in dependencies
    used_archives={item['archive_reference'] for item in dependencies.values() if 'archive_reference' in item}
    write(OUT/'reuse_index.json',dict(UTC=utc(),fixed_R153_science=SCIENCE153,fixed_R154_science=SCIENCE154,
        inherited_runtime_and_source_base=BASE,providers=providers,dependencies=[dependencies[k] for k in sorted(dependencies)],
        archives={key:archives[key] for key in sorted(used_archives)},
        resolution='Resolve unlisted transitive old paths through the fixed provider manifests and their own reuse indexes.',
        old_carriers_downloaded=0,old_carriers_repacked=0,old_producers_or_compilers_run=0))
    assert sha(identity['PE'])==identity['PE_SHA']=='0d3a94183285cc2794676c717a23dc75a47c872ad48c26d2237dd8634f1a5a01'
    assert sha(identity['DLL'])==identity['DLL_SHA']==DLL_SHA
    current={path.relative_to(ROOT).as_posix():sha(path) for path in sorted((ROOT/'scripts').glob('round155*.py'))}
    snapshots=[]
    for path in sorted((OUT/'engineering/source_snapshots').glob('*.json')):
        snapshot=read(path)
        for digest in snapshot['files'].values():
            assert sha(OUT/'engineering/source_bytes'/f'{digest}.py.txt')==digest
        snapshots.append(dict(label=path.stem,path=path.relative_to(ROOT).as_posix(),SHA256=sha(path),files=snapshot['files']))
    queues=[]
    for path in sorted((OUT/'infra').glob('*/plan.json')):
        plan=read(path)
        if 'frozen_sources' in plan:queues.append(dict(path=path.relative_to(ROOT).as_posix(),SHA256=sha(path),frozen_sources=plan['frozen_sources']))
    changed=subprocess.check_output(['git','diff','--name-only',BASE,'--','src','include','config'],cwd=ROOT,text=True).strip()
    assert not changed,('unexpected production source changes',changed)
    write(OUT/'source_manifest.json',dict(UTC=utc(),production_identity=identity,production_identity_SHA=sha(OUT/'production_identity.json'),
        production_measured_source_commit='d834d62c7a1be599867db04a427f1d43dd3631cb',PE_SHA256=identity['PE_SHA'],DLL_SHA256=DLL_SHA,
        no_Cpp_or_config_changes=True,no_rebuild=True,fixed_inherited_source_tree=BASE,
        current_new_sources=current,executed_new_source_snapshots=snapshots,dispatcher_source_bindings=queues,
        fixed_python_dependencies=fixed_python,outer_meter_label=own,
        inherited_worktree_line_endings_explicit=True,
        inherited_python_scope='actual bytes of static project imports reachable from the current Round155 source set; not an arbitrary dynamic-import execution trace',
        source_bytes_are_immutable_per_launch=True,older_producer_sources_by_fixed_references_only=True,
        latest_source_is_not_relabelled_as_every_measured_version=True))
    print(json.dumps(dict(dependencies=len(dependencies),referenced_old_archives=len(used_archives),
        current_new_sources=len(current),fixed_python_dependencies=len(fixed_python),
        exact_checkout_EOL_transforms=sum(v['checkout_transform']!='identity' for v in fixed_python.values()),
        executed_source_snapshots=len(snapshots),old_archive_downloads=0)),flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
