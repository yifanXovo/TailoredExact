"""Finite registered four-start inner diagnostic sequence; no retry."""
from round99_common import *
if __name__=='__main__':
    path=OUT/'inner_protocol01.json';q=read(path);assert len(q['arms'])==4
    python=ROOT/'build/research/round88-ot/venv/Scripts/python.exe'
    for a in q['arms']:
        label=f'inner_{a["number"]:02d}_{a["role"]["id"]}_{a["arm"]}'
        receipt(label,[python,ROOT/'scripts/round99_inner.py',path,a['number'],label],kind='diagnostic_receipts',cap=a['cap_seconds'],optimizer_calls=1)
        assert read(OUT/'diagnostics'/label/'summary.json')['passed']
