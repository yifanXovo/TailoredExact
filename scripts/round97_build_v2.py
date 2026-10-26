"""Build the separate R97 v2 tree only while no solver/build is active."""
import sys
from round97_build import ROOT, CMAKE, NINJA, run
import round96_external as ext

BUILD=ROOT/'build/research/round97-native-closure-v2'

if __name__=='__main__':
    ext.ensure_idle()
    label=sys.argv[1]
    if not (BUILD/'CMakeCache.txt').exists():
        run(label+'_configure',[CMAKE,'-S',ROOT,'-B',BUILD,'-G','Ninja',
            '-DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe',
            '-DCMAKE_MAKE_PROGRAM='+str(NINJA),'-DEXACT_EBRP_ENABLE_GUROBI=ON',
            '-DGUROBI_ROOT=D:/gurobi1302/win64','-DCMAKE_BUILD_TYPE='])
    run(label,[CMAKE,'--build',BUILD,'--target',*(sys.argv[2:] or
        ['ExactEBRP','Round95FullBlockTests','Round96RouteOrderTests','Round97NativeClosureTests',
         'Round96RouteOrderDiagnostic']),'--parallel','4'])
