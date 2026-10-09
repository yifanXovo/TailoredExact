"""Verify the actual draft/base/head and exact public bytes at a pinned commit."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import time
from urllib.parse import quote
from urllib.request import Request, urlopen

REPO = 'yifanXovo/TailoredExact'
BASE_NAME = 'codex/round108-frozen-mb-validation'
BASE_SHA = 'd11c94d81e6a2c5dcd64dad8c54b390f3cb4a027'
HEAD_NAME = 'codex/round109-frozen-mb-geographic-evaluation'


def command(root, argv):
    return subprocess.check_output(argv, cwd=root, text=True).strip()


def state(root, pr, head):
    value = json.loads(command(root, ['gh', 'pr', 'view', str(pr), '--repo', REPO,
                       '--json', 'url,state,isDraft,headRefName,headRefOid,baseRefName']))
    assert value['state'] == 'OPEN' and value['isDraft']
    assert value['headRefName'] == HEAD_NAME and value['headRefOid'] == head
    assert value['baseRefName'] == BASE_NAME
    remote = command(root, ['git', 'ls-remote', 'origin', 'refs/heads/'+BASE_NAME,
                           'refs/heads/'+HEAD_NAME]).splitlines()
    refs = {line.split()[1]: line.split()[0] for line in remote}
    assert refs['refs/heads/'+BASE_NAME] == BASE_SHA
    assert refs['refs/heads/'+HEAD_NAME] == head
    return dict(PR=value, remote_refs=refs)


def fetch(item, head):
    url = 'https://raw.githubusercontent.com/'+REPO+'/'+head+'/'+quote(item['path'], safe='/')
    digest = hashlib.sha256()
    size = 0
    tick = time.perf_counter()
    request = Request(url, headers={'Accept-Encoding': 'identity', 'User-Agent': 'Round109-exact-byte-review'})
    with urlopen(request, timeout=180) as response:
        assert response.status == 200
        while block := response.read(1024 * 1024):
            digest.update(block)
            size += len(block)
    actual = digest.hexdigest()
    assert size == item['bytes'] and actual == item['SHA'], item['path']
    return dict(path=item['path'], URL=url, bytes=size, SHA=actual,
                seconds=time.perf_counter()-tick, passed=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--head', required=True)
    parser.add_argument('--pr', type=int, required=True)
    parser.add_argument('--bindings', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    assert len(args.head) == 40 and command(root, ['git', 'rev-parse', 'HEAD']) == args.head
    output = Path(args.out)
    assert not output.exists()
    records = json.loads(Path(args.bindings).read_text(encoding='utf-8'))['files']
    initial = state(root, args.pr, args.head)
    tick = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as pool:
        actual = list(pool.map(lambda item: fetch(item, args.head), records))
    final = state(root, args.pr, args.head)
    assert final == initial
    value = dict(passed=True, pinned_delivery_commit=args.head, base_SHA=BASE_SHA,
                 actual_state_before=initial, actual_state_after=final,
                 actual_remote_files=actual, bytes=sum(item['bytes'] for item in actual),
                 seconds=time.perf_counter()-tick, production_PE_is_separate=True,
                 result_commit_does_not_contain_its_own_verification=True,
                 engineering=True, Optimize=0, IIS=0)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8', newline='\n') as file:
        json.dump(value, file, indent=2, allow_nan=False)
        file.write('\n')
    print(json.dumps(dict(passed=True, head=args.head, files=len(actual),
                         bytes=value['bytes'], seconds=value['seconds']), allow_nan=False))


if __name__ == '__main__':
    main()
