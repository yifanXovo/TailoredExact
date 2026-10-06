from round105_common import *
if __name__ == '__main__':
    label=sys.argv[1]
    if not (BUILD/'CMakeCache.txt').exists():
        receipt(label+'_configure',[CMAKE,'-S',ROOT,'-B',BUILD,'-G','Ninja',
            '-DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe','-DCMAKE_MAKE_PROGRAM='+str(NINJA),
            '-DEXACT_EBRP_ENABLE_GUROBI=ON','-DGUROBI_ROOT=D:/gurobi1302/win64','-DCMAKE_BUILD_TYPE='],600,True)
    receipt(label,[CMAKE,'--build',BUILD,'--target',*(sys.argv[2:] or ['ExactEBRP','Round105Tests','Round105Oracle','Round65ReferenceBuild']),'--parallel','4'],900,True)
