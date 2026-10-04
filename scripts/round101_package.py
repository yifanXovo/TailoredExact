"""Compact exact-byte evidence plus local artifact index, after performance.
No Optimize; no binaries, large matrices, license files or broad old-tree scan.
"""
import json,shutil,sys
from round100_idle import ensure_idle
from round101_common import *
from round101_recover_scope import records_view,audit_view

def package(label,campaigns):
    ensure_idle();target=OUT/label;target.mkdir(exist_ok=False);copied=[];selected=[]
    def copy(source,relative):
        source=Path(source);dest=target/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,dest);assert sha(source)==sha(dest)
        copied.append(dict(source=source.relative_to(ROOT).as_posix(),target=dest.relative_to(ROOT).as_posix(),
            bytes=source.stat().st_size,sha256=sha(source)))
    for role in ['F2','R98-C2','R99-N2','F5']:
        folder=OUT/'diagnostics/lp01'/role
        for name in ['raw.point','raw.separation.json','implication_0.json','implication_1.json']:
            copy(folder/name,Path('lp')/role/name)
    for name in ['diagnostics/lp01/summary.json','diagnostics/reextension01/summary.json',
                 'diagnostics/pair_structure01/summary.json','diagnostics/numeric_replay01/summary.json',
                 'diagnostics/matrix_guards01/summary.json','qualification/pure05/stdout.log']:
        copy(OUT/name,Path('qualification')/name)
    for campaign in campaigns:
        folder=OUT/campaign;identity=read(folder/'identity.json')
        done=records_view(folder)
        assert len(done)==len(identity['launches']) and all(x['audit_passed'] for x in done)
        for name in ['identity.json','summary.jsonl','reference_batch_receipt.json']:
            if (folder/name).exists():copy(folder/name,Path('campaigns')/campaign/name)
        for launch in identity['launches']:
            raw=Path(launch['destination']);stem=f'{campaign}_{launch["number"]:02d}_{launch["id"]}_{launch["arm"]}'
            for file in ['completion.json','audit.json']:
                copy(raw/file,Path('runs')/stem/file)
            # Final physical routes are extracted without unrelated result fields.
            result=read(raw/'result.json') if (raw/'result.json').exists() else {}
            if not result:
                audited=audit_view(raw);observations=read(raw/'observations.json')
                witness=min(audited['witnesses'],key=lambda w:w['F'])
                event=next(r['payload'] for r in observations if r['sequence']==witness['sequence'])
                write(target/'runs'/stem/'interrupted_routes.json',dict(input_sha256=launch['panel']['input_sha256'],
                    routes=event['routes'],F=witness['F'],journal_sequence=witness['sequence'],
                    source_path=str((raw/'journal'/f'event_{witness["sequence"]}.json').relative_to(ROOT)),
                    scope='Audited committed physical witness from interrupted process; not a native final result'))
            if result.get('routes'):
                write(target/'runs'/stem/'final_routes.json',dict(input_sha256=launch['panel']['input_sha256'],
                    routes=result['routes'],F=result['upper_bound'],result_path=str((raw/'result.json').relative_to(ROOT)),
                    result_sha256=sha(raw/'result.json'),scope='Audited same-run final physical routes, not a new primal input'))
            for path in sorted((raw/'external/native_logs').glob('*.round101.summary.json')):
                prefix=path.name.removesuffix('.summary.json')
                copy(path,Path('native')/stem/(prefix+'.summary.json'))
                contract=path.with_name(prefix+'.contract.json');certs=path.with_name(prefix+'.certificates.jsonl')
                assert contract.exists() and certs.exists()
                lines=certs.read_bytes().splitlines(keepends=True);rows=[json.loads(x) for x in lines]
                if not rows:continue
                wanted={0,len(rows)-1}
                for condition in [lambda r:r['node']==0,lambda r:r['node']>0,
                                  lambda r:r['proof']['method']=='complete_subset_dp',
                                  lambda r:r['proof']['method']=='eligibility_slot_upper']:
                    first=next((i for i,r in enumerate(rows) if condition(r)),None)
                    if first is not None:wanted.add(first)
                copy(contract,Path('native')/stem/contract.name)
                dest=target/'native'/stem/(prefix+'.certificates.jsonl')
                dest.write_bytes(b''.join(lines[i] for i in sorted(wanted)))
                selected.append(dict(source=certs.relative_to(ROOT).as_posix(),source_sha256=sha(certs),
                    source_records=len(rows),retained_records=len(wanted),source_line_numbers=[i+1 for i in sorted(wanted)],
                    target=dest.relative_to(ROOT).as_posix(),target_sha256=sha(dest),byte_exact_records=True,
                    selection='first/last plus first root, positive-node, small DP and scalable row; evidence packaging only, no score filtering'))
    for p in sorted((OUT/'recovery06').glob('*.json')):
        copy(p,Path('recovery06')/p.name)
    # Hash only this round's local tree, with explicit inherited matrix additions.
    artifacts=[]
    for path in sorted(OUT.rglob('*')):
        if not path.is_file() or path==OUT/'preexisting_untracked_paths.txt':continue
        artifacts.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=sha(path)))
    for record in read(OUT/'diagnostics/lp01/summary.json')['records']:
        path=ROOT/record['actual_source'];assert sha(path)==record['actual_sha256']
        artifacts.append(dict(path=record['actual_source'],bytes=path.stat().st_size,sha256=record['actual_sha256'],
            inherited_actual_matrix=True))
    write(target/'manifest.json',dict(copies=copied,selected_native_records=selected,
        all_local_artifacts=artifacts,optimizer_calls=0,script_sha256=sha(__file__),
        exclusions=['This final manifest itself, to avoid self-hash recursion','Preexisting unrelated untracked-path inventory,103MB'],
        original_native01_PE_missing=True,
        scope='Complete local Round101 tree and four explicitly cited inherited matrices at packaging time; compact retained real rows/points/routes/receipts. Later final report/review/PR metadata are tracked separately. No native search rerun.'))
    print(json.dumps(dict(passed=True,local_files=len(artifacts),compact_copies=len(copied),native_samples=len(selected),Optimize=0)))

if __name__=='__main__':package(sys.argv[1],sys.argv[2:])
