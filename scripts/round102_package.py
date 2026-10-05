"""Compact exact-byte evidence and explicit large-artifact index, after solves.
No broad historical scan, DLL/license/binary submission or native Optimize.
"""
import sys,json,shutil,gzip
from pathlib import Path
from round102_common import *
from round100_idle import ensure_idle

def main(label,campaigns,report):
    ensure_idle();target=OUT/label;target.mkdir(exist_ok=False);copies=[];large=[]
    def copy(p,rel):
        p=Path(p);d=target/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
        assert sha(p)==sha(d);copies.append(dict(source=p.relative_to(ROOT).as_posix(),target=d.relative_to(ROOT).as_posix(),sha256=sha(d),bytes=d.stat().st_size))
    for role in ['F2','R98-C2','R99-N2','F5']:
        for name in ['S0.json','S1.json','actual-direction.json','fixed-charge.json','strengthened_point.json']:
            copy(OUT/'diagnostics/lp01'/role/name,Path('lp')/role/name)
    for p in ['diagnostics/lp01/summary.json','diagnostics/screen01/summary.json',
              'diagnostics/cpp_replay01/summary.json','diagnostics/native_points01/summary.json',
              'diagnostics/F5_actual_export_redundancy.json','engineering/fault_reader01.json',
              'engineering/build04/receipt.json','engineering/faults02/stdout.log',
              'engineering/fault_reader_final01.json']:
        copy(OUT/p,Path('qualification')/p)
    for file in (OUT/'diagnostics').glob('final_*/summary.json'):copy(file,Path('qualification')/file.relative_to(OUT))
    for file in (OUT/'diagnostics').glob('prelong_*/summary.json'):copy(file,Path('qualification')/file.relative_to(OUT))
    # Full typed F2 matrix plus compressed original first native vector enable
    # independent original-row residual checks without a large native LP.
    old=ROOT/'results/unified_exact_round101/diagnostics/lp01/F2'
    typed=old/'matrix.txt';assert typed.is_file()
    d=target/'lp/F2/typed_old_matrix.txt.gz';d.write_bytes(gzip.compress(typed.read_bytes(),mtime=0))
    copies.append(dict(source=typed.relative_to(ROOT).as_posix(),target=d.relative_to(ROOT).as_posix(),source_sha256=sha(typed),sha256=sha(d),compression='gzip exact original bytes'))
    for name in campaigns:
        camp=OUT/name;q=read(camp/'identity.json');records=[json.loads(x) for x in (camp/'summary.jsonl').read_text().splitlines()]
        assert len(records)==len(q['launches']) and all(r['audit_passed'] for r in records)
        for file in ['identity.json','summary.jsonl','reference_batch_receipt.json']:
            if (camp/file).exists():copy(camp/file,Path('campaigns')/name/file)
        for a in q['launches']:
            raw=Path(a['destination']);stem=f'{name}_{a["number"]:02d}_{a["id"]}_{a["arm"]}'
            for p in (raw/'external/native_logs').glob('*.round102.summary.json'):
                copy(p,Path('native')/stem/p.name)
                for suffix in ['.contract.json','.certificates.jsonl','.point.json']:
                    v=Path(str(p).replace('.summary.json',suffix))
                    if v.exists():copy(v,Path('native')/stem/v.name)
            # Logs/models/full result remain local; endpoint physical routes and
            # receipt/audit copies are already compact in the report directory.
    for directory in [OUT/report,OUT/(report+'_clocks')]:
        for p in directory.rglob('*'):
            if p.is_file():copy(p,Path('report')/p.relative_to(OUT))
    for root in ['fees','engineering']:
        for p in (OUT/root).glob('*/receipt.json'):copy(p,Path('receipts')/p.relative_to(OUT))
    for p in (OUT/'fees').glob('*/launch.json'):
        receipt=p.parent/'receipt.json';allowance=p.parent/'failure_allowance.json'
        failed=receipt.exists() and read(receipt)['exit_code']!=0
        if failed or allowance.exists():
            copy(p,Path('failures')/p.relative_to(OUT))
            for filename in ['stderr.log','failure_allowance.json']:
                source=p.parent/filename
                if source.exists():copy(source,Path('failures')/source.relative_to(OUT))
    for r in read(OUT/'diagnostics/lp01/summary.json')['records']:
        p=ROOT/r['actual_source'];assert sha(p)==r['actual_sha256']
        large.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p),inherited_actual_LP=True))
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and target not in p.parents and p.stat().st_size>=262144:
            large.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
    for p in [BUILD/'ExactEBRP.exe',BUILD/'Round65ReferenceBuild.exe',BUILD/'Round102ServiceDiagnostic.exe']:
        large.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p),local_binary_only=True))
    write(target/'manifest.json',dict(copies=copies,large_local_artifacts=large,Optimize=0,script_sha256=sha(__file__),
        scope='Four explicit inherited LPs and this round local artifacts>=256KiB; real compact signed rows, full first-root points, LP maximization points, physical witnesses and audited receipts retained. Hashes index rather than replace evidence. Binaries/DLL/license/user files not submitted.'))
    print(json.dumps(dict(passed=True,copies=len(copies),large=len(large),Optimize=0)))

if __name__=='__main__':main(sys.argv[1],sys.argv[3:],sys.argv[2])
