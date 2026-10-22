"""Same compiler/flags, unchanged ABI, selective frozen archive linking.

Only replaced complete translation units precede the original archive. No old
object or production PE is edited. The source closure is recorded explicitly.
"""
from round130_common import *

CHANGED=['CplexBaseline','IntervalRowFactory','PaperExternalGiniTree','GurobiBaseline']
FLAGS=['-std=c++17','-Wall','-Wextra','-Wpedantic','-DEXACT_EBRP_ENABLE_GUROBI=1',
    '-I'+str(ROOT/'include'),'-ID:/gurobi1302/win64/include']
def call(label,args):
    rc=metered(label,'build',args)
    if rc:raise SystemExit(rc)
def build():
    init=read(OUT/'initialization.json')
    assert sha(COMPILER)==init['compiler_SHA'] and sha(ARCHIVE)==init['frozen_core_archive_SHA']
    BUILD.mkdir(parents=True,exist_ok=True)
    for stem in CHANGED+['main']:
        p=ROOT/'src'/(stem+'.cpp');obj=BUILD/(stem+'.o')
        signature=dict(source=sha(p),headers={q.relative_to(ROOT).as_posix():sha(q) for q in (ROOT/'include').rglob('*') if q.is_file()},flags=FLAGS,compiler=sha(COMPILER))
        receipt=BUILD/(stem+'_binding.json')
        if obj.exists() and receipt.exists() and read(receipt)==signature:continue
        attempt=len(list((OUT/'fees').glob('build_'+stem+'_*')))+1
        call(f'build_{stem}_{attempt:02d}',[COMPILER,*FLAGS,'-c',p,'-o',obj])
        write(receipt,signature)
    args=[COMPILER,BUILD/'main.o',*[BUILD/(s+'.o') for s in CHANGED],ARCHIVE,
        '-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32','-loleaut32','-luuid','-lcomdlg32','-ladvapi32','-o',E3]
    attempt=len(list((OUT/'fees').glob('build_link_*')))+1
    call(f'build_link_{attempt:02d}',args)
    write(OUT/'E3_build.json',dict(UTC=utc(),PE=str(E3),PE_SHA=sha(E3),DLL_SHA=sha(DLL),compiler_SHA=sha(COMPILER),
        source_bindings=source_bindings(),original_archive_SHA=sha(ARCHIVE),original_archive_source=SOURCE,
        replaced_complete_translation_units=CHANGED+['main'],SolveOptions_and_SolveResult_ABI_unchanged=True,
        inherited_flags=FLAGS,link_command=list(map(str,args)),final_qualification_pending=True))
    print(json.dumps(dict(PE_SHA=sha(E3),budget=budget())))
if __name__=='__main__':build()
