"""Explicit post-seal metadata adapter revision; no native rerun or byte mutation."""
from round134_common import *
import shutil
def main():
    path=OUT/'execution_binding.json'
    original=OUT/'execution_binding_original.json'
    if not original.exists():shutil.copyfile(path,original)
    previous=read(path);current=dict(previous)
    current['helper_SHA']=dict(previous['helper_SHA'])
    for name in current['helper_SHA']:current['helper_SHA'][name]=sha(ROOT/name)
    amendments=OUT/'repair';amendments.mkdir(exist_ok=True)
    number=len(list(amendments.glob('reader_amendment_*.json')))+1
    record=amendments/f'reader_amendment_{number:02}.json'
    write(record,dict(UTC=utc(),before=previous,after=current,
        reason=sys.argv[1],native_Optimize=0,producer_and_plan_bytes_unchanged=True,
        no_solver_retry_no_certificate_backdating=True))
    write(path,current)
    print(record)
if __name__=='__main__':main()
