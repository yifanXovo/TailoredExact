"""Small exact inventory-unit and rejected-input checks; no Native or Optimize."""
from round146_math import compiled
from round146_common import *
def main():
    configure();tick=time.perf_counter();root=OUT/'qualification/units';root.mkdir(parents=True,exist_ok=True)
    a=dict(supports={1:[0,2,5],2:[1,4],3:[0,3]},c_binary64={1:.1,2:1/3,3:1.7},Bminus=3,B=7)
    b=dict(supports={i:[8*y for y in ys] for i,ys in a['supports'].items()},c_binary64={i:c/8 for i,c in a['c_binary64'].items()},Bminus=24,B=56)
    first=compiled(a,root/'original.json');scaled=compiled(b,root/'scaled.json')
    assert first['lower']==scaled['lower'] and first['upper']==scaled['upper']
    for x,y in zip(first['states'],scaled['states']):
        assert x['i']==y['i'] and x['y']*8==y['y']
        for k in ['feasible','lower','upper','low','high']:assert x[k]==y[k],(x,y,k)
    for x,y in zip(first['rows'],scaled['rows']):
        normalized={('G' if k=='G' else '_'.join(k.split('_')[:2])+'_'+str(int(k.split('_')[2])//8)):v for k,v in y['terms'].items()}
        assert normalized==x['terms']
    driver=read(OUT/'rows_driver.json');negative=root/'negative_ratio.txt';negative.write_text('2 1 2 1\n-0.25 2 0 1\n1 2 0 1\n',encoding='utf-8')
    result=subprocess.run([driver['PE'],str(negative)],cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
    assert result.returncode==1 and 'nonnegative_actual_ratio' in result.stderr
    write(OUT/'qualification_units.json',dict(PASS=True,Optimize=0,Native_load=0,seconds=time.perf_counter()-tick,
        exact_power_of_two_inventory_unit_invariance=True,support_stock_and_ratio_units_changed_consistently=True,
        rejected_negative_ratio=dict(exit_code=result.returncode,stderr=result.stderr),row_header_SHA=driver['header_SHA']))
    print('PASS exact inventory-unit invariance and negative-ratio rejection')
if __name__=='__main__':main()
