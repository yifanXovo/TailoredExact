"""Exact-byte compact witness package, only after all performance is idle.

No Optimize, mathematical re-solve, broad historical scan or binary upload.
Compression is engineering; numerical readers are separately charged.
"""
import sys,json,shutil,gzip
from round103_common import *
from round100_idle import ensure_idle

def main(label,report,fees,campaigns):
    ensure_idle();target=OUT/label;target.mkdir(exist_ok=False);copies=[];indexed=[];pool={};large_pool={}
    def keep(source,relative):
        p=Path(source);rel=Path(relative);dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        compressed=p.stat().st_size>=8192
        digest=sha(p)
        if compressed and digest in large_pool:
            first=large_pool[digest]
            copies.append(dict(first,source=p.relative_to(ROOT).as_posix(),deduplicated=True))
            return
        if compressed:
            dest=dest.with_name(dest.name+'.gz')
            with p.open('rb') as original,dest.open('xb') as raw:
                with gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as stream:shutil.copyfileobj(original,stream)
        else:
            assert not dest.exists();shutil.copy2(p,dest);assert sha(p)==sha(dest)
        copies.append(dict(source=p.relative_to(ROOT).as_posix(),target=dest.relative_to(ROOT).as_posix(),
            source_sha256=digest,sha256=sha(dest),source_bytes=p.stat().st_size,bytes=dest.stat().st_size,
            compression='gzip exact original bytes' if compressed else None))
        if compressed:large_pool[digest]=copies[-1]
    def model(source,expected):
        p=Path(source);assert sha(p)==expected
        if expected not in pool:
            keep(p,Path('models')/(expected+'.lp'));pool[expected]=copies[-1]['target']
        return pool[expected]
    selected=['F2_raw01','F2_native01','C2_raw01','C2_native02','F5_raw01','F5_native01','N2_raw01','N2_native01',
        'capacity_C2_01','capacity_F5_01','capacity_F2_01','capacity_anchor_C2_01','capacity_anchor_F5_01',
        'finalpoint_F5_01','anchor_selection_C2_01','anchor_selection_F5_01','anchor_point_C2_01','anchor_point_F5_01',
        'primal_F5_base01','primal_F5_anchor01','same_domain01','same_domain02','C2_native01','root_faults01']
    selected += [p.name for p in (OUT/'diagnostics').iterdir() if p.is_dir() and
        (p.name.startswith('final_evidence') or p.name.startswith('small_hull'))]
    for name in selected:
        directory=OUT/'diagnostics'/name;assert directory.exists(),directory
        for p in directory.iterdir():
            if p.is_file() and p.suffix in ['.json','.jsonl','.txt']:
                keep(p,Path('diagnostics')/name/p.name)
        summary=read(directory/'summary.json') if (directory/'summary.json').exists() else {}
        if 'iterations' in summary:
            last=directory/f'iteration_{len(summary["iterations"])-1:03d}'
            for p in last.iterdir():
                if p.suffix=='.json':keep(p,Path('diagnostics')/name/last.name/p.name)
        if name.startswith(('final_evidence','small_hull')):
            for p in directory.rglob('*'):
                if p.is_file() and p.parent!=directory and p.suffix in ['.json','.jsonl','.txt']:
                    keep(p,Path('diagnostics')/name/p.relative_to(directory))
            if (directory/'reference/off.lp').exists():
                model(directory/'reference/off.lp',sha(directory/'reference/off.lp'))
        plan=read(directory/'plan.json') if (directory/'plan.json').exists() else {}
        if 'source' in plan and 'source_sha256' in plan:
            model(ROOT/plan['source'],plan['source_sha256'])
    for p in (OUT/'review').iterdir():
        if p.is_file():keep(p,Path('review')/p.name)
    for name in campaigns:
        camp=OUT/name;q=read(camp/'identity.json')
        records=[json.loads(x) for x in (camp/'summary.jsonl').read_text().splitlines()]
        assert len(records)==len(q['launches']) and all(r['audit_passed'] for r in records)
        for namefile in ['identity.json','summary.jsonl','reference_batch_launch.json','reference_batch_receipt.json']:
            if (camp/namefile).exists():keep(camp/namefile,Path('campaigns')/name/namefile)
        for role,reference in q['references'].items():
            refdir=camp/'reference'/role
            for filename in ['launch.json','completion.json','build.json']:keep(refdir/filename,Path('campaigns')/name/'reference'/role/filename)
            model(refdir/'original.lp',reference['canonical_sha256'])
        for a in q['launches']:
            raw=Path(a['destination']);stem=f'{name}_{a["number"]:02d}_{a["id"]}_{a["arm"]}'
            for filename in ['completion.json','audit.json','result.json','affinity.json','phases.csv']:
                if (raw/filename).exists():keep(raw/filename,Path('runs')/stem/filename)
            ledger=raw/'external/paper_optimize_ledger.csv'
            if ledger.exists():keep(ledger,Path('runs')/stem/ledger.name)
            for pattern in ['*.round68.start.json','*.round68.start.values.csv']:
                for p in (raw/'external/native_logs').glob(pattern):
                    keep(p,Path('native')/stem/p.name)
            for p in (raw/'external/native_logs').glob('*.round102.*'):
                if p.suffix in ['.json','.jsonl']:
                    keep(p,Path('native')/stem/p.name)
            for p in (raw/'external/native_logs').glob('*.round103.*'):
                if p.suffix in ['.json','.jsonl']:
                    keep(p,Path('native')/stem/p.name)
                    if p.name.endswith('.contract.json'):
                        c=read(p);model(c['source_path'],c['source_sha256'])
                    if p.name.endswith('.summary.json'):
                        s=read(p)
                        if not s['cache_hit']:model(s['canonical_path'],s['canonical_sha256'])
    report_directories=[OUT/report,OUT/(report+'_clocks'),OUT/fees]
    for optional in ['reports_development01','reports_development01_clocks','fees_prefinal01','fees_prefinal02']:
        if (OUT/optional).exists():report_directories.append(OUT/optional)
    for directory in report_directories:
        for p in directory.rglob('*'):
            if p.is_file():keep(p,Path('report')/p.relative_to(OUT))
    for root in ['fees','engineering']:
        for p in (OUT/root).glob('*/receipt.json'):keep(p,Path('receipts')/p.relative_to(OUT))
    for p in (OUT/'fees').glob('*/launch.json'):
        keep(p,Path('launches')/p.relative_to(OUT))
        receipt=p.parent/'receipt.json'
        if receipt.exists() and read(receipt)['exit_code']!=0:
            for filename in ['stderr.log','stdout.log']:
                source=p.parent/filename
                if source.exists():keep(source,Path('failures')/source.relative_to(OUT))
    # Preserve compact successful engineering fixtures and intentional faults.
    for name in ['witness_tests03','hull_tests02']:
        p=OUT/'engineering'/name/'stdout.log'
        if p.exists():keep(p,Path('qualification')/name/p.name)
    for case in ['calls_open','rows_write']:
        d=OUT/'diagnostics/root_faults01'/case
        for filename in ['launch.json','completion.json','stderr.log']:
            keep(d/filename,Path('faults')/case/filename)
        for p in (d/'journal').iterdir():
            if p.is_file():keep(p,Path('faults')/case/'journal'/p.name)
    # Index this round's large local artifacts without copying every closure
    # iteration. This index is not itself a membership or validity proof.
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and target not in p.parents and p.stat().st_size>=262144:
            indexed.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
    for filename in ['ExactEBRP.exe','Round65ReferenceBuild.exe','Round103HullOracle.exe','Round98ModelExport.exe']:
        p=BUILD/filename;indexed.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p),local_binary_only=True))
    write(target/'manifest.json',dict(copies=copies,large_local_artifacts=indexed,original_LP_pool=pool,
        Optimize_calls=0,script_sha256=sha(__file__),
        scope='Eight full initial points, actual typed matrices, selected support/combination evidence, final capability points, all production rows/contracts/first standard-LP vectors, full source/canonical LP bytes, physical audited report witnesses, receipts/failures and independent review. Larger iteration data indexed, not independently re-proved. No executables/DLL/licenses/unrelated user files.'))
    sizes={c['target']:c['bytes'] for c in copies}
    print(json.dumps(dict(passed=True,copies=len(copies),unique_files=len(sizes),indexed=len(indexed),
        compressed_bytes=sum(sizes.values()),Optimize_calls=0)))

if __name__=='__main__':main(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4:])
