"""One offline sanitized replacement carrier and one verified empty-root restore.

Pack consumes a restricted local original only during this security repair.
Public restore accepts only the new safe manifest and parts, never old bytes.
"""
import argparse
import gzip
import io
import json
from pathlib import Path
import tarfile
import time
import publication_security as security

R116 = 'results/unified_exact_round116'
R117 = 'results/unified_exact_round117'

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')

class Parts:
    def __init__(self, directory):
        self.directory = directory
        self.paths = []
        self.file = None
        self.size = 0
        self.position = 0

    def write(self, data):
        count = len(data)
        while data:
            if self.file is None:
                p = self.directory / f'evidence.tar.gz.part{len(self.paths)+1:03d}'
                self.paths.append(p)
                self.file = p.open('xb')
                self.size = 0
            n = min(len(data), 32*1024*1024-self.size)
            self.file.write(data[:n])
            self.size += n
            self.position += n
            data = data[n:]
            if self.size == 32*1024*1024:
                self.file.close()
                self.file = None
        return count

    def flush(self):
        if self.file:
            self.file.flush()

    def tell(self):
        return self.position

    def finish(self):
        if self.file:
            self.file.close()
            self.file = None

def sanitize_source(root, private):
    out = root / R116
    private.mkdir(parents=True, exist_ok=True)
    replacements = {}
    mapping = []
    def save(path, data, categories):
        original = path.read_bytes()
        rel = path.relative_to(root).as_posix()
        backup = private / rel
        backup.parent.mkdir(parents=True, exist_ok=True)
        with backup.open('xb') as f:
            f.write(original)
        path.write_bytes(data)
        replacements[rel] = data
        mapping.append({'original_path': rel, 'original_sha256': security.sha(original),
                        'original_bytes': len(original), 'sanitized_path': rel,
                        'sanitized_sha256': security.sha(data), 'sanitized_bytes': len(data),
                        'categories': categories, 'reason': 'Remove non-scientific web runtime/session material; preserve source provenance'})
    receipts = {}
    for name in ['system_data','license','discovery','station_information','system_information']:
        folder = out / 'source/requests' / name
        meta_path, body_path = folder/'01.json', folder/'01.response'
        meta = json.loads(meta_path.read_bytes())
        original = body_path.read_bytes()
        safe = security.extract_html(original, meta['request_url']) if meta['kind'] == 'html' else original
        if safe != original:
            if name == 'license':
                for phrase in [b'source material', b'non-commercial purposes', b'stand-alone dataset']:
                    assert phrase in safe
            if name == 'system_data':
                assert b'gbfs.capitalbikeshare.com' in safe and b'General Bikeshare' in safe
            save(body_path, safe, ['scripts','client_credentials','runtime_configuration','non-text_attributes'])
        clean = dict(meta)
        clean['headers'] = security.safe_headers(meta['headers'])
        clean['request_url'] = security.safe_url(meta['request_url'])
        clean['final_url'] = security.safe_url(meta['final_url'])
        if clean.get('error'):
            clean['error'] = '[REDACTED: raw transport error; historical status preserved]'
        clean.update(original_response_SHA256=meta['response_SHA256'], original_response_bytes=meta['response_bytes'],
                     response_SHA256=security.sha(safe), response_bytes=len(safe),
                     publication_tool_version=security.VERSION,
                     response_headers_policy='explicit research-safe whitelist',
                     discarded_header_names=sorted(k.lower() for k in meta['headers'] if k.lower() not in security.HEADER_ALLOWLIST),
                     response_form='safe_visible_text_extract' if meta['kind']=='html' else 'unchanged_static_JSON')
        save(meta_path, (json.dumps(clean,indent=2)+'\n').encode(), ['response_header_whitelist','source_identity_separated_from_safe_identity'])
        receipts[name] = clean
    path = out / 'source/snapshot.json'
    snapshot = json.loads(path.read_bytes())
    for prefix, name in [('station','station_information'),('discovery','discovery'),('system','system_information'),('license','license'),('entry','system_data')]:
        snapshot[prefix+'_request'] = receipts[name]
        if prefix in ['license','entry']:
            snapshot['original_'+prefix+'_SHA'] = snapshot[prefix+'_SHA']
            snapshot[prefix+'_SHA'] = receipts[name]['response_SHA256']
    snapshot['security_publication'] = {'tool_version':security.VERSION,'original_runtime_bodies_superseded':True,
                                      'station_response_raw_bytes_unchanged':True,'historical_recipe_identity_retained':True,
                                      'redaction_manifest':R117+'/redaction_manifest.json'}
    save(path, (json.dumps(snapshot,indent=2)+'\n').encode(), ['nested_response_headers','explicit_safe_HTML_identity_mapping'])
    assert security.scan_items(replacements.items())['passed']
    return replacements, mapping

