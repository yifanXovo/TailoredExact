"""Preperformance bookkeeping and zero-Optimize qualification exports."""
from round127_common import *
from round127_data import TRAIN,positivity,source
from round127_build import FLAGS,CHANGED
import copy

def recover_generation():
    # Tiny files were fully produced once. The first invocation stopped only
    # at a CRLF-altered inherited reference hash, after both draws completed.
    # Recover existing files; no call to the generator or selection routine.
    recipe=read(OUT/'tiny_recipe.json');roles=[];restored=[]
    for name in ['PB-B20-S','PB-B35-B']:
        p='reference/round122_paper_benchmark/'+name+'.txt';before=sha(ROOT/p)
        blob=git('show',BASE+':'+p);(ROOT/p).write_bytes(blob)
        restored.append(dict(path=p,checkout_SHA_before=before,restored_blob_SHA=sha(ROOT/p),source_commit=BASE))
    for p0 in recipe['roles']:
        p=copy.deepcopy(p0);path=OUT/'inputs'/(p['id']+'.txt')
        parsed=read(OUT/'inputs'/(p['id']+'_parsed.json'))
        assert parsed==json.loads(json.dumps(source.old.parse_instance_mirror(path)))
        selection=read(OUT/'inputs'/(p['id']+'_selection.json'))
        assert selection['selection_id']==p['selection_id'] and selection['dataset_family']==recipe['families'][p['source']]
        p.update(input_path=path.relative_to(ROOT).as_posix(),instance_path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),
            source_identity_SHA=source.SOURCES[p['source']]['identity_SHA'],shortage_arithmetic=positivity(parsed,p))
        roles.append(p)
    manifest=read(OUT/'experiment_manifest.json')
    for p in manifest['E0_main']+[q['role'] for q in manifest['E1_core']]+TRAIN:
        assert sha(ROOT/p['input_path'])==p['input_sha256'],p
        parsed=source.old.parse_instance_mirror(ROOT/p['input_path'])
        assert (parsed['V'],parsed['M'],parsed['Q'])==(p['V'],p['M'],p['Q_vector'])
    write(OUT/'input_manifest.json',dict(tiny_roles=roles,main_roles=manifest['E0_main'],training_roles=TRAIN,
        core_roles=[q['role'] for q in manifest['E1_core']],recipe_commit='ea5491743',generated_once=True,Optimize=0))
    write(OUT/'generation_receipt.json',dict(UTC=utc(),recipe_commit='ea5491743',input_SHA={p['id']:p['input_sha256'] for p in roles},
        original_attempt='fees/tiny_generate',generation_completed_before_reference_hash_failure=True,read_only_recovery_of_tiny=True,
        redraws=0,Optimize=0,inherited_checkout_repairs=restored))
    print('Recovered both once-generated tiny inputs; original benchmark blob hashes restored')

def build_exporters():
    for layer in ['E0','E1']:
        exe=BUILD/('Round127Export'+layer+'.exe')
        args=[COMPILER,*FLAGS,ROOT/'scripts/round127_export.cpp']
        if layer=='E1':args += [BUILD/(s+'.o') for s in CHANGED]
        args += [ARCHIVE,'-o',exe]
        attempt=len(list((OUT/'fees').glob('exporter_'+layer+'*')))+1
        rc=metered('exporter_'+layer+f'_{attempt:02d}','build',args)
        if rc:raise SystemExit(rc)
    write(OUT/'exporter_identity.json',{layer:dict(path=str(BUILD/('Round127Export'+layer+'.exe')),SHA=sha(BUILD/('Round127Export'+layer+'.exe'))) for layer in ['E0','E1']})
if __name__=='__main__':{'recover-generation':recover_generation,'build-exporters':build_exporters}[sys.argv[1]]()
