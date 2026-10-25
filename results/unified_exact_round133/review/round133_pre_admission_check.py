"""Independent read-only identity checks after the production source freeze.

No solver/runtime binding, compilation or mathematical point replay. This is
not D admission; the final reader and matrices are still pending.
"""
from pathlib import Path
import datetime, hashlib, json, subprocess, time, zipfile

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/unified_exact_round133'
REVIEW=OUT/'review'
COMMIT='4507c3554c6544048d307168779c8757f53cc5ae'
CANDIDATE_SHA='101e8f75d2675d1f728ddd8aa4010d0b57821218e730a7b06207239af6a997b2'

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1048576),b''):h.update(chunk)
    return h.hexdigest()
def write(path,value):
    assert not path.exists(),'Preserve prior review and its actual source identities'
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')

def main():
    tick=time.perf_counter();candidate_path=OUT/'candidate_manifest.json'
    assert sha(candidate_path)==CANDIDATE_SHA
    candidate=read(candidate_path);build_path=OUT/'candidate_build.json';build=read(build_path)
    assert sha(build_path)==candidate['build_manifest_SHA']
    assert candidate['source_commit']==COMMIT
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()==COMMIT
    checked=[]
    for name,digest in candidate['source_hashes'].items():
        assert sha(ROOT/name)==digest,name
        checked.append(name)
    archive=ROOT/candidate['executed_source_bytes']['path']
    assert sha(archive)==candidate['executed_source_bytes']['SHA']
    with zipfile.ZipFile(archive) as z:
        expected=set(candidate['source_hashes'])|{'generated/CplexBaselineResearch.cpp'}
        assert len(z.namelist())==len(set(z.namelist()))==len(expected)
        assert set(z.namelist())==expected
        for name,digest in candidate['source_hashes'].items():
            assert hashlib.sha256(z.read(name)).hexdigest()==digest,name
        generated=build['generated_research_source']
        assert hashlib.sha256(z.read('generated/CplexBaselineResearch.cpp')).hexdigest()==generated['SHA']
        assert sha(generated['path'])==generated['SHA']
    binaries=[]
    for label,row in build['binaries'].items():
        assert sha(row['PE'])==row['PE_SHA'] and sha(row['DLL'])==row['DLL_SHA']
        for key in ('main_object','compact_object'):
            assert sha(row[key]['path'])==row[key]['SHA']
        binaries.append(dict(kind=label,PE_SHA=row['PE_SHA'],DLL_SHA=row['DLL_SHA']))
    assert sha(build['reused_archive']['path'])==build['reused_archive']['SHA']
    assert sha('D:/msys64/ucrt64/bin/g++.exe')==build['compiler_SHA']
    original_paths={'production_SHA':'E:/codes/ExactEBRP-work/build-cache/round130/ExactEBRP.exe',
                    'research_SHA':'E:/codes/ExactEBRP-work/build-cache/round132/Round132Research.exe'}
    for key,path in original_paths.items():assert sha(path)==candidate['original_binaries_unchanged'][key]
    abi_path=OUT/'qualification/ABI.json';abi=read(abi_path)
    assert abi['PASS'] and abi['layouts']['previous']==abi['layouts']['candidate']
    for name,digest in abi['candidate_headers'].items():assert sha(ROOT/'include'/name)==digest
    tests=[]
    for name in ('native_evidence_journal_tests_05','round133_terminal_tests_05',
                 'round133_inclusive_cutoff_tests_02','round27_paper_scheduling_tests_01'):
        folder=OUT/'fees'/('test_run_'+name);receipt=read(folder/'receipt.json')
        assert receipt['exit_code']==0 and receipt['exit_observed'] and not receipt['timeout']
        tests.append(dict(name=name,receipt_SHA=sha(folder/'receipt.json'),
            stdout_SHA=sha(folder/'stdout.log'),stdout=(folder/'stdout.log').read_text().strip()))
    inputs=read(OUT/'infra/staged_inputs.json')['inputs']
    for value in inputs:
        assert sha(ROOT/value['path'])==value['SHA']
        content=subprocess.check_output(['git','show',value['source_commit']+':'+value['source_path']],cwd=ROOT)
        assert hashlib.sha256(content).hexdigest()==value['SHA']
    evidence=dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        reviewer='/root/reliability_review',source_commit=COMMIT,candidate_manifest_SHA=CANDIDATE_SHA,
        build_manifest_SHA=sha(build_path),actual_source_and_header_files=len(checked),
        source_zip_members=len(expected),executed_source_zip_SHA=sha(archive),
        current_and_zipped_executed_source_bytes_match=True,actual_binary_identities=binaries,
        original_PE_identities_preserved=True,main_compact_archive_compiler_identities_checked=True,
        ABI_receipt_SHA=sha(abi_path),ABI_layouts=abi['layouts'],core_test_receipts=tests,
        original_input_files_checked=len(inputs),original_input_bytes=sum(row['bytes'] for row in inputs),
        actual_input_bytes_equal_fixed_commit_sources=True,native_Optimize=0,native_module_imports=0,
        compilation=0,repeated_exact_point_calculation=0,outer_seconds=time.perf_counter()-tick)
    write(REVIEW/'pre_admission_identity_checks.json',evidence)
    review=dict(schema='round133-independent-pre-admission-v1',UTC=evidence['UTC'],
        reviewer='/root/reliability_review',primary_implementer='/root',
        decision='NO_REMAINING_PRODUCTION_STATIC_BLOCKER_IN_REVIEWED_SCOPE',
        D1_admission='NOT_GRANTED_FINAL_READER_AND_MATRIX_FREEZE_PENDING',
        candidate_manifest_SHA=CANDIDATE_SHA,source_commit=COMMIT,
        identity_check_receipt_SHA=sha(REVIEW/'pre_admission_identity_checks.json'),
        corrected_findings=['Separate local qualification from cover completeness and raw observations',
            'Match declared requested/read-back settings and preserve distinct failure reasons',
            'Test raw source contradictions before cutoff-complement conversion',
            'Latch late finite-bound and INFEASIBLE contradictions, including later-call witnesses',
            'Reject failed/unknown status and solution-count reads rather than fabricate values',
            'Apply physical-gap-open to terminal and reachable C6 optimal return',
            'Abandon all dependent native control state to a new full-domain open floor0 state',
            'Preserve existing Scope/Request/Outcome ABI while recording qualification reason',
            'Remove proof-only artificial infeasibility from both inclusive cutoff emitters'],
        retained_positive_paths=['Qualified local bounds with incomplete global cover',
            'Qualified genuine native infeasibility and cutoff complement',
            'Normal positive objective closure and exact complete child disjunction'],
        diagnostic_readout_repair='Independent review accepts immutable raw-point-bound reuse and physical F repair; replay does not reproduce original native-under-physical gap',
        legacy_D3_policy='Known old artificial marker may receive complete UNEVALUABLE closeout only after complete model/producer/H/Start/physical/return/clock audit; no analytic qualification upgrade',
        not_approved=['Automatic transfer of diagnostics to D starts/cutoffs/bounds',
            'Use of an actual native Y-box as an independently proved physical-domain box',
            'Qualification of A==c or A<c artificial-row calls by claiming the physical domain is empty'],
        remaining_before_formal_qualification=['Freeze final reader and common/campaign helper identities, including complete old-marker UNEVALUABLE disposition',
            'Run or bind targeted pure reader fault checks for the final changed reader',
            'Freeze D1 and conditional D3 matrices with exact identities, order, parameters, caps and readout policy',
            'Issue independent final freeze admission and separate D2 small-native admission before launch'],
        later_required=['Observe D1/D2 actual path coverage and qualification, and conditional complete D3 comparisons',
            'Review final manuscript/status axes and public no-native recovery evidence'],
        scope_limits=['No universal exact-arithmetic MIP or invisible native-tree correctness claim',
            'Closed C5/coalescing/R119 modes are outside this finite active S2 review',
            'No new reviewer Optimize, compilation or repeated rational point calculation'])
    write(REVIEW/'pre_admission.json',review)
    print(json.dumps(dict(status='PRE_ADMISSION_ONLY',sources=len(checked),source_zip_members=len(expected),
        original_inputs=len(inputs),native_Optimize=0,seconds=time.perf_counter()-tick)))

if __name__=='__main__':main()
