"""Explicit report completeness qualifiers; no altered pair/stage mathematics."""
import argparse, hashlib, json
from pathlib import Path

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    with path.open('w',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')

def annotate(directory, entry):
    directory=Path(directory);selection=read(directory/'selection_decision.json');summary=read(directory/'summary.json')
    valid=[v for v in selection['seed_primary_pairs'].values() if v['evaluable']]
    selection.update(all42_valid_formal=selection['qualified_formal_arms']==42,
                     evaluable_seed_pairs=len(valid),
                     formally_evaluable_seed_nonLOSS=sum(v['classification']!='LOSS' for v in valid),
                     Seed_sensitivity_assessment_complete=len(valid)==3,
                     completed_formal_arms_key_means_actual_attempts=True)
    summary.update(native_normal_formal_attempts=summary['formal_arms'],
                   qualified_formal_arms=selection['qualified_formal_arms'],
                   formal_clock_violations=selection['formal_clock_violations'],
                   formal_clock_failure_preserved=True,
                   scoped_evidence_module_SHA=sha(Path(entry).resolve().parent/'round110_scoped_evidence.py'),
                   all42_valid_formal=selection['all42_valid_formal'],
                   evaluable_seed_pairs=selection['evaluable_seed_pairs'],
                   formally_evaluable_seed_nonLOSS=selection['formally_evaluable_seed_nonLOSS'],
                   Seed_sensitivity_assessment_complete=selection['Seed_sensitivity_assessment_complete'],
                   primary_reader_entry_SHA=sha(entry),
                   report_qualifier_source_SHA=sha(__file__))
    write(directory/'selection_decision.json',selection);write(directory/'summary.json',summary)
    return summary

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--reports',type=Path,required=True);ap.add_argument('--entry',type=Path,required=True)
    a=ap.parse_args();print(json.dumps(annotate(a.reports,a.entry),allow_nan=False))
