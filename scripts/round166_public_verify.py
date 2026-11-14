"""One anonymous normal-TLS new-only public recovery; no historical downloads."""
from round166_common import *
import argparse,csv,gzip,io,ssl,urllib.request,urllib.parse,zipfile

def public_recovery(publication):
    tick=time.perf_counter();source=read(OUT/'source_publication.json');science=source['science_commit']
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    root=WORK/'recovery'/('round166_public_'+stamp);assert not root.exists();root.mkdir(parents=True)
    downloads=root/'downloads';restored=root/'restored';downloads.mkdir();restored.mkdir()
    context=ssl.create_default_context();assert context.check_hostname and context.verify_mode==ssl.CERT_REQUIRED
    transfers=[]
    def fetch(pin,binding):
        name=binding['path'];url='https://raw.githubusercontent.com/yifanXovo/TailoredExact/'+pin+'/'+urllib.parse.quote(name,safe='/')
        target=downloads/Path(name).name;assert not target.exists();begin=time.perf_counter()
        request=urllib.request.Request(url,headers={'User-Agent':'Round166-public-byte-verification'})
        digest=hashlib.sha256();length=0
        with urllib.request.urlopen(request,context=context,timeout=90) as response,target.open('xb') as stream:
            assert response.status==200
            while True:
                chunk=response.read(256*1024)
                if not chunk:break
                stream.write(chunk);digest.update(chunk);length+=len(chunk)
                assert length<=binding['bytes'],('unexpected public object size',name,length)
        assert length==binding['bytes'] and digest.hexdigest()==binding['SHA256'],('public bytes differ',name)
        transfers.append(dict(commit=pin,path=name,URL=url,bytes=length,SHA256=digest.hexdigest(),seconds=time.perf_counter()-begin,
            HTTP_status=200,TLS_certificate_verification=True,hostname_verification=True,Authorization_header=False))
        print('Public bytes verified:',name,flush=True);return target
    publication_binding=bind(OUT/'source_publication.json')
    recovered_publication=fetch(publication,publication_binding);assert read(recovered_publication)==source
    source_zip=fetch(publication,source['archive']);source_map_path=fetch(publication,source['member_map'])
    with gzip.open(source_map_path,'rt',encoding='utf-8',newline='') as f:source_map=list(csv.DictReader(f))
    def safe_target(name):
        p=(restored/name).resolve();assert p.is_relative_to(restored.resolve()) and '..' not in Path(name).parts,name
        return p
    def check_archive(path,entries,extract_source=False):
        expected={e['member']:e for e in entries};assert len(expected)==len(entries)
        with zipfile.ZipFile(path) as archive:
            names=archive.namelist();assert len(names)==len(set(names)) and set(names)==set(expected),path
            for name in names:
                expected_member=expected[name];data=archive.read(name)
                assert len(data)==int(expected_member['bytes']) and hashlib.sha256(data).hexdigest()==expected_member['SHA256'],name
                if extract_source or name.startswith('runtime/'):
                    target=safe_target(name);target.parent.mkdir(parents=True,exist_ok=True)
                    with target.open('xb') as f:f.write(data)
        return len(entries)
    source_count=check_archive(source_zip,source_map,True)
    assert source_count==source['source_bundle_members']
    raw_manifest_path=restored/'results/unified_exact_round166/evidence_archives.json'
    assert raw_manifest_path.read_bytes()==(OUT/'evidence_archives.json').read_bytes()
    raw=read(raw_manifest_path);map_path=restored/raw['member_map']['path'];assert sha(map_path)==raw['member_map']['SHA256']
    with gzip.open(map_path,'rt',encoding='utf-8',newline='') as f:raw_map=list(csv.DictReader(f))
    count=0
    for archive in raw['archives']:
        local=fetch(science,archive);entries=[e for e in raw_map if e['archive']==archive['path']]
        assert len(entries)==archive['members'];count+=check_archive(local,entries)
    assert count==len(raw_map)==raw['members']
    assert source['changed_scientific_paths']==source_count+len(raw['archives'])
    pe=restored/'runtime/ExactEBRP.exe';assert sha(pe)==read(OUT/'candidate_manifest.json')['production_PE_SHA']
    receipt=dict(UTC=utc(),PASS=True,publication_commit=publication,science_commit=science,
        fresh_empty_root=str(root),anonymous=True,normal_TLS=True,TLS_bypass=False,Authorization_header=False,
        source_science_git_blob_members_verified=source_count,raw_new_members_verified=count,
        raw_archives_recovered=len(raw['archives']),own_runtime_PE_SHA=sha(pe),
        raw_layout='All new raw ZIP bytes recovered and every member streamed/CRC/SHA checked; retained compressed. Source/paper and own runtime members expanded.',
        old_carrier_downloads=0,old_carrier_repacked=0,commercial_DLL_downloaded=False,private_antecedent_downloaded=False,
        transfers=transfers,network_transfer_seconds=sum(t['seconds'] for t in transfers),
        total_restore_and_byte_check_seconds=time.perf_counter()-tick,Optimize=0,
        receipt_not_in_its_own_verified_scientific_commit=True,generator=bind(Path(__file__)))
    write(root/'recovery_receipt.json',receipt);write(OUT/'public_recovery.json',receipt)
    print('New-only public recovery PASS:',source_count,'source/paper members;',count,'new raw members.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--publication',required=True);args=parser.parse_args();public_recovery(args.publication)
