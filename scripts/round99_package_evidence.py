"""Read-only compact packaging; excludes licenses, binaries and big matrices."""
import re,shutil
from round99_common import *

CAMPAIGNS=['factorial01','repeat01','linked01','long01','confirmation01','confirmation_recovery01']
PRIVATE=re.compile(r'Username|WLS|LicenseID|TokenServer|license|ComputeServer|ServerPassword|CSManager|CSAuth|CloudAccessID|CloudSecretKey|Password|Secret',re.I)

def main():
    target=OUT/'evidence';target.mkdir(exist_ok=False);index=[];redactions=[]
    def record(path,scope):
        path=Path(path)
        index.append(dict(path=path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
                          sha256=sha(path),bytes=path.stat().st_size,scope=scope))
    def copy(path,destination):
        path=Path(path);destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
        assert not destination.exists();shutil.copy2(path,destination);record(path,'compact copy retained in evidence')
    def sanitized_log(path,destination):
        lines=Path(path).read_text(encoding='utf-8',errors='replace').splitlines()
        cleaned=[s.rstrip() for s in lines if not PRIVATE.search(s)]
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as f:f.write('\n'.join(cleaned)+'\n')
        redactions.append(dict(original_path=Path(path).relative_to(ROOT).as_posix(),original_sha256=sha(path),
            sanitized_path=destination.relative_to(ROOT).as_posix(),sanitized_sha256=sha(destination),
            removed_lines=len(lines)-len(cleaned),scope='license/credential-bearing lines omitted; native numeric body unchanged; trailing whitespace stripped'))
        record(path,'original native log retained locally; sanitized derivative committed')
    for name in CAMPAIGNS:
        camp=OUT/name;dest=target/'campaigns'/name
        for filename in ['identity.json','summary.jsonl','reference_batch_receipt.json','interruption_manifest.json','recovery_plan.json']:
            if (camp/filename).exists():copy(camp/filename,dest/filename)
        q=read(camp/'identity.json')
        for a in q['launches']:
            d=Path(a['destination'])
            if not d.exists():continue
            for p in (d/'external/models').glob('*.lp'):record(p,'actual typed canonical model; no recreated replacement')
            for p in (d/'external/native_logs').glob('*.round68.start*'):record(p,'actual native submitted Start and per-column readback')
            initial=d/'external/initial_witness.json'
            if initial.exists():copy(initial,dest/'startups'/f'{a["number"]:02d}_{a["id"]}_{a["arm"]}.json')
            logs=[d/'native.log'] if a['arm']=='P-GRB' else list((d/'external/native_logs').glob('*.gurobi.log'))
            for p in logs:
                if p.exists():sanitized_log(p,target/'native_logs'/name/d.name/p.name)
        for p in (camp/'reference').rglob('*'):
            if p.is_file() and p.suffix in ['.lp','.json']:record(p,'paid plain reference or exact copy-only reference')
    for parent in ['qualification','diagnostic_receipts','engineering']:
        for folder in (OUT/parent).iterdir():
            if not folder.is_dir():continue
            for filename in ['launch.json','receipt.json','actual_calls_supplement.json']:
                if (folder/filename).exists():copy(folder/filename,target/parent/folder.name/filename)
            if (folder/'stderr.log').exists() and (folder/'receipt.json').exists():
                receipt=read(folder/'receipt.json')
                if receipt.get('exit_code') not in [0,None]:
                    sanitized_log(folder/'stderr.log',target/'failures'/f'{parent}_{folder.name}.stderr.txt')
    for name in ['micro02','lp_F201','lp_R98-C101','lp_R98-C201','linked_qual01','native_scope_followup03','native_scope_followup04']:
        folder=OUT/'diagnostics'/name
        if not folder.exists():continue
        for p in folder.iterdir():
            if p.is_file() and (p.suffix=='.json' or p.name=='calls.jsonl'):
                copy(p,target/'diagnostics'/name/p.name)
            elif p.is_file():record(p,'local raw LP/presolve/vector diagnostic artifact')
    for p in (OUT/'frozen/v1').rglob('*'):
        if p.is_file():record(p,'pre-mutation actual v1 source/helper/binary snapshot')
    for p in (OUT/'inner_results02').rglob('native.log'):
        sanitized_log(p,target/'inner_native_logs'/p.parent.name/'native.log')
    for filename in ['ExactEBRP.exe','Round99ModelExport.exe','Round65ReferenceBuild.exe','Round99DiscreteTests.exe']:
        for build in ['round99-discrete-v1','round99-discrete-v2']:
            p=ROOT/'build/research'/build/filename
            if p.exists():record(p,'local actual experimental binary')
    record(Path('D:/gurobi1302/win64/bin/gurobi130.dll'),'sole production native engine')
    write(target/'native_log_redactions.json',redactions)
    write(OUT/'local_artifact_index.json',dict(local_only_large_artifacts=True,files=index,
        no_model_regeneration=True,scope='exact local bytes; availability required for full local matrix audit, not full solver reproduction',
        script_sha256=sha(__file__)))
    events=[]
    path=OUT/'confirmation01/raw/07_N3_M-B/interrupted_observations.json'
    for v in read(path):
        if v['payload']['kind']=='witness':events.append(dict(available_seconds=v['effective_available_seconds'],
            event_sha256=v['sha256'],event=v['payload'],scope='interrupted attempt only; excluded from formal pairs'))
    write(target/'interrupted_physical_events.json',events)
    print(json.dumps(dict(indexed_files=len(index),native_logs_sanitized=len(redactions),scope='compact packaging only; no native call')))

if __name__=='__main__':main()
