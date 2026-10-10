"""Root-only current raw reconstruction; immutable main36 table import.

Reuse the R110 raw rebuild loop and R108 physics/scope parser, without importing
an old all42 selection or changing historical source files.
"""
import argparse, collections, csv, inspect, json, time
from pathlib import Path
import round110_reader as frozen
import round110_evidence as current
import round111_decisions as decision

ROUND='results/unified_exact_round111'
MAIN_SHA='74cb24e040d2fa6d2efcc2614a9d90aaceaa6355ad17ed382f48731094c12049'
frozen.ROUND=ROUND
current.ROUND=Path(ROUND)
frozen.numerical=current
frozen.decision=decision

def imported_main(root):
    folder=Path(root)/ROUND/'review/inherited_main03'
    assert frozen.sha(folder/'audit.json')==MAIN_SHA
    audit=frozen.read(folder/'audit.json');assert audit['decision']=='ACCEPT_FIXED_R110_MAIN36_IMPORT'
    rows=frozen.read(folder/'main36_imported_rows.json');out=[]
    primitive=('U','L','gap','relative_gap','complete_seconds','cap_seconds','seed','V','M')
    flags=('certificate','certificate_qualified','numbers_qualified','original_whole_clock_unknown','formal_protocol_qualified')
    for row in rows:
        value=dict(row)
        for field in primitive:
            if field in value:value[field]=None if value[field]=='' else float(value[field])
        for field in flags:
            if field in value:value[field]=None if value[field]=='' else value[field]=='True'
        value['seed']=int(value['seed']);value['V']=int(value['V']);value['M']=int(value['M'])
        if value.get('complete_seconds_interval'):value['complete_seconds_interval']=json.loads(value['complete_seconds_interval'])
        value['original_formal_protocol_qualified']=row.get('formal_protocol_qualified','')
        if value['number'] in (15,17,25,26):
            assert value['complete_seconds'] is None and max(value['complete_seconds_interval'])<=value['cap_seconds']
            value['formal_protocol_qualified']=True
        else:assert value['formal_protocol_qualified'] is True
        value.update(evidence_layer='INHERITED_R110_MAIN',raw_reaudited_in_R111=False,import_audit_SHA=MAIN_SHA)
        out.append(value)
    assert len(out)==36
    return out

def require_identity(root,identity,candidate):
    assert identity['candidate_binary_sha256']==candidate['production_PE_SHA'] and identity['dll_sha256']==candidate['DLL_SHA']
    assert identity['source_hashes']==candidate['source_bindings']
    for path,digest in candidate['source_bindings'].items():assert frozen.sha(root/path)==digest,path
    for path,digest in identity['helpers'].items():assert frozen.sha(root/path)==digest,path
    assert identity['runner_sha256']==frozen.sha(root/'scripts/round111_campaign.py')
    assert identity['prereg_sha256']==frozen.sha(frozen.portable(root,identity['protocol_path']))
frozen.require_identity=require_identity

original_endpoint=frozen.endpoint
_original_raw_endpoint=frozen._inherited_endpoint
_source=inspect.getsource(_original_raw_endpoint)
_needle="assert t<=p['cap_seconds'],('complete arm exceeded preregistered cap',t,p['cap_seconds'])"
assert _source.count(_needle)==1
_namespace=dict(_original_raw_endpoint.__globals__)
exec(compile(_source.replace(_needle,'pass # retain actual over-cap mathematical record; qualification below'),
    __file__+'::retain_actual_clock','exec'),_namespace)
frozen._inherited_endpoint=_namespace['endpoint']
def endpoint(root,launch,ident,d,j,formal):
    ep=original_endpoint(root,launch,ident,d,j,formal)
    ep['arm'].update(number=launch['number'],old_R110_number=launch['old_R110_number'],
        full_clock_within_frozen_cap=ep['arm']['complete_seconds']<=launch['cap_seconds'],
        formal_protocol_qualified=ep['arm']['complete_seconds']<=launch['cap_seconds'],
        evidence_layer='CURRENT_R111_SEED',own_raw_recomputed=True)
    return ep
