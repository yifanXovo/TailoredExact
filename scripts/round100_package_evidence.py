"""Compact read-only delivery packaging; no solver or model regeneration."""
import csv,re,shutil
from round100_common import *
from round100_idle import ensure_idle

CAMPAIGNS=['development01','certification_CF01','certification_N201','holdout01']
PRIVATE=re.compile(r'Username|WLS|LicenseID|TokenServer|license|ComputeServer|ServerPassword|CSManager|CSAuth|CloudAccessID|CloudSecretKey|Password|Secret',re.I)

def main():
    ensure_idle()
    target=OUT/'evidence';target.mkdir(exist_ok=False);index=[];redactions=[]
    def record(path,scope):
        path=Path(path)
        index.append(dict(path=path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
            sha256=sha(path),bytes=path.stat().st_size,scope=scope))
    def copy(path,destination):
        path=Path(path);destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
        assert not destination.exists();shutil.copy2(path,destination);record(path,'compact original copied to evidence')
    def sanitized_log(path,destination):
        lines=Path(path).read_text(encoding='utf-8',errors='replace').splitlines()
        cleaned=[s.rstrip() for s in lines if not PRIVATE.search(s)]
        omitted=0
        if sum(len(s)+1 for s in cleaned)>1024*1024:
            omitted=max(0,len(cleaned)-400)
            cleaned=cleaned[:150]+[f'[delivery excerpt: {omitted} middle lines omitted; original indexed by SHA256]']+cleaned[-250:]
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as f:f.write('\n'.join(cleaned)+'\n')
        redactions.append(dict(original_path=Path(path).relative_to(ROOT).as_posix(),original_sha256=sha(path),
            sanitized_path=destination.relative_to(ROOT).as_posix(),sanitized_sha256=sha(destination),
            private_lines_removed=sum(bool(PRIVATE.search(s)) for s in lines),middle_lines_omitted=omitted,
            scope='private lines excluded; trailing whitespace stripped; logs above 1 MiB explicitly excerpted; complete native call ledger retained'))
        record(path,'local original native log; sanitized full log or explicit excerpt committed')
    for name in CAMPAIGNS:
        camp=OUT/name
        assert camp.exists(),f'required completed campaign missing: {name}'
        dest=target/'campaigns'/name
        q=read(camp/'identity.json')
        done=[json.loads(s) for s in (camp/'summary.jsonl').read_text().splitlines()]
        assert len(done)==len(q['launches']) and all(r['audit_passed'] for r in done)
        for filename in ['identity.json','summary.jsonl','reference_batch_receipt.json']:
            if (camp/filename).exists():copy(camp/filename,dest/filename)
        for a in q['launches']:
            d=Path(a['destination'])
            for p in (d/'external/models').glob('*.lp'):record(p,'actual typed canonical model; retained locally without regeneration')
            for p in (d/'external/native_logs').glob('*.round68.start*'):record(p,'actual complete submitted Start and per-column native readback')
            for filename in ['result.json','observations.json','phases.csv']:
                if (d/filename).exists():record(d/filename,'complete local performance evidence; compact endpoint/checkpoints committed')
            initial=d/'external/initial_witness.json'
            if initial.exists():copy(initial,dest/'startups'/f'{a["number"]:02d}_{a["id"]}_{a["arm"]}.json')
            logs=[d/'native.log'] if a['arm']=='P-GRB' else sorted((d/'external/native_logs').glob('*.gurobi.log'))
            for p in logs:
                if p.exists():sanitized_log(p,target/'native_logs'/name/d.name/p.name)
        for p in (camp/'reference').rglob('*'):
            if p.is_file() and p.suffix in ['.lp','.json']:record(p,'self-paid original plain reference model/identity')
    for parent in ['qualification','diagnostic_receipts','engineering']:
        root=OUT/parent
        if not root.exists():continue
        for folder in sorted(root.iterdir()):
            if not folder.is_dir():continue
            for filename in ['launch.json','receipt.json','actual_calls_supplement.json']:
                if (folder/filename).exists():copy(folder/filename,target/parent/folder.name/filename)
            if (folder/'stderr.log').exists() and (folder/'receipt.json').exists() and read(folder/'receipt.json').get('exit_code') not in [0,None]:
                sanitized_log(folder/'stderr.log',target/'failures'/f'{parent}_{folder.name}.stderr.txt')
    for p in sorted((OUT/'qualification').glob('dev_start_*.json')):copy(p,target/'qualification'/p.name)
    for name in ['micro01','matrix01']:
        folder=OUT/'diagnostics'/name
        for p in sorted(folder.iterdir()):
            if p.is_file() and (p.suffix=='.json' or p.name=='calls.jsonl'):copy(p,target/'diagnostics'/name/p.name)
            elif p.is_file():record(p,'local raw qualification vector/LP/native evidence')
    for parent in ['exports','micro_models01']:
        for p in (OUT/parent).rglob('*'):
            if p.is_file():record(p,'actual finite qualification writer model/identity')
    for filename in ['ExactEBRP.exe','Round100ModelExport.exe','Round65ReferenceBuild.exe','Round100QuantityTests.exe']:
        if (BUILD/filename).exists():record(BUILD/filename,'actual frozen local experimental binary')
    record(Path('D:/gurobi1302/win64/bin/gurobi130.dll'),'sole production native engine')
    trajectory=OUT/'complete_results_final/trajectories.csv'
    record(trajectory,'complete local trajectory; all physical events and scoped checkpoints committed separately')
    with trajectory.open(newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f);fields=reader.fieldnames;rows=[];best={}
        for row in reader:
            if row['source'] not in ['committed_bound','committed_witness']:continue
            key=(row['campaign'],row['number']);u,l=best.get(key,(None,None));keep=False
            if row['source']=='committed_witness' and row.get('U'):
                value=float(row['U'])
                if u is None or value<u:u=value;keep=True
            if row.get('global_available','').lower()=='true' and row.get('global_bound'):
                value=float(row['global_bound'])
                if l is None or value>l:l=value;keep=True
            best[key]=(u,l)
            if keep:rows.append(row)
    with (target/'legal_bound_improvements.csv').open('x',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    write(target/'native_log_redactions.json',redactions)
    write(OUT/'local_artifact_index.json',dict(local_only_large_artifacts=True,files=index,no_model_regeneration=True,
        scope='exact local bytes; SHA indexing is not an independent search reproduction; compact delivery preserves all physical witness events, audited endpoints, native calls and covered checkpoints',
        script_sha256=sha(__file__)))
    print(json.dumps(dict(indexed_files=len(index),native_logs_sanitized=len(redactions),legal_improvement_events=len(rows),Optimize=0)))

if __name__=='__main__':main()
