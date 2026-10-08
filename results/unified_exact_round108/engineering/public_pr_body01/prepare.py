"""Prepare an English PR body from the final report after real public recovery."""
import argparse,hashlib,json,sys,time
from pathlib import Path
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def finish(root,review):
    root=Path(root).resolve();out=root/'results/unified_exact_round108';here=Path(__file__).resolve().parent
    start=time.perf_counter();summary=read(out/'reports_final/summary.json')
    selected=read(out/'selection_decision.json');assert selected['stage']==summary['stage']
    isolated=read(root/review);assert isolated['decision']=='ACCEPT'
    comparison=read(out/'public_comparison_receipt.json');assert comparison['comparison']['passed'] is True
    restored=read(out/'public_restore_receipt.json');assert restored['public_files_only'] is True and restored['original_workspace_reads'] is False
    exported=read(out/'public_export_receipt.json');assert exported['only_proposed_public_files_and_explicit_public_dependencies'] is True
    manifest=read(out/'compact_evidence/manifest.json')
    text=(out/'final_report.md').read_text(encoding='utf-8')
    assert text.startswith('# Round108: '+summary['stage']) and 'Actual export to a new public-only directory' in text
    text+='\n## Actual public recovery and draft context\n\n'
    text+='This answers whether the single inherited R100 M-B warrants broader paper evaluation while allowing explicit ENS tradeoffs. All 21 registered formal arms completed normally; no performance retry, cancellation, production change, new cut or new variant was used.\n\n'
    json_names=comparison['comparison']['exact_JSON_files_compared']
    text+=f"The public export root was `{exported['public_root']}`; the distinct fresh restored root was `{restored['restored_root']}`. Actual isolated stdlib reconstruction compared {comparison['comparison']['exact_csv_fields_compared']} CSV fields and every value in all {len(json_names)} decision/summary JSON files ({', '.join(json_names)}), with exact equality. The standalone independent isolated review is ACCEPT. This is raw-evidence/mathematical recovery, not an independent engine performance rerun.\n\n"
    text+=f"Combined compressed carrier bytes: {manifest['archive_bytes']}; exact combined SHA256: {manifest['archive_sha256']}. The manifest supplies every own raw member and 15 exact small historical dependencies; PE, DLL, license and credentials are excluded. See [public manifest](https://github.com/yifanXovo/TailoredExact/blob/codex/round108-frozen-mb-validation/results/unified_exact_round108/compact_evidence/manifest.json) and [reproduction record](https://github.com/yifanXovo/TailoredExact/blob/codex/round108-frozen-mb-validation/results/unified_exact_round108/reproduce.md).\n\n"
    if manifest['parts']:
        text+=f"The actual large carrier is published as {len(manifest['parts'])} consecutive compressed-byte parts, without per-part recompression: " + ', '.join(f"`{p['path']}` ({p['bytes']} bytes)" for p in manifest['parts']) + '. Each part is below the strict 95 MiB Git blob limit; offsets, part hashes and the combined hash are validated before plain-member recovery. The local oversized combined file is not a public Git blob.\n\n'
    text+=f"The actual isolated review is [public_isolated_review01](https://github.com/yifanXovo/TailoredExact/blob/codex/round108-frozen-mb-validation/{review}). It binds the fresh restored root, standalone source and completed raw audit.\n\n"
    text+='This is a new stacked draft on [Round107 PR #169](https://github.com/yifanXovo/TailoredExact/pull/169), base codex/round107-ens-frontier-route-events at b5db3f038f64215766a54498d8acc82e384de733. The old PR and main are not modified or merged. Current table links: [all arms](https://github.com/yifanXovo/TailoredExact/blob/codex/round108-frozen-mb-validation/results/unified_exact_round108/reports_final/arms.csv), [all pairs](https://github.com/yifanXovo/TailoredExact/blob/codex/round108-frozen-mb-validation/results/unified_exact_round108/reports_final/pairs.csv), [selection](https://github.com/yifanXovo/TailoredExact/blob/codex/round108-frozen-mb-validation/results/unified_exact_round108/selection_decision.json), [evidence gaps](https://github.com/yifanXovo/TailoredExact/blob/codex/round108-frozen-mb-validation/results/unified_exact_round108/reports_final/candidate_evidence_gap.csv), and [stopped families](https://github.com/yifanXovo/TailoredExact/blob/codex/round108-frozen-mb-validation/results/unified_exact_round108/reports_final/stopped_mechanism_families.csv).\n'
    with (here/'body.md').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    write(here/'receipt.json',dict(command=[sys.executable,str(Path(__file__).resolve()),'--root',str(root),'--isolated-review',review],
        read_root=str(root),exit_code=0,seconds=time.perf_counter()-start,source_SHA=sha(__file__),
        body_SHA=sha(here/'body.md'),final_report_SHA=sha(out/'final_report.md'),
        summary_SHA=sha(out/'reports_final/summary.json'),selection_SHA=sha(out/'selection_decision.json'),
        independent_isolated_review_SHA=sha(root/review),public_comparison_SHA=sha(out/'public_comparison_receipt.json'),
        public_restore_SHA=sha(out/'public_restore_receipt.json'),public_manifest_SHA=sha(out/'compact_evidence/manifest.json'),
        tables_copied_exactly_from_final_report=True,engineering=True,conservative_solver_starts=0,Optimize=0,IIS=0))
    print(json.dumps(dict(stage=summary['stage'],body_SHA=sha(here/'body.md'),Optimize=0)))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--isolated-review',required=True);a=p.parse_args();finish(a.root,a.isolated_review)
