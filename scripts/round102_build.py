from round102_common import *
from round100_idle import ensure_idle
import sys
if __name__=='__main__':
    ensure_idle();label=sys.argv[1]
    if not (BUILD/'CMakeCache.txt').exists():
        receipt(label+'_configure',[CMAKE,'-S',ROOT,'-B',BUILD,'-G','Ninja','-DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe','-DCMAKE_MAKE_PROGRAM='+str(NINJA),'-DEXACT_EBRP_ENABLE_GUROBI=ON','-DGUROBI_ROOT=D:/gurobi1302/win64','-DCMAKE_BUILD_TYPE='],600,0,True)
    receipt(label,[CMAKE,'--build',BUILD,'--target',*(sys.argv[2:] or ['ExactEBRP','Round102ServiceTests','Round102ServiceDiagnostic','Round101FailureTests','Round65ReferenceBuild']),'--parallel','4'],600,0,True)