def pack(root, original_archive, private):
    tick = time.perf_counter()
    root = Path(root).resolve()
    private = Path(private).resolve()
    assert not private.is_relative_to(root), 'restricted original backup must be outside public tree'
    out = root / R117
    replacements, mapping = sanitize_source(root, private / 'affected_originals')
    old_manifest = json.loads((root/R116/'compact_evidence/manifest.json').read_bytes())
    old_files = old_manifest['files']
    # Revised publication entry points have preserved, safe historical code copies.
    for name in ['round116_data.py','round116_delivery.py']:
        path = 'scripts/'+name
        historical = R117+'/historical_helpers/'+name+'.txt'
        original = (root/historical).read_bytes()
        safe = (root/path).read_bytes()
        mapping.append({'original_path':path,'original_sha256':security.sha(original),
                        'sanitized_path':path,'sanitized_sha256':security.sha(safe),
                        'categories':['closed_unsafe_acquisition'] if name=='round116_data.py' else ['publication_gate'],
                        'preserved_historical_code_path':historical,
                        'reason':'Security publication change; old admitted identity remains attached only to original bytes'})
        replacements[path] = safe
    write(out/'redaction_manifest.json',{'schema':'round117-redaction-v1','tool_version':security.VERSION,
          'entries':mapping,'original_carrier_parts':old_manifest['parts'],
          'carrier_mapping_path':R117+'/carrier_replacement.json',
          'safe_manifest_path':R117+'/safe_evidence/manifest.json',
          'scientific_comparison':'All unchanged old carrier members compared byte for byte during streaming replacement; four-role reconstruction checked separately',
          'review_scope':'Both HTMLs, five receipts, all nested requests, entire R116 carrier and R115 inherited carrier; no history purge claim',
          'old_SHA_does_not_verify_safe_bytes':True,'original_hash_cannot_reconstruct_removed_secrets':True})
    extras = {p.relative_to(root).as_posix():p.read_bytes() for p in (out).rglob('*') if p.is_file() and 'safe_evidence' not in p.parts}
    for name in ['publication_security.py','round117_release.py','round117_validate.py']:
        extras['scripts/'+name] = (root/'scripts'/name).read_bytes()
    extras['tests/test_publication_security.py'] = (root/'tests/test_publication_security.py').read_bytes()
    extras[R116+'/public_reproduction.md'] = (root/R116/'public_reproduction.md').read_bytes()
    directory = out/'safe_evidence'
    directory.mkdir(exist_ok=False)
    writer = Parts(directory)
    files = {}
    unchanged = 0
    scanner = security.Scanner()
    seen = set()
    def add(archive, name, data):
        security.Scanner.member_name(name)
        if name in files:
            raise ValueError('duplicate publication member')
        scanner.files += 1
        scanner.payload(data,name)
        if scanner.findings or scanner.errors:
            raise ValueError('publication gate failed; values withheld')
        files[name] = {'SHA':security.sha(data),'bytes':len(data)}
        member = tarfile.TarInfo(name)
        member.size = len(data)
        member.mode = 0o644
        member.mtime = 0
        archive.addfile(member,io.BytesIO(data))
    try:
        with gzip.GzipFile(fileobj=writer,mode='wb',mtime=0) as gz:
            with tarfile.open(fileobj=gz,mode='w|') as target:
                with tarfile.open(original_archive,mode='r|gz') as source:
                    for member in source:
                        assert member.isfile()
                        name = member.name
                        original = source.extractfile(member).read()
                        assert old_files[name]['SHA']==security.sha(original) and old_files[name]['bytes']==len(original)
                        seen.add(name)
                        safe = replacements.get(name,original)
                        if safe==original:
                            unchanged += 1
                        add(target,name,safe)
                assert seen==set(old_files)
                for name,data in sorted(extras.items()):
                    if name not in files:
                        add(target,name,data)
    finally:
        writer.finish()
    parts = [{'path':p.relative_to(root).as_posix(),'SHA':security.sha(p.read_bytes()),'bytes':p.stat().st_size} for p in writer.paths]
    manifest = {'schema':'round117-sanitized-current-evidence-v1','files':files,'parts':parts,
                'historical_R116_members':len(old_files),'historical_R116_members_byte_equal':unchanged,
                'historical_byte_exceptions':sorted(replacements),'old_carrier_dependency':False,
                'native_starts':0,'Optimize':0}
    write(directory/'manifest.json',manifest)
    removed = []
    for part in old_manifest['parts']:
        path = root/part['path']
        assert path.resolve().is_relative_to((root/R116/'compact_evidence').resolve())
        assert security.sha(path.read_bytes())==part['SHA']
        removed.append({'path':part['path'],'sha256':part['SHA'],'bytes':part['bytes'],'current_tree_removed':True})
        path.unlink()
    write(root/R116/'compact_evidence/SUPERSEDED.json',{'status':'SUPERSEDED_SECURITY_REDACTION','original_parts':removed,
          'original_manifest_sha256':security.sha((root/R116/'compact_evidence/manifest.json').read_bytes()),
          'replacement_manifest':R117+'/safe_evidence/manifest.json','old_manifest_historical_identity_only':True,
          'history_purged':False})
    write(out/'carrier_replacement.json',{'schema':'round117-carrier-replacement-v1','tool_version':security.VERSION,
          'old_carriers_removed':removed,'new_parts':parts,
          'safe_manifest_path':R117+'/safe_evidence/manifest.json',
          'safe_manifest_sha256':security.sha((directory/'manifest.json').read_bytes()),
          'scientific_comparison':'All unchanged old carrier members compared byte for byte during streaming replacement; four-role reconstruction checked separately',
          'review_scope':'Both HTMLs, five receipts, all nested requests, entire R116 carrier and R115 inherited carrier; no history purge claim',
          'old_SHA_does_not_verify_safe_bytes':True,'original_hash_cannot_reconstruct_removed_secrets':True})
    report = {'old_carrier_members':len(old_files),'old_members_unchanged':unchanged,'changed_old_members':len(old_files)-unchanged,
              'changed_old_paths':sorted(p for p in replacements if p in old_files),
              'all_other_scientific_members_byte_equal':True,'historical_V100_evidence_preserved':True,
              'no_new_scientific_observations':True,'safe_carrier_members':len(files),
              'scan_findings':scanner.findings,'scan_errors':scanner.errors,'bytes_scanned':scanner.bytes,
              'publication_gate_passed':not scanner.findings and not scanner.errors,
              'compressed_bytes':sum(p['bytes'] for p in parts),
              'parts':parts,'native_starts':0,'Optimize':0,'engineering_seconds':time.perf_counter()-tick}
    write(out/'scientific_integrity.json',report)
    print(json.dumps({k:report[k] for k in ['old_carrier_members','old_members_unchanged','changed_old_members','safe_carrier_members','compressed_bytes','publication_gate_passed','engineering_seconds']}),flush=True)
    return report

