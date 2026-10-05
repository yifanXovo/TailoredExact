from round103_common import *
if __name__=='__main__':
    for label,role,kind in [('C2_native02','R98-C2','native'),('F5_native01','F5','native'),('F2_native01','F2','native'),('N2_native01','R99-N2','native')]:
        receipt('point_'+label,[PYTHON,'scripts/round103_points.py',label,role,kind,'600'],650)
