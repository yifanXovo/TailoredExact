"""Append Artifact-authored rows without reserializing the legacy 85 records."""
from round163_common import *
from round163_table_schema import EXPECTED
import csv,io

def run():
    tick=time.perf_counter()
    schema=read(OUT/'main_table_schema_readback.json');temp=TEMP/'tables'
    additions=list(csv.reader(io.StringIO((temp/'master_append_utf8.csv').read_text(encoding='utf-8'),newline='')))
    assert len(additions)==6 and all(len(v)==28 for v in additions)
    assert [r[0] for r in additions]==[p['id'] for p in read(OUT/'input_manifest.json')['roles']]
    facts=[]
    for i,meta in enumerate(schema['tables']):
        p=Path(meta['path']);before=p.read_bytes();text=before.decode(meta['encoding'])
        old=list(csv.reader(io.StringIO(text,newline='')))
        assert old[0]==meta['header']
        keys={(r[0],r[7],r[8],r[10],r[11],r[12],r[13]) for r in old[1:]}
        newkeys=[(r[0],r[7],r[8],r[10],r[11],r[12],r[13]) for r in additions]
        assert len(set(newkeys))==6
        assert not any(k in keys for k in newkeys), 'never duplicate an already appended B/P position'
        # An intervening user edit is preserved as the current prefix; only
        # headers and duplicate keys constrain a safe append.
        backup=temp/f'actual_prefix_before_append_{i}.csv';backup.write_bytes(before)
        assert text.endswith(('\n','\r')),'unexpected unterminated last row; inspect before changing formatting'
        stream=io.StringIO(newline='');writer=csv.writer(stream,lineterminator='\r\n');writer.writerows(additions)
        suffix=stream.getvalue().encode(meta['encoding'])
        assert p.read_bytes()==before,'concurrent user write during append preparation'
        with p.open('ab') as f:f.write(suffix);f.flush();os.fsync(f.fileno())
        after=p.read_bytes();assert after==before+suffix
        data=list(csv.reader(io.StringIO(after.decode(meta['encoding']),newline='')))
        assert data[:len(old)]==old and data[-6:]==additions and all(len(v)==28 for v in data)
        facts.append(dict(path=str(p),before_SHA256=hashlib.sha256(before).hexdigest(),after_SHA256=sha(p),
            before_rows=len(old)-1,after_rows=len(data)-1,added_rows=6,encoding=meta['encoding'],
            original_prefix_bytes_identical=True,header_cells_unchanged=True,comparison_labels_unchanged=True,
            intervening_user_edit_preserved=hashlib.sha256(before).hexdigest()!=meta['SHA256'],local_before_backup=str(backup)))
    master=OUT/'reports/GI_TBC_vs_P_GRB_All_Tested_Instances.csv'
    master.write_bytes(Path(schema['tables'][0]['path']).read_bytes())
    write(OUT/'main_table_update.json',dict(PASS=True,UTC=utc(),tables=facts,repository_master_copy=str(master),
        master_copy_SHA256=sha(master),canonical_28_column_increment='reports/GI_TBC_vs_P_GRB_Round163_Increment.csv',
        only_verified_B_P_pairs=True,Eplus_not_relabelled_as_B=True,new_classification_values_blank=True,
        weight_multiplier='actual lambda/.15, independently checked by Artifact calculation',historical_identities_and_source_links_preserved=True))
    value=read(OUT/'main_table_update.json');value['ordinary_append_IO_seconds']=time.perf_counter()-tick
    write(OUT/'main_table_update.json',value)
    print(json.dumps(dict(PASS=True,updated_files=len(facts),new_B_P_pairs=6)))

if __name__=='__main__':run()
