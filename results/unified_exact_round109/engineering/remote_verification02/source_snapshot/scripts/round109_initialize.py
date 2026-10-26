"""Record actual starting state and materialize the exact public source blob."""
from round109_common import *
import hashlib, shutil

def main():
    OUT.mkdir(exist_ok=True)
    d=OUT/'engineering/initialization01';d.mkdir(parents=True,exist_ok=False)
    source=ROOT/'results/data_generation_citibike_round57/source_station_table.csv'
    checkout=source.read_bytes();(d/'source_station_table_checkout.csv').write_bytes(checkout)
    blob=subprocess.check_output(['git','rev-parse',BASE+':'+source.relative_to(ROOT).as_posix()],cwd=ROOT,text=True).strip()
    assert blob=='84fb8af5aaa9836d316820227e4f06e8cd4b1e63'
    exact=subprocess.check_output(['git','cat-file','blob',blob],cwd=ROOT)
    digest=hashlib.sha256(exact).hexdigest()
    assert len(exact)==69678 and digest=='9f9aad24e61d661971c24c6f5ec78a69081edf01ffc433563e52a70b2eaca2d0'
    source.write_bytes(exact)
    shutil.copyfile('C:/Users/Administrator/.codex/attachments/83131214-bc6e-4e56-b36c-0d1d15219033/已粘贴的文本.txt',OUT/'goal.md')
    user_paths=['results/gf_compact_bc_round/handling_convention_test/handling_convention.json',
        'results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv',
        'results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json']
    original=Path('E:/codes/ExactEBRP')
    baseline=dict(base_head=BASE,current_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        current_branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
        original_root=str(original),user_file_SHA={p:sha(original/p) for p in user_paths},
        latest_PR170=json.loads(subprocess.check_output(['gh','pr','view','170','--json','url,headRefName,headRefOid,baseRefName,state,isDraft'],cwd=ROOT,text=True)),
        managed_checkout_failed=dict(operation_id='a175a670-a7d7-4303-a756-7f2afeefb423',reason='C device no space during full checkout; tool cleaned failed checkout',
            exact_failed_shell_command_unknown=True,solver_starts=0),
        sparse_checkout=str(ROOT),AGENTS_found=False,active_solver_processes_before_start=0,
        source_materialization=dict(commit=BASE,blob=blob,bytes=len(exact),SHA=digest,checkout_bytes=len(checkout),
            checkout_SHA=hashlib.sha256(checkout).hexdigest(),reason='Git autocrlf materialization restored to exact public blob before any draw'),
        current_PE_SHA=sha(BUILD/'ExactEBRP.exe'),DLL_SHA=sha(DLL),production_identity=check_identity(),
        original_network_proxy_permission_configuration_changed=False)
    write(OUT/'baseline.json',baseline)
    write(d/'receipt.json',dict(passed=True,zero_Optimize=True,solver_starts=0,source_blob=blob,source_SHA=digest))
    print('initial identity and exact public table verified; zero Optimize')

if __name__=='__main__':main()
