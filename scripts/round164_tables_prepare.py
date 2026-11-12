"""Refresh the accessible master identities without changing user files."""
from round164_common import *
import csv,io
from round164_setup import TABLES

def run():
    facts=[]
    pending=[(138,'R-B35-S-T2',1,2400),(155,'N-B35-S',None,7200),(156,'R-X35-S-T2',None,7200)]
    for i,path in enumerate(TABLES):
        raw=path.read_bytes();enc='gb18030';data=list(csv.reader(io.StringIO(raw.decode(enc),newline='')))
        assert len(data[0])==28 and all(len(r)==28 for r in data)
        def has(item):
            rnd,name,seed,cap=item
            return any(r[0]==name and int(r[12])==rnd and int(r[13])==cap and
                (seed is None or int(r[10])==seed) and r[19] in ('N/A','n.a.','NA') for r in data[1:])
        present=[dict(round=v[0],id=v[1],seed=v[2],cap=v[3],found=has(v)) for v in pending]
        keys=[(r[0],r[7],r[8],r[10],r[11],r[12],r[13],r[26],r[27]) for r in data[1:]]
        assert len(keys)==len(set(keys)),('inspect historical duplicate identity before append',str(path))
        backup=TEMP/'tables'/f'actual_master_before_{i}.csv';backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(raw)
        facts.append(dict(path=str(path),SHA256=sha(path),bytes=len(raw),encoding=enc,rows=len(data)-1,
            header=data[0],columns=28,local_backup=str(backup),specified_historical_rows=present,
            all_three_specified_rows_present=all(r['found'] for r in present)))
    # Prefer a real accessible complete 94-row source if it has appeared during
    # the long panel. Never silently replace it with an older 91-row copy.
    primary=max(facts,key=lambda f:(f['all_three_specified_rows_present'],f['rows']))
    complete94=primary['rows']==94 and primary['all_three_specified_rows_present']
    assert primary['rows'] in (91,94),('inspect changed master; no blind overwrite',primary)
    header=list(primary['header']);header[-2:]=['实验数据来源','实例元数据来源']
    write(OUT/'main_table_final_discovery.json',dict(PASS=True,UTC=utc(),tables=facts,primary=primary,
        supplied_94_row_version_found=complete94,canonical_increment_header=header,
        expected_increment_pairs=12,expected_working_master_rows=primary['rows']+12,
        unavailable_historical_union=[r for r in primary['specified_historical_rows'] if not r['found']],
        external_user_files_will_be_preserved=not complete94,
        fallback='deliver exact 12-pair increment and byte-prefix-preserving 103-row working copy; the unavailable 94-row master still needs union' if not complete94 else None))
    print(json.dumps(dict(PASS=True,primary_rows=primary['rows'],found_complete_94=complete94,
        expected_working_master_rows=primary['rows']+12)))

if __name__=='__main__':run()
