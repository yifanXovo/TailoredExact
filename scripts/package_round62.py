"""Final evidence index. Run only after all experimental processes have ended."""
import csv
import json
from pathlib import Path
from round62_research import ROOT,OUT,RAW,previous,sha,write


def main():
    assert not (OUT/'active_run.lock').exists(),'do not hash large artifacts during a performance run'
    entries=previous.entries();charged=[e for e in entries if e['charged']]
    assert len(charged)<=72
    for e in entries:
        assert (ROOT/e['destination']/'completion.json').exists(),e['destination']
    files=[]
    for path in sorted(RAW.rglob('*')):
        if not path.is_file() or 'paired_executables' in path.parts:continue
        files.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=sha(path)))
    with (OUT/'raw_evidence.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,['path','bytes','sha256']);writer.writeheader();writer.writerows(files)
    diagnostics=[];native=[]
    fields=['status','certificate_type','certificate_scope','strict_certified_original_problem','objective','lower_bound','upper_bound','gap',
        'round62_archive_mode','round62_threshold_mode','round62_archive_evidence_persisted','round62_external_stop_requested',
        'round62_external_certificate','round62_control_upper_bound','round62_archive_upper_bound','round62_archive_construction_seconds']
    for e in charged:
        folder=ROOT/e['destination']
        for name in ['micro_result.json','oracle_result.json','audit_result.json']:
            if (folder/name).exists():
                diagnostics.append(dict(number=e['charged_number'],id=e['id'],stage=e['stage'],arm=e['arm'],
                    source=(folder/name).relative_to(ROOT).as_posix(),sha256=sha(folder/name),result=json.loads((folder/name).read_text())))
        result=folder/'result.json';ledger=folder/'external'/'paper_optimize_ledger.csv'
        if not result.exists() or not ledger.exists():continue
        r=json.loads(result.read_text());compact={k:r[k] for k in fields if k in r}
        compact.update({k:v for k,v in r.items() if k.startswith('external_gini_tree_') or
            (k.startswith('gurobi_') and any(t in k for t in ['effective','return_code','version']))})
        calls=list(csv.DictReader(ledger.open(newline='')))
        native.append(dict(number=e['charged_number'],id=e['id'],stage=e['stage'],arm=e['arm'],
            result_sha256=sha(result),ledger_sha256=sha(ledger),summary=compact,calls=calls))
    write(OUT/'diagnostic_results.json',diagnostics)
    write(OUT/'full_native_evidence.json',native)
    write(OUT/'evidence_index.json',dict(raw_root=str(RAW),raw_file_count=len(files),raw_bytes=sum(p['bytes'] for p in files),
        raw_manifest_sha256=sha(OUT/'raw_evidence.csv'),charged_launches=len(charged),
        executable_manifests=[p.name for p in sorted(OUT.glob('paired_executables_*.json'))],
        submitted_verification='python scripts/verify_round62.py --submitted',
        scope='Local raw artifacts are hashed, not uploaded. Submitted physical witnesses and mathematical proofs are independently checkable.'))
    print('indexed',len(files),'local raw artifacts;',len(native),'complete native lifecycles;',len(diagnostics),'diagnostic results')


if __name__=='__main__':main()
