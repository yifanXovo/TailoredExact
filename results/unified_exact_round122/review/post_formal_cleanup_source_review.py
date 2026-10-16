"""Static-only initial cleanup plan review. Never executes the plan or lists targets."""
import datetime,time
from independent_review_round122 import ROOT,OUT,REVIEW,sha,save_receipt

def run():
    tick=time.perf_counter();source=OUT/'engineering/cleanup_round122.ps1'
    expected='c79f625c074338088964a5b5bd46aa5123ada8d4998479de34d902bc57bb6786'
    assert sha(source)==expected
    text=source.read_text(encoding='utf-8-sig')
    assert text.count('Remove-Item -LiteralPath $taskChecked -Recurse -Force')==1
    assert "[IO.Path]::GetFullPath($taskPath).TrimEnd('\\')" in text
    assert '$taskTargets -notcontains $taskAbsolute' in text and text.count('[IO.FileAttributes]::ReparsePoint')==2
    assert '$taskReplay.scientific_commit' not in text and '$taskManifest.parts.Count' not in text
    assert "candidate_prerecord=(Join-Path $taskEvidence 'cleanup_candidates.json')" in text
    result=dict(decision='REQUIRES_GATE_BINDING_AND_FINAL_STATUS_HARDENING',scope='Actual bounded read-only source/PowerShell-AST review of planned cleanup v1 only; not cleanup execution admission.',
        reviewer='independent executor /root/contract_review',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source_SHA=sha(source),review_script_SHA=sha(__file__),PowerShell_parser_errors=0,
        native_PS_delete_command='Remove-Item -LiteralPath $taskChecked -Recurse -Force',delete_command_count=1,
        containment_findings='Four literal E-work targets; absolute normalization and exact whitelist; all ancestor/internal reparse entries rejected; native literal-path deletion; write-ahead and per-target external receipts.',
        asset_findings='Current raw/carrier/main/old trees and frozen PE/DLL/core lie outside all four targets; necessary assets and protected main dirty bytes are explicitly rehashed.',
        required_changes=[
            'Bind replay/public-export receipt scientific_commit to scienceA9ed88... and fresh_empty_root to exact taskRestore; require the intended typed32/48 stage and boundary success, rather than generic counts/pass flags.',
            'Hash-bind normalized manifest to the completed public-export metadata and exact6 parts. Validate each retained part path remains in the canonical directory and outside deletion targets; preserve size/SHA checks. Current empty parts would vacuously pass while receipt claims six verified parts.',
            'Actually read cleanup_candidates.json, verify its exact normalized four-target set and bind its SHA into the pre-delete external receipt.',
            'Persist explicit cleanup_passed based on no failed removals/all four absent plus carrier/runtime/main postchecks; return failure or require caller to inspect that field, rather than ordinary exit0 despite a nonempty failed list.',
            'Recheck protected main HEAD after deletion if claiming all main-state protection after cleanup.'
        ],
        no_delete_or_target_enumeration=True,restored_checker_untouched=True,
        native_starts=0,Optimize=0,network_requests=0,Git_commands=0,existing_source_or_payload_member_edits=0,seconds=time.perf_counter()-tick)
    save_receipt('post_formal_cleanup_source_review.json',result)

if __name__=='__main__':run()
