"""R105 selection with the inherited exact-byte pack/verify/restore engine."""
from round105_common import *
import round104_evidence as archive
from pathlib import Path
import json

def selected():
    files=set()
    def add(path):
        p=Path(path).resolve();assert p.is_file() and p.is_relative_to(ROOT)
        assert p.suffix.lower() not in ['.dll','.exe','.lic','.key']
        files.add(p)
    def tree(path):
        for p in Path(path).rglob('*'):
            if p.is_file():add(p)
    for camp in sorted(OUT.iterdir()):
        if not (camp/'identity.json').exists():continue
        q=read(camp/'identity.json');add(camp/'identity.json')
        for p in camp.glob('*.json*'):add(p)
        tree(camp/'reference')
        for launch in q['launches']:
            add(ROOT/launch['panel']['input_path'])
            d=Path(launch['destination'])
            if not d.exists():continue
            for p in d.iterdir():
                if p.is_file():add(p)
            observed=d/'observations.json'
            if observed.exists():
                for e in read(observed):
                    if e['payload']['kind']=='bound':continue
                    for suffix in ['json','commit']:
                        p=d/'journal'/('event_'+str(e['sequence'])+'.'+suffix)
                        if p.exists():add(p)
            tree(d/'hga.csv.exchange');tree(d/'external')
    for category in ['fees','engineering']:
        for d in (OUT/category).iterdir():
            if not d.is_dir() or not (d/'receipt.json').exists():continue
            for n in ['launch.json','receipt.json','process.json','stdout.log','stderr.log']:
                p=d/n
                if p.exists():add(p)
    tree(OUT/'modes');tree(OUT/'mode_batch01');tree(OUT/'review')
    tree(OUT/'reports01');tree(OUT/'reports02')
    # Final matching core qualification and the targeted assignment/deadline
    # extension. Earlier repeated models remain local; all paid receipts stay.
    tree(OUT/'qualification/native04');tree(OUT/'qualification/native_added01')
    for d in (OUT/'qualification').iterdir():
        p=d/'qualification.csv'
        if p.exists():add(p)
    for p in OUT.glob('*.json'):
        add(p)
    return sorted(files)

if __name__=='__main__':
    assert sys.argv[1] in ['pack','verify','restore']
    archive.OUT=OUT;archive.selected=selected
    if sys.argv[1]=='pack':
        archive.pack()
        manifest=OUT/'compact_evidence/manifest.json'
        q=read(manifest)
        q['selection_source_sha256']=sha(__file__)
        q['omitted']='Duplicate scalar-bound journal files; earlier repeated native qualification models except final native04 and targeted native-added. All corresponding paid receipts and qualification CSVs retained; all formal/real-mode/core/deadline/review model and witness bytes retained.'
        manifest.write_text(json.dumps(q,indent=2)+'\n',encoding='utf-8')
    else:
        archive.verify(sys.argv[1]=='restore')
