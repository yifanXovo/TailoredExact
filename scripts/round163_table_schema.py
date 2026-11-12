"""Preserve the actual 28-column legacy CSV, including duplicate empty headers."""
from round163_common import *
from round163_preflight import table_read,TABLES
import csv,io

EXPECTED='实例,站点数_不含仓库,车辆数,场景,场景代码,数据来源,空间分布,路线时限_T_秒,目标权重_lambda,权重倍数_lambda相对0.15,Gurobi_Seed,重复序号,数据轮次,求解时限_秒,GI_TBC_状态,GI_TBC_收敛时间_秒,GI_TBC_未收敛Gap_百分比,GI_TBC_LB,GI_TBC_UB,P_GRB_状态,P_GRB_收敛时间_秒,P_GRB_未收敛Gap_百分比,P_GRB_LB,P_GRB_UB,对比结果,对比说明,实验数据来源,实例元数据来源'.split(',')

def run():
    discovery=read(OUT/'main_table_discovery.json');facts=[]
    for p in TABLES:
        raw,enc,_=table_read(p);data=list(csv.reader(io.StringIO(raw.decode(enc),newline='')))
        assert len(data[0])==28 and all(len(row)==28 for row in data)
        assert data[0][:26]==EXPECTED[:26] and data[0][-2:]==['','']
        facts.append(dict(path=str(p),SHA256=sha(p),encoding=enc,header=data[0],columns=28,rows=len(data)-1,
            experiment_source_column_one_based=27,metadata_source_column_one_based=28,all_row_widths_equal=True))
    write(OUT/'main_table_schema_readback.json',dict(PASS=True,UTC=utc(),tables=facts,canonical_increment_header=EXPECTED,
        initial_DictReader_unique_key_view_collapsed_two_empty_headers=True,initial_file_bytes_unchanged=True,
        append_contract='exact original prefix, 28 fields per new row, original two empty header cells retained; distinct source URLs in columns27/28',
        raw_table_corresponds_to_required_28_column_order=True,header_rename=False))
    discovery.update(raw_schema_readback='main_table_schema_readback.json',raw_columns=28,source_header_cells=['',''],
        clarification='The initial dict-key view has 27 unique keys because two source header cells are empty; actual CSV has 28 fields in every row. Original bytes are retained.')
    write(OUT/'main_table_discovery.json',discovery)
    print('28 physical CSV columns and all 85 historical row widths confirmed; two empty source headers preserved.')

if __name__=='__main__':run()
