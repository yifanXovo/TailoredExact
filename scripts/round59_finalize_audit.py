"""Final read-only evidence checks and local artifact manifest; no optimizer."""
import csv,json
from pathlib import Path
from round59_research import ROOT,OUT,RAW,sha,write
from analyze_round59 import csvwrite

def main():
    budget=json.loads((OUT/'budget_audit.json').read_text())
    assert budget['charged_processes']<=80
    assert budget['distinct_performance_scenarios_including_invalid_T']<=12
    complete=json.loads((OUT/'process_completion_audit.json').read_text())
    assert len(complete)==budget['charged_processes']
    assert not any(r['next_optimizer_overlap'] or r['watchdog'] for r in complete)
    full=list(csv.DictReader((OUT/'full_instance_results.csv').open()))
    assert len(full)==40
    assert len({(r['id'],r['arm']) for r in full})==40
    assert all(r['valid_ub']=='True' for r in full)
    audits=json.loads((OUT/'independent_route_audit.json').read_text())
    assert len(audits)==40 and all(r['passed'] for r in audits)
    assert {r['result_sha256'] for r in audits}=={r['result_sha256'] for r in full}
    by_sha={r['result_sha256']:r for r in audits}
    for path in OUT.glob('frozen_startup_*.json'):
        frozen=json.loads(path.read_text());assert sha(ROOT/frozen['source_result'])==frozen['source_result_sha256']
        assert abs(by_sha[frozen['source_result_sha256']]['objective']-frozen['U'])<1e-7
    assert len({r['executable_sha256'] for r in full})==1
    origin=list(csv.DictReader((OUT/'original_compact_f0_pairs.csv').open()))
    assert len(origin)==2 and all(r['same_build']=='True' and r['same_state']=='True' for r in origin)
    cuts=list(csv.DictReader((OUT/'native_mechanism_pairs.csv').open()))
    assert len(cuts)==8 and all(r['same_canonical_model']=='True' for r in cuts)
    start=json.loads((OUT/'repository_start_audit.json').read_text())
    preserved=[]
    for r in start['tracked_modifications']:
        digest=sha(ROOT/r['path']).upper();assert digest==r['sha256']
        preserved.append(dict(path=r['path'],original_sha256=r['sha256'],final_sha256=digest,unchanged=True))
    write(OUT/'user_file_preservation.json',preserved)
    files=[]
    for path in sorted(RAW.rglob('*')):
        if path.is_file():
            files.append(dict(path=str(path.relative_to(ROOT)),bytes=path.stat().st_size,sha256=sha(path)))
    csvwrite(OUT/'local_artifact_manifest.csv',files)
    write(OUT/'final_evidence_audit.json',dict(passed=True,full_instance_runs=40,
        independent_route_audits=40,original_formulation_pairs=2,internal_mechanism_and_monitor_pairs=8,
        strict_certificates={arm:sum(r['certificate']=='True' for r in full if r['arm']==arm) for arm in ['P-GRB','K1-H','K1-S','F0-Single-S']},
        local_artifact_count=len(files),local_artifact_bytes=sum(r['bytes'] for r in files),
        charged_processes=budget['charged_processes'],preserved_user_files=3,
        diagnostic_certificates_excluded_from_full_counts=True))
    print('Final evidence audit passed:',len(full),'full runs;',len(files),'local files hashed.')

if __name__=='__main__':main()
