"""Preserve qualified working bytes in Git; never rewrite a working source.

Run once only while the experiment/archival compute slot is free. Reject any
non-newline difference before staging tracked frozen files. The three unrelated
historical dirty files are outside this explicit path list.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name("frozen_git_byte_preservation.json")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def blobs(paths):
    process = subprocess.Popen(["git", "cat-file", "--batch"], cwd=ROOT,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    payload, _ = process.communicate(b"".join((":" + p + "\n").encode() for p in paths))
    assert process.returncode == 0
    result = {}
    offset = 0
    for path in paths:
        end = payload.index(b"\n", offset)
        header = payload[offset:end].split()
        assert len(header) == 3 and header[1] == b"blob", (path, header)
        size = int(header[2])
        offset = end + 1
        result[path] = payload[offset:offset + size]
        offset += size
        assert payload[offset:offset + 1] == b"\n"
        offset += 1
    assert offset == len(payload)
    return result


def main():
    started = time.perf_counter()
    assert not OUT.exists(), "Do not overwrite a completed repair receipt"
    assert not git("diff", "--cached", "--name-only").strip(), "Index must start empty"
    manifest = json.loads((ROOT / "results/unified_exact_round91/qualification_001/source_manifest_audit.json").read_text())
    source_paths = [row["path"] for row in manifest]
    assert len(source_paths) == 165 and len(set(source_paths)) == 165
    frozen = {row["path"]: row["expected"] for row in manifest}
    paths = git("ls-files", "-z", "--", *source_paths,
                "results/unified_exact_round88", "results/unified_exact_round89",
                "results/unified_exact_round90", "scripts/round88*.py",
                "scripts/round89*.py", "scripts/round90*.py", "scripts/round91*.py",
                "research_plans/ensc_optimization_plan_2026-09-26.md",
                "research_plans/ensc_optimization_instances_2026-09-26.json")
    paths = sorted(set(p.decode() for p in paths.split(b"\0") if p))
    assert set(source_paths).issubset(paths)
    previous = blobs(paths)
    working = {}
    changed = []
    for path in paths:
        file = ROOT / path
        assert file.is_file() and not file.is_symlink()
        data = file.read_bytes()
        working[path] = data
        if path in frozen:
            assert digest(data) == frozen[path], ("frozen source drift", path)
        assert data.replace(b"\r\n", b"\n") == previous[path].replace(b"\r\n", b"\n"), ("non-newline tracked change", path)
        if data != previous[path]:
            changed.append(dict(path=path, previous_git_sha256=digest(previous[path]),
                                qualified_working_sha256=digest(data), size_bytes=len(data)))
    # Restrict mutation to the Git index; working bytes remain untouched.
    for first in range(0, len(paths), 80):
        git("add", "--renormalize", "--", *paths[first:first + 80])
    git("add", "--", ".gitattributes")
    current = blobs(paths)
    for path in paths:
        assert current[path] == working[path] == (ROOT / path).read_bytes(), path
    subprocess.run(["git", "diff", "--cached", "--ignore-space-at-eol", "--exit-code",
                    "--", *source_paths], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    receipt = dict(scope="qualified source165, tracked R88-R90 evidence and pinned research scripts/plans",
                   files_checked=len(paths), frozen_sources=165,
                   working_files_rewritten=0, non_newline_changes=0,
                   staged_bytes_match_working=True,
                   git_blob_bytes_corrected=len(changed), corrections=changed,
                   wall_seconds=time.perf_counter() - started,
                   note="Archives and semantic content preserved. Historical commits remain unchanged; this commit stores the measured working bytes for future checkouts.")
    OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in receipt.items() if k != "corrections"}))


if __name__ == "__main__":
    main()
