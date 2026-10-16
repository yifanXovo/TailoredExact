"""Tiny in-memory recovery checks; never exports a scientific carrier."""
import io,json,pathlib,sys,tarfile,time
ROOT=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from round122_release import Joined,normalize,typed_equal
from round122_common import write,sha

tick=time.perf_counter();buffer=io.BytesIO()
with tarfile.open(fileobj=buffer,mode='w') as archive:
    for name,data in [('a',b'abc'),('b',b'defgh')]:
        member=tarfile.TarInfo(name);member.size=len(data)
        archive.addfile(member,io.BytesIO(data))
buffer.seek(0)
with tarfile.open(fileobj=buffer) as archive:
    stream=Joined(archive,['a','b'])
    assert stream.read(2)==b'ab'
    assert stream.read(3)==b'cde'
    assert stream.read(99)==b'fgh'
    assert stream.read(1)==b''
assert normalize('E:/rootx/a',['E:/root'])=='E:/rootx/a'
assert normalize('E:/root/a',['E:/root'])=='<ROOT>/a'
typed_equal({'x':[1,-0.0,True]},{'x':[1,-0.0,True]})
rejected=0
for left,right in [(1,True),(0.,-0.),({'x':1},{'x':1.}),([1],[1,2])]:
    try:typed_equal(left,right)
    except AssertionError:rejected+=1
    else:raise AssertionError('typed mismatch accepted')
assert rejected==4
receipt=dict(passed=True,checks=['streamed part boundary','complete root path component','JSON type','array length','signed zero'],
    fixture_only=True,scientific_carrier_exports=0,scientific_restores=0,native_starts=0,Optimize=0,
    code_SHA=sha(__file__),release_SHA=sha(ROOT/'scripts/round122_release.py'),engineering_seconds=time.perf_counter()-tick)
write(pathlib.Path(__file__).with_suffix('.json'),receipt)
print(json.dumps(receipt))
