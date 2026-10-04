"""Exclusive zero-Optimize correctness qualification, never a performance arm."""
import sys,subprocess
from round101_common import *
from round100_idle import ensure_idle
import round86_native_evidence as nej

def run(label):
    ensure_idle()
    dest=OUT/'builds'/label;dest.mkdir(exist_ok=False)
    build=ROOT/'build/research'/('round101-'+label)
    assert not build.exists()
    measured=read(OUT/'builds/final_numeric_guards/manifest.json')
    assert sha(BUILD/'ExactEBRP.exe')==measured['binary_sha256']['ExactEBRP.exe']
    assert sha(OUT/'builds/final_numeric_guards/ExactEBRP.exe')==measured['binary_sha256']['ExactEBRP.exe']
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    source=bindings()
    changed={k:dict(measured=v,current=source[k]) for k,v in measured['source_hashes'].items() if source[k]!=v}
    assert set(changed)=={'CMakeLists.txt','src/GurobiBaseline.cpp'}
    write(dest/'prebuild.json',dict(source_delivery_head=revision,source_hashes=source,
        changed_vs_measured=changed,test_sha256=sha(ROOT/'tests/round101_failure_tests.cpp'),
        measured_source=measured['source_delivery_head'],measured_binary_sha256=measured['binary_sha256'],
        mode='separate correctness-only build; frozen measured directory is untouched',maximum_optimizer_calls=0))
    receipt(label+'_configure',[CMAKE,'-S',ROOT,'-B',build,'-G','Ninja',
        '-DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe','-DCMAKE_MAKE_PROGRAM='+str(NINJA),
        '-DEXACT_EBRP_ENABLE_GUROBI=ON','-DGUROBI_ROOT=D:/gurobi1302/win64','-DCMAKE_BUILD_TYPE='])
    receipt(label+'_build',[CMAKE,'--build',build,'--target','ExactEBRP','Round101FailureTests',
        'Round101FleetTests','NativeEvidenceJournalTests','--parallel','4'],cap=600)
    artifacts=dest/'fault_artifacts'
    receipt(label+'_faults',[build/'Round101FailureTests.exe',artifacts],cap=60)
    receipt(label+'_fleet',[build/'Round101FleetTests.exe'],cap=60)
    receipt(label+'_journal',[build/'NativeEvidenceJournalTests.exe'],cap=60)
    replay=[]
    for name in ['status','cut','certificate','unknown','summary']:
        directory=artifacts/name
        records=[nej.receipt(directory/f'event_{i}.commit',1,2) for i in range(1,5)]
        identity=records[0]['payload']
        panel=dict(input_sha256=identity['input_sha256'],lambda_=identity['lambda'],
            T_seconds=identity['T'],pickup_seconds=identity['pickup_seconds'],drop_seconds=identity['drop_seconds'])
        panel['lambda']=panel.pop('lambda_')
        before=nej.audit(ROOT,panel,records[:3],'synthetic-no-engine')
        assert before['LB']==.1 and before['certificate'] is False
        try:nej.audit(ROOT,panel,records,'synthetic-no-engine')
        except AssertionError as e:
            assert e.args[0][0]=='journal_failure'
            replay.append(dict(case=name,rejected='journal_failure',
                prior_prefix_LB=before['LB'],failure=records[-1]['payload']['reason']))
        else:raise AssertionError('R86 reader accepted a fatal fleet stream')
        assert not (directory/'event_5.commit').exists()
    assert bindings()==source
    assert sha(BUILD/'ExactEBRP.exe')==measured['binary_sha256']['ExactEBRP.exe']
    for k,v in read(OUT/'baseline.json')['user_edit_sha256'].items():assert sha(ROOT/k)==v
    write(dest/'manifest.json',dict(source_delivery_head=revision,source_hashes=source,
        test_sha256=sha(ROOT/'tests/round101_failure_tests.cpp'),
        binary_sha256={p.name:sha(p) for p in [build/n for n in
            ['ExactEBRP.exe','Round101FailureTests.exe','Round101FleetTests.exe','NativeEvidenceJournalTests.exe']]},
        dll_sha256=measured['dll_sha256'],native_version=measured['native_version'],
        maximum_optimizer_calls=0,reader_rejections=replay,passed=True,
        build_directory=str(build),measured_build_untouched=True,
        limitation='Synthetic callback-control fault fixtures; no Gurobi DLL/Optimize, no new performance qualification. Previously available prefixes cannot anticipate a future failure.'))
    print('post-review guard qualification passed; zero Optimize calls',flush=True)

if __name__=='__main__':run(sys.argv[1])
