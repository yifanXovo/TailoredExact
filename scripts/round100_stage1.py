"""Exactly four finite paid qualification batches, no implicit retries."""
from round100_common import *
from round100_idle import ensure_idle
if __name__=='__main__':
    ensure_idle()
    receipt('micro_export01',[BUILD/'Round100QuantityTests.exe',OUT/'micro_models01'],kind='qualification',cap=60)
    receipt('model_exports01',['D:/msys64/ucrt64/bin/python.exe',ROOT/'scripts/round100_qualification.py','exports'],kind='qualification',cap=180)
    py=ROOT/'build/research/round88-ot/venv/Scripts/python.exe'
    receipt('micro01',[py,ROOT/'scripts/round100_qualification.py','micro','micro01'],kind='qualification',cap=300,optimizer_calls=3)
    receipt('matrix01',[py,ROOT/'scripts/round100_qualification.py','matrix','matrix01'],kind='qualification',cap=300,optimizer_calls=3)