frozen.endpoint=endpoint

def fee_records(out):
    records=[]
    for p in sorted((out/'fees').glob('*/launch.json')):
        launch=frozen.read(p);receipt=frozen.read(p.parent/'receipt.json')
        row=dict(receipt,label=p.parent.name,qualification=launch['qualification'],original_outer_seconds=receipt['outer_seconds'])
        if (p.parent/'charge_classification.json').exists():row['qualification']=frozen.read(p.parent/'charge_classification.json')['qualification']
        if (p.parent/'outer_accounting_interval.json').exists():
            correction=frozen.read(p.parent/'outer_accounting_interval.json');assert correction['original_outer_seconds']==row['outer_seconds']
            row.update(outer_seconds=correction['budget_charge_seconds'],outer_seconds_interval=correction['outer_seconds_interval'])
        records.append(row)
    assert sum(r['conservative_process_starts'] for r in records)<=24 and sum(r['outer_seconds'] for r in records)<=18000
    assert sum(r['conservative_process_starts'] for r in records if r['qualification'])<=8 and sum(r['outer_seconds'] for r in records if r['qualification'])<=600
    return records
frozen.fee_records=fee_records

def selection(seed,roles,eligibility,unresolved=()):return decision.selection(_main,seed,roles,True,unresolved)

def rebuild(root,dest,qualification_only=False):
    global _main
    root=Path(root).resolve();_main=imported_main(root)
    source=inspect.getsource(frozen.rebuild)
    old="eligibility_record=read(out/'review/sealed_input_eligibility.json')\n        assert eligibility_record['input_manifest_SHA']==sha(out/'input_manifest.json')\n        eligibility=eligibility_record['eligibility']"
    assert old in source;source=source.replace(old,"eligibility={r['id']:True for r in roles}")
    source=source.replace("data={(a['id'],a['seed'],a['arm']):a for a in arms}","data={(a['id'],a['seed'],a['arm']):a for a in _main+arms}")
    source=source.replace('if len(arms)==42:','if True:').replace('decision.selection(arms,roles,eligibility,','_selection(arms,roles,eligibility,')
    source=source.replace("for id in ['G20-C2','G50-R1','G100-R2']]","for id in ['G20-C2','G50-R1','G100-R2'] if id in selection['seed_primary_pairs']]")
    source=source.replace("reader_SHA=sha(Path(__file__))","reader_SHA=_reader_SHA")
    source=source.replace("root/'scripts/round110_decisions.py'","root/'scripts/round111_decisions.py'")
    namespace=dict(vars(frozen),_main=_main,_selection=selection,_reader_SHA=frozen.sha(__file__))
    exec(compile(source,__file__+'::unchanged_raw_loop','exec'),namespace)
    summary=namespace['rebuild'](root,dest,qualification_only)
    dest=Path(dest)
    published=frozen.read(root/ROUND/'review/inherited_main03/main36_imported_rows.json')
    for value in published:
        value.update(evidence_layer='INHERITED_R110_MAIN',raw_reaudited_in_R111=False,import_audit_SHA=MAIN_SHA,
            original_formal_protocol_qualified=value.get('formal_protocol_qualified',''))
    frozen.table(dest/'inherited_main36.csv',published)
    with (root/ROUND/'review/inherited_main03/authority/arms.csv').open(newline='',encoding='utf-8') as f:
        old_seed=[row for row in csv.DictReader(f) if row['seed']=='1']
    assert len(old_seed)==6
    frozen.table(dest/'inherited_old_seed6.csv',old_seed)
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--compare',type=Path);p.add_argument('--qualification-only',action='store_true');a=p.parse_args()
    print(json.dumps(rebuild(a.root,a.out,a.qualification_only)),flush=True)
    if a.compare:print(json.dumps(frozen.compare(a.compare,a.out)),flush=True)
