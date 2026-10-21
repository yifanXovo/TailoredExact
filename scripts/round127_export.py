"""Reuse the inherited document exporter with Round127 destinations and date."""
from pathlib import Path
import inspect,os
import round126_export as inherited

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round127'
namespace=dict(vars(inherited),OUT=OUT,TEMP_PARENT=Path(os.environ.get('ROUND127_PDF_TEMP','E:/codes/ExactEBRP-work/temp/round127/pdf')))
source=inspect.getsource(inherited.export).replace('date=19 October 2026','date=21 October 2026').replace('ROUND126_PDF_','ROUND127_PDF_')
exec(compile(source,__file__+'::inherited_document_export','exec'),namespace)
if __name__=='__main__':namespace['export']()
