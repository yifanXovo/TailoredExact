"""Resume the same failed public root; change only the semantic I/O launcher."""
import argparse, hashlib, json, pathlib, sys
ROOT=pathlib.Path('E:/codes/ExactEBRP-work/restore/round137-public-e735c3447eb1')
COMMIT='e735c3447eb1443713c700942d873de1783a4a26'
EXPECTED_DRIVER='3548368389eabd608f56c5c36a2a64b77b070c470a93018bde89a1412d0bf805'

parser=argparse.ArgumentParser()
parser.add_argument('--commit',required=True)
parser.add_argument('--destination',type=pathlib.Path,required=True)
parser.add_argument('--receipt',type=pathlib.Path,required=True)
parser.add_argument('--resume',action='store_true')
args=parser.parse_args()
assert args.commit==COMMIT and args.destination.resolve()==ROOT.resolve() and args.resume
state=json.loads((ROOT/'restore_state.json').read_text(encoding='utf-8'))
assert state['state']=='FAILED_PRESERVE' and state['commit']==COMMIT
published=ROOT/'scripts/round137_public_restore.py';raw=published.read_bytes()
assert hashlib.sha256(raw).hexdigest()==EXPECTED_DRIVER
before="command=[sys.executable,str(self.dest/'scripts/round137_portable_check.py'),'--root',str(self.dest),'--receipt',str(semantic)]"
after="command=[sys.executable,str(_ROUND137_METADATA_IO_ADAPTER),'--root',str(self.dest),'--receipt',str(semantic)]"
text=raw.decode('utf-8');assert text.count(before)==1
adapter=pathlib.Path(__file__).with_name('round137_public_semantic_io.py').resolve(strict=True)
namespace=dict(__name__='__main__',__file__=str(published),
    _ROUND137_METADATA_IO_ADAPTER=adapter)
# All fetch/expand/member hashes, ownership, same-commit FAILED-only resume,
# cumulative9000s and min(4500,remaining) semantic limits remain byte-for-byte.
exec(compile(text.replace(before,after),str(published)+'::metadata_io_launch','exec'),namespace)
