"""Engineering-only cold restore, frozen-byte and closed-receipt verification."""
from round104_common import *
import shutil
import round104_evidence as evidence

def main(label):
    from round100_idle import ensure_idle
    ensure_idle()
    q=read(OUT/'control01/identity.json');baseline=read(OUT/'baseline.json')
    checked=0
    for name,expected in {**q['source_hashes'],**q['helpers'],**baseline['protected_files']}.items():
        assert sha(ROOT/name)==expected,name;checked+=1
    assert sha(BUILD/'ExactEBRP.exe')==q['candidate_binary_sha256']
    assert sha(Path('D:/gurobi1302/win64/bin/gurobi130.dll'))==q['dll_sha256']
    review=read(OUT/'diagnostics/final_review01/summary.json')
    rp='results/unified_exact_round104/review/round104_delivery_review.py'
    assert sha(ROOT/rp)==review['source_hashes'][rp]
    fees=read(OUT/'fees_summary.json');receipts=list((OUT/'fees').glob('*/receipt.json'))
    assert len(receipts)==fees['wrapper_starts']==len(list((OUT/'fees').glob('*/launch.json')))
    assert sum(read(p)['outer_seconds'] for p in receipts)==fees['charged_outer_seconds']
    assert sha(OUT/'fees.csv')==fees['fee_csv_sha256']
    assert fees['conservative_counted_starts']<=72 and fees['charged_outer_seconds']<=80000
    assert all(read(p)['exit_code'] is not None for p in receipts)
    syntax=[]
    for p in sorted((ROOT/'scripts').glob('round104*.py')):
        if p.name.startswith('round104_make_'):continue
        compile(p.read_text(encoding='utf-8'),str(p),'exec');syntax.append(p.name)
    cold=ROOT/'build/research'/('round104-evidence-'+label)
    cold.mkdir(exist_ok=False)
    target=cold/'results/unified_exact_round104/compact_evidence';target.mkdir(parents=True)
    for n in ['manifest.json','evidence.tar.gz']:shutil.copyfile(OUT/'compact_evidence'/n,target/n)
    evidence.ROOT=cold;evidence.OUT=cold/'results/unified_exact_round104'
    evidence.verify(restore=True)
    manifest=read(target/'manifest.json')
    for r in manifest['files']:assert sha(cold/r['path'])==r['sha256']
    engineering=[dict(label=p.parent.name,**read(p),receipt_sha256=sha(p))
        for p in sorted((OUT/'engineering').glob('*/receipt.json'))]
    result=dict(passed=True,source_sha256=sha(__file__),measured_source_head='339835c46c37f353c7cf9813ef749782098fff5d',
        frozen_source_helper_and_user_file_checks=checked,user_file_hashes_preserved=True,
        PE_sha256=q['candidate_binary_sha256'],DLL_sha256=q['dll_sha256'],
        byte_exact_cold_restore=True,cold_root=cold.relative_to(ROOT).as_posix(),cold_files=len(manifest['files']),
        archive_sha256=manifest['archive_sha256'],archive_bytes=manifest['archive_bytes'],
        closed_paid_receipts=len(receipts),charged_outer_seconds=fees['charged_outer_seconds'],
        conservative_counted_starts=fees['conservative_counted_starts'],syntax_files=syntax,
        closed_engineering_receipts_before_this_check=engineering,
        current_check_receipt='engineering/'+label+'/receipt.json',Optimize_calls=0,DP_calls=0,
        scope='Engineering byte/receipt/syntax verification only; no repeated numerical review or performance')
    write(OUT/'delivery_verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='closed_engineering_receipts_before_this_check'}))

if __name__=='__main__':main(sys.argv[1])
