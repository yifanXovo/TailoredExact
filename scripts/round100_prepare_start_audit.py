"""Construct a finite zero-Optimize native reader from the audited R99 reader."""
from round100_common import *
if __name__=='__main__':
    text=(ROOT/'scripts/round99_start_audit.py').read_text()
    text=text.replace('import gurobipy as gp','from round100_gurobi_runtime import gp,binding')
    text=text.replace('round99_common','round100_common')
    text=text.replace("mode in ['off','m-binary-linked']","mode in ['off','m-binary-linked','ens-q']")
    text=text.replace("['projected','m-binary','m-binary-linked']","['projected','m-binary','m-binary-linked','ens-q']")
    text=text.replace("env.setParam('OutputFlag',0);env.start()","env.setParam('OutputFlag',0);env.start();assert binding()['sha256']==sha('D:/gurobi1302/win64/bin/gurobi130.dll')")
    with (ROOT/'scripts/round100_start_audit.py').open('x',encoding='utf-8') as f:f.write(text)
