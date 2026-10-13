"""Bounded safe dependency selection and static setup; never starts Optimize."""
import io, json, shutil, sys, tarfile, time
from pathlib import Path
from round118_data import ROOT,OUT,BASE,read,write,sha,utc
import publication_security as security

def setup():
    tick=time.perf_counter(); m=read(ROOT/'results/unified_exact_round117/safe_evidence/manifest.json')
    prefixes=['results/unified_exact_round116/campaign/group01/raw/01_E20-C1_S0_P-GRB/',
        'results/unified_exact_round116/campaign/group01/raw/04_E20-C1_S0_M-B/',
        'results/unified_exact_round116/qualification/reference/H100/']
    exact={'reference/round100_confirmation/H100.txt'}
    selected={p:v for p,v in m['files'].items() if p in exact or any(p.startswith(k) for k in prefixes)}
    parts=[]
    for row in m['parts']:
        p=ROOT/row['path']; assert sha(p)==row['SHA'] and p.stat().st_size==row['bytes'];parts.append(p.read_bytes())
    restored=[]
    with tarfile.open(fileobj=io.BytesIO(b''.join(parts)),mode='r|gz') as arc:
        for member in arc:
            if member.name not in selected: continue
            security.Scanner.member_name(member.name); assert member.isfile()
            data=arc.extractfile(member).read(); expected=selected[member.name]
            assert security.sha(data)==expected['SHA'] and len(data)==expected['bytes']
            p=ROOT/member.name
            if p.exists():assert p.read_bytes()==data
            else:
                p.parent.mkdir(parents=True,exist_ok=True)
                with p.open('xb') as f:f.write(data)
            restored.append(member.name)
    assert set(restored)==set(selected)
    production=read(ROOT/'results/unified_exact_round116/production_identity.json')
    for p,h in production['source_bindings'].items():assert sha(ROOT/p)==h
    pe=ROOT/'build/research/round118-inherited/ExactEBRP.exe';pe.parent.mkdir(parents=True,exist_ok=True)
    original=Path('E:/codes/ExactEBRP-round116/build/research/round116-inherited/ExactEBRP.exe')
    assert sha(original)==production['production_PE_SHA']; assert not pe.exists();shutil.copyfile(original,pe)
    dll=Path('D:/gurobi1302/win64/bin/gurobi130.dll');assert sha(dll)==production['DLL_SHA']
    write(OUT/'production_identity.json',dict(production,actual_base=BASE,production_PE_path=pe.relative_to(ROOT).as_posix(),
        production_copied_not_compiled=True,DLL_path=str(dll),verified_UTC=utc(),source_files_checked=len(production['source_bindings'])))
    h=ROOT/'results/unified_exact_round116/qualification/reference/H100'
    dst=OUT/'qualification/reference/H100';dst.mkdir(parents=True,exist_ok=False)
    for name in ['original.lp','build.json']:shutil.copyfile(h/name,dst/name)
    write(OUT/'safe_dependency_receipt.json',dict(safe_manifest_SHA=sha(ROOT/'results/unified_exact_round117/safe_evidence/manifest.json'),
        safe_parts=m['parts'],selected_members=selected,selected_bytes=sum(q['bytes'] for q in selected.values()),
        complete_historical_carrier_restored=False,old_contaminated_carrier=False,network=False,
        V100_models_or_execution=False,production_PE_SHA=sha(pe),DLL_SHA=sha(dll),
        original_helpers_are_historical_authority_only=True,native_starts=0,Optimize=0,engineering_seconds=time.perf_counter()-tick))
    print(json.dumps(dict(selected_members=len(selected),selected_bytes=sum(q['bytes'] for q in selected.values()),PE_SHA=sha(pe),Optimize=0)))

if __name__=='__main__':setup()