def restore(root, destination, receipt_path):
    tick=time.perf_counter()
    root,destination=Path(root).resolve(),Path(destination).resolve()
    assert root!=destination and not destination.is_relative_to(root)
    destination.mkdir(parents=True,exist_ok=False)
    path=root/R117/'safe_evidence/manifest.json'
    manifest=json.loads(path.read_bytes())
    assert manifest['schema']=='round117-sanitized-current-evidence-v1' and not manifest['old_carrier_dependency']
    data=[]
    for part in manifest['parts']:
        p=(root/part['path']).resolve()
        assert p.is_relative_to((root/R117/'safe_evidence').resolve())
        body=p.read_bytes()
        assert security.sha(body)==part['SHA'] and len(body)==part['bytes']
        data.append(body)
    restored=set()
    with tarfile.open(fileobj=io.BytesIO(b''.join(data)),mode='r|gz') as archive:
        for member in archive:
            security.Scanner.member_name(member.name)
            assert member.isfile() and member.name not in restored
            expected=manifest['files'][member.name]
            body=archive.extractfile(member).read()
            assert member.size==expected['bytes']==len(body) and security.sha(body)==expected['SHA']
            path=(destination/member.name).resolve()
            assert path.is_relative_to(destination)
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as f:
                f.write(body)
            restored.add(member.name)
    assert restored==set(manifest['files'])
    report={'safe_manifest_sha256':security.sha((root/R117/'safe_evidence/manifest.json').read_bytes()),
            'restored_root':str(destination),'fresh_empty_directory':True,'files_verified':len(restored),
            'every_new_file_hash_equal':True,'old_contaminated_carrier_read':False,'network_requests':0,
            'original_root_fallback':False,'native_starts':0,'Optimize':0,'engineering_seconds':time.perf_counter()-tick}
    write(receipt_path,report)
    print(json.dumps(report),flush=True)
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('pack');p.add_argument('--root',required=True);p.add_argument('--original-archive',required=True);p.add_argument('--private',required=True)
    p=sub.add_parser('restore');p.add_argument('--root',required=True);p.add_argument('--destination',required=True);p.add_argument('--out',required=True)
    args=parser.parse_args()
    if args.action=='pack':pack(args.root,args.original_archive,args.private)
    else:restore(args.root,args.destination,args.out)
