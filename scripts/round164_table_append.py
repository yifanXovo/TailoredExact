"""Transport only Artifact-authored rows, without reserializing historical CSV."""
from round164_common import *
import csv,io

def run():
    tick=time.perf_counter();discovery=read(OUT/'main_table_final_discovery.json');primary=discovery['primary']
    temp=TEMP/'tables'
    additions=list(csv.reader(io.StringIO((temp/'master_append_utf8.csv').read_text(encoding='utf-8'),newline='')))
    assert len(additions)==12 and all(len(r)==28 for r in additions)
    assert all(r[10] in ('1','2') and r[11]=='1' and r[12]=='164' for r in additions)
    path=Path(primary['path']);before=path.read_bytes();assert sha(path)==primary['SHA256']
    old=list(csv.reader(io.StringIO(before.decode(primary['encoding']),newline='')))
    assert old[0]==primary['header'] and len(old)-1==primary['rows']
    key=lambda r:(r[0],r[7],r[8],r[10],r[11],r[12],r[13],r[26],r[27])
    assert len({key(r) for r in additions})==12 and not {key(r) for r in additions}&{key(r) for r in old[1:]}
    assert before.endswith((b'\n',b'\r'))
    stream=io.StringIO(newline='');csv.writer(stream,lineterminator='\r\n').writerows(additions)
    suffix=stream.getvalue().encode(primary['encoding']);output=OUT/'reports/GI_TBC_vs_P_GRB_All_Tested_Instances.csv'
    output.write_bytes(before+suffix)
    after=output.read_bytes();data=list(csv.reader(io.StringIO(after.decode(primary['encoding']),newline='')))
    assert after==before+suffix and data[:len(old)]==old and data[-12:]==additions
    assert all(len(r)==28 for r in data)
    changes=[]
    if discovery['supplied_94_row_version_found']:
        # Only equal current authoritative replicas are safe to append. A
        # differently edited copy remains intact instead of being overwritten.
        for table in discovery['tables']:
            target=Path(table['path'])
            if table['SHA256']!=primary['SHA256']:continue
            assert target.read_bytes()==before
            with target.open('ab') as f:f.write(suffix);f.flush();os.fsync(f.fileno())
            assert target.read_bytes()==after
            changes.append(dict(path=str(target),before_rows=94,after_rows=106,original_prefix_bytes_identical=True,
                before_SHA256=primary['SHA256'],after_SHA256=sha(target),encoding=primary['encoding']))
    else:
        assert all(sha(Path(t['path']))==t['SHA256'] for t in discovery['tables'])
    write(OUT/'main_table_update.json',dict(PASS=True,UTC=utc(),primary_source=str(path),
        source_rows=primary['rows'],working_master_path=output.relative_to(ROOT).as_posix(),
        working_master_rows=len(data)-1,working_master_SHA256=sha(output),added_pairs=12,
        encoding=primary['encoding'],physical_columns=28,original_prefix_bytes_identical=True,
        original_header_cells_unchanged=True,original_precision_and_source_links_preserved=True,
        canonical_increment='reports/GI_TBC_vs_P_GRB_Round164_Increment.csv',external_actual_writes=changes,
        external_user_files_preserved_if_94_unavailable=not discovery['supplied_94_row_version_found'],
        actual_94_row_master_found=discovery['supplied_94_row_version_found'],
        missing_historical_union=discovery['unavailable_historical_union'],
        unavailable_94_row_master_not_claimed_updated=True,Seed0_duplicated=False,Eplus_relabelled=False,
        ordinary_transport_IO_seconds=time.perf_counter()-tick))
    print(json.dumps(dict(PASS=True,working_master_rows=len(data)-1,increment=12,external_writes=len(changes))))

if __name__=='__main__':run()
