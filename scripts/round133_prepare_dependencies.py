"""Stage only previously indexed old snippets from fixed public Git objects."""
from round133_common import *
from pathlib import PurePosixPath
import io, zipfile

def main():
    own=os.environ.get('ROUND133_METERED_PARENT_LABEL')
    assert not [row for row in budget()['unclosed'] if row['label']!=own],'do not stage while another outer is active'
    manifest=OUT/'dependencies/historical_snippets.json';assert not manifest.exists()
    history=read(OUT/'historical_impact.json');proof=read(OUT/'review/directed_old_evidence_receipt.json')
    carriers={r['archive_path']:r for r in history['carrier_checks']['carriers']}
    required={r['path']:dict(r) for r in history['read_bindings']}
    for name,identity in proof['reads'].items():
        normalized=name.replace('\\','/');relative=normalized[normalized.index('results/'):]
        if relative in required:
            assert required[relative]['SHA256']==identity['SHA256'];continue
        if '/campaign/' in relative:
            group=relative.split('/')[3];archive=f'results/unified_exact_round132/artifacts/campaign_{group}.zip'
            row=carriers[archive]
            location=dict(kind='hash_verified_archive_member',public_commit=BASE,archive_path=archive,
                archive_SHA256=row['archive_SHA256'],archive_bytes=row['archive_bytes'],member=relative,
                member_SHA256=identity['SHA256'])
        else:location=dict(kind='loose_repository_file',commit=BASE,path=relative)
        required[relative]=dict(path=relative,SHA256=identity['SHA256'],bytes=identity['bytes'],public_location=location)
    archives={};rows=[]
    for relative,row in sorted(required.items()):
        parts=PurePosixPath(relative)
        assert not parts.is_absolute() and '..' not in parts.parts and ':' not in relative
        location=row['public_location'];transport='exact'
        if location['kind']=='hash_verified_archive_member':
            name=location['archive_path']
            if name not in archives:
                blob=git('show',BASE+':'+name)
                assert len(blob)==location['archive_bytes'] and hashlib.sha256(blob).hexdigest()==location['archive_SHA256']
                archives[name]=zipfile.ZipFile(io.BytesIO(blob))
            raw=archives[name].read(location['member'])
            assert hashlib.sha256(raw).hexdigest()==location['member_SHA256']
            public_SHA=row['SHA256']
        else:
            raw=git('show',BASE+':'+relative);public_SHA=hashlib.sha256(raw).hexdigest()
            if public_SHA!=row['SHA256']:
                lf=raw.replace(b'\r\n',b'\n')
                choices=[(lf,'LF'),(lf.replace(b'\n',b'\r\n'),'CRLF')]
                recovered=next(((b,label) for b,label in choices if hashlib.sha256(b).hexdigest()==row['SHA256']),None)
                assert recovered is not None,('old byte identity not recoverable',relative)
                original=raw;raw,transport=recovered
                if relative.endswith('.json'):assert json.loads(original)==json.loads(raw)
        assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['SHA256'],relative
        if relative=='results/unified_exact_round132/campaign/D_group24/raw/02_X-35-U_S1_R1_S2/external/models/L0_epoch_0_generation_1.lp':
            target=OUT/'dependencies/C/D24_call4_serialized.lp'
        elif relative=='results/unified_exact_round132/inputs/X-35-U.txt':
            target=OUT/'inputs/X-35-U.txt'
        else:target=OUT/'dependencies/history'/relative
        if target.exists():assert target.read_bytes()==raw,('owned dependency identity',relative,str(target),sha(target),row['SHA256'])
        else:
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as stream:stream.write(raw)
        rows.append(dict(source_path=relative,path=target.relative_to(ROOT).as_posix(),SHA256=row['SHA256'],
            bytes=len(raw),source_commit=BASE,public_location=location,public_transport_SHA256=public_SHA,
            exact_text_transport_materialization=transport))
    for archive in archives.values():archive.close()
    write(manifest,dict(schema='round133-finite-historical-fragments-v1',UTC=utc(),files=rows,
        source_archive_count=len(archives),whole_old_campaign_extractions=0,
        old_34_carriers_modified_or_repacked=False,local_raw_fallback=False,Optimize=0,
        selected_payload_bytes=sum(row['bytes'] for row in rows)))
    print(json.dumps(dict(files=len(rows),bytes=sum(row['bytes'] for row in rows),old_archives_streamed=len(archives),Optimize=0)))

if __name__=='__main__':main()
