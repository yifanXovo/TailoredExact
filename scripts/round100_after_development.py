"""Finite nine-scope real Start qualification and read-only extraction."""
from round100_common import *
from round100_idle import ensure_idle
if __name__=='__main__':
    ensure_idle()
    receipt('dev_actual_start01',[ROOT/'build/research/round88-ot/venv/Scripts/python.exe',ROOT/'scripts/round100_start_batch.py'],
        kind='qualification',cap=300,optimizer_calls=0)
    receipt('development_extract01',['D:/msys64/ucrt64/bin/python.exe',ROOT/'scripts/round100_results.py','development_results01','development01'],
        kind='engineering',cap=300,optimizer_calls=0)
