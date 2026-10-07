"""Zero-solver syntax, measured-source and exact carrier-selection preflight."""
from round107_common import *
import ast
import round107_evidence as evidence

for source in (ROOT/'scripts').glob('round107*.py'):
    ast.parse(source.read_text(encoding='utf-8'))
identity=read(OUT/'development03/identity.json')
for relative,expected in identity['source_hashes'].items():
    assert sha(ROOT/relative)==expected,relative
files=evidence.selected()
assert not (OUT/'compact_evidence').exists()
tables=list((OUT/'reports05').glob('*.csv'))
required={'arm_results.csv','paired_results.csv','fees.csv','native_calls.csv',
          'candidate_events.csv','requests.csv','request_outcomes.csv',
          'frontier_timeline.csv','leaf_obligations.csv','controller_AM.csv',
          'controller_targets.csv','time_partitions.csv','final_physical_fleets.csv'}
assert required.issubset({p.name for p in tables})
result=dict(selected_files=len(files),raw_bytes=sum(p.stat().st_size for p in files),
    production_source_bindings=len(identity['source_hashes']),published_CSV_tables=len(tables),
    reader_SHA=sha(ROOT/'scripts/round107_reader.py'),all_scripts_syntax_passed=True,
    Optimize_calls=0,IIS_calls=0)
write(OUT/'engineering/delivery_preflight02/result.json',result)
print(json.dumps(result))
