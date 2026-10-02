import sys
import round100_idle as old
from round100_common import *
if __name__=='__main__':
    old.ensure_idle();label=sys.argv[1]
    if not (BUILD/'CMakeCache.txt').exists():
        receipt(label+'_configure',[CMAKE,'-S',ROOT,'-B',BUILD,'-G','Ninja',
            '-DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe','-DCMAKE_MAKE_PROGRAM='+str(NINJA),
            '-DEXACT_EBRP_ENABLE_GUROBI=ON','-DGUROBI_ROOT=D:/gurobi1302/win64','-DCMAKE_BUILD_TYPE='])
    receipt(label,[CMAKE,'--build',BUILD,'--target',*(sys.argv[2:] or
        ['ExactEBRP','Round100QuantityTests','Round100ModelExport','Round65ReferenceBuild']),
        '--parallel','4'])
