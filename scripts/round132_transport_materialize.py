"""Hash-checked public newline repair for the existing single recovery root.

This is a transport repair after an observed failure, not a second recovery,
scientific rerun or permission to use a local raw/check-out fallback.
"""
import argparse,datetime,hashlib,json,os,pathlib,re,subprocess,time

SCIENCE='52b02252ba47e8228b73e071d6ed692385a4f816'
MANIFEST_SHA='7484980d2f13509a3dea0f213030522c483d82bcee8e3868484c8f2a7cceab8c'
MAP_SHA='f7eefea418d9ec6a178dfb9be63bb4866e333d1a82a860b6f6c83b1f68f35e66'
PREFIX='results/unified_exact_round132/'

def sha(data):return hashlib.sha256(data).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--science-commit',required=True)
    parser.add_argument('--repair-map-ref',required=True)
    parser.add_argument('--destination',required=True)
    parser.add_argument('--receipt',required=True)
    args=parser.parse_args()
    assert args.science_commit==SCIENCE and re.fullmatch('[0-9a-f]{40}',args.repair_map_ref)
    allowed=pathlib.Path('E:/codes/ExactEBRP-work/restore').resolve()
    dest=pathlib.Path(args.destination).resolve()
    receipt=pathlib.Path(args.receipt).resolve()
    assert dest==allowed/'round132-public' and dest.is_dir()
    assert receipt.is_relative_to(pathlib.Path('E:/codes/ExactEBRP-work').resolve()) and not receipt.is_relative_to(dest)
    assert not receipt.exists(),'Preserve the previous materialization receipt'
    for path in [dest,*dest.parents]:assert not path.is_symlink() and not path.is_junction()
    state=read(dest/'restore_state.json')
    assert state['commit']==SCIENCE and state['initially_empty'] and state['owner']=='Round132 single science-commit recovery'
    tick=time.perf_counter();transfers=[];materialized=[]
    def get(ref,name):
        assert re.fullmatch('[0-9a-f]{40}',ref)
        rel=pathlib.PurePosixPath(name)
        assert not rel.is_absolute() and '..' not in rel.parts and all(':' not in x and '\\' not in x for x in rel.parts)
        command=[str(pathlib.Path(os.environ['WINDIR'])/'System32/curl.exe'),'--disable','--proto','=https','--proto-redir','=https','--fail','--location','--silent','--show-error','--max-time','60',f'https://raw.githubusercontent.com/yifanXovo/TailoredExact/{ref}/{name}']
        r=subprocess.run(command,capture_output=True,timeout=65)
        assert r.returncode==0,(r.returncode,r.stderr.decode('utf-8',errors='replace'))
        transfers.append(dict(ref=ref,path=name,bytes=len(r.stdout),SHA256=sha(r.stdout),curlrc_disabled=True,application_credentials_supplied=False))
        return r.stdout
    result=dict(science_commit=SCIENCE,repair_metadata_commit=args.repair_map_ref,destination=str(dest),same_existing_owned_root=True,Optimize=0,native_starts=0,compilation=0,local_raw_or_old_checkout_fallback=False)
    try:
        published_script=get(args.repair_map_ref,'scripts/round132_transport_materialize.py')
        assert sha(published_script)==sha(pathlib.Path(__file__).read_bytes()),'Executed tool must equal its published pinned source'
        manifest_raw=get(SCIENCE,PREFIX+'export_manifest.json');assert sha(manifest_raw)==MANIFEST_SHA
        manifest=json.loads(manifest_raw);by={r['path']:r for r in manifest['files']}
        raw=get(args.repair_map_ref,PREFIX+'transport_materialization_map.json');assert sha(raw)==MAP_SHA
        mapping=json.loads(raw)
        assert mapping['science_commit']==SCIENCE and mapping['science_export_manifest_SHA256']==MANIFEST_SHA
        assert len(mapping['files'])==1
        for row in mapping['files']:
            name=row['path'];expected=by[name]
            assert name==PREFIX+'literature_evidence.csv'
            assert expected['bytes']==row['expected_bytes'] and expected['SHA256']==row['expected_SHA256']
            target=dest.joinpath(*pathlib.PurePosixPath(name).parts)
            assert target.parent.resolve().is_relative_to(dest)
            for path in [target,*target.parents]:assert not path.is_symlink() and not path.is_junction()
            if target.exists():
                assert sha(target.read_bytes())==row['expected_SHA256'],'Preserve unexpected existing content'
                materialized.append(dict(path=name,already_exact=True));continue
            transport=get(SCIENCE,name)
            assert len(transport)==row['transport_bytes'] and sha(transport)==row['transport_SHA256']
            lf=transport.replace(b'\r\n',b'\n');assert sha(lf)==row['normalized_LF_SHA256']
            ordinals=row['CRLF_newline_ordinals_zero_based'];count=lf.count(b'\n')
            assert count==row['newline_count'] and ordinals==sorted(set(ordinals)) and all(type(i) is int and 0<=i<count for i in ordinals)
            indices=set(ordinals);chunks=lf.split(b'\n')
            exact=b''.join(part+((b'\r\n' if i in indices else b'\n') if i<count else b'') for i,part in enumerate(chunks))
            assert len(exact)==expected['bytes'] and sha(exact)==expected['SHA256']
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as stream:stream.write(exact)
            materialized.append(dict(path=name,bytes=len(exact),SHA256=sha(exact),CRLF_ordinals=ordinals,only_newline_serialization_changed=True))
        result.update(status='PASS',map_SHA256=MAP_SHA,manifest_SHA256=MANIFEST_SHA,published_tool_SHA256=sha(published_script),materialized=materialized,transfers=transfers)
    except Exception as error:
        result.update(status='FAILED_PRESERVE_SAME_ROOT',error=repr(error),materialized=materialized,transfers=transfers)
        raise
    finally:
        result.update(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),seconds=time.perf_counter()-tick)
        receipt.parent.mkdir(parents=True,exist_ok=True);receipt.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],files=len(materialized),same_owned_root=True,seconds=result['seconds'])))

if __name__=='__main__':main()
