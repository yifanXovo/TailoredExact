"""Compare inherited and candidate public type layouts, without native work."""
from round133_common import *
import shutil

def main():
    destination=BUILD/f'abi_attempt_{len(list(BUILD.glob("abi_attempt_*")))+1:02d}'
    destination.mkdir(parents=True,exist_ok=False)
    previous=destination/'previous';previous.mkdir()
    headers=['NativeEvidenceJournal.hpp','FixedIntervalMipBackend.hpp','ControllingLeafScheduler.hpp']
    for name in headers:(previous/name).write_bytes(git('show',BASE+':include/'+name))
    source=destination/'layout.cpp'
    source.write_text('''#include "FixedIntervalMipBackend.hpp"
#include <iostream>
int main(){ebrp::FixedIntervalMipRequest q;
std::cout << "{\\\"scope\\\":" << sizeof(ebrp::NativeEvidenceScope)
 << ",\\\"request\\\":" << sizeof(q) << ",\\\"outcome\\\":" << sizeof(ebrp::FixedIntervalMipOutcome)
 << ",\\\"native_scope_offset\\\":" << (reinterpret_cast<char*>(&q.native_evidence_scope)-reinterpret_cast<char*>(&q))
 << ",\\\"gamma_L_offset\\\":" << (reinterpret_cast<char*>(&q.gamma_L)-reinterpret_cast<char*>(&q)) << "}\\n";}
''',encoding='utf-8')
    layouts={}
    for name,first in [('previous',previous),('candidate',ROOT/'include')]:
        executable=destination/(name+'.exe')
        command=[COMPILER,'-std=c++17','-I'+str(first),'-I'+str(ROOT/'include'),source,'-o',executable]
        process=subprocess.run(list(map(str,command)),capture_output=True,timeout=60,env=environment())
        (destination/(name+'.compile.log')).write_bytes(process.stdout+process.stderr)
        assert process.returncode==0
        process=subprocess.run([str(executable)],capture_output=True,timeout=30)
        assert process.returncode==0;layouts[name]=json.loads(process.stdout)
    assert layouts['previous']==layouts['candidate'],layouts
    current=OUT/'qualification/ABI.json'
    if current.exists():
        history=OUT/'qualification/ABI_history'/f'{sha(current)}.json'
        history.parent.mkdir(parents=True,exist_ok=True)
        if not history.exists():history.write_bytes(current.read_bytes())
        assert sha(history)==sha(current)
    write(current,dict(UTC=utc(),PASS=True,baseline=BASE,layouts=layouts,
        previous_headers={name:sha(previous/name) for name in headers},
        candidate_headers={name:sha(ROOT/'include'/name) for name in headers},
        NativeEvidenceJournal_allocations='Only rebuilt GurobiBaseline and PaperExternalGiniTree TUs',
        native_Optimize=0,compiler_SHA=sha(COMPILER)))
    print(json.dumps(layouts))

if __name__=='__main__':main()
