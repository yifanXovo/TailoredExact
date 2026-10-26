"""Package compact five-pair evidence after all optimizers have stopped.

The independently checked formal journals remain in the original raw tree;
their 10 observation files and every non-journal raw artifact are packaged.
The excluded, partially started run 11 is packaged separately by path.
"""
import json
import os
from pathlib import Path
import tarfile

import round87_analyze as base


ROOT, STAGE, OUT = base.ROOT, base.STAGE, base.OUT


def files_without_formal_journals(root):
    for directory, children, names in os.walk(root):
        children[:] = sorted(child for child in children if child != "journal")
        for name in sorted(names):
            path = Path(directory) / name
            if path.is_file():
                yield path


def main():
    assert not (STAGE / "package_index.json").exists()
    closure = base.read(OUT / "partial_completion.json")
    analysis = base.read(OUT / "analysis.json")
    validation = base.read(STAGE / "independent_validation.json")
    summary = base.read(OUT / "summary.json")
    identity = base.read(OUT / "identity.json")
    assert closure["all_formal_runs_valid"] and closure["completed_formal_runs"] == 10
    assert analysis["completed_pairs"] == validation["completed_pairs"] == 5
    assert validation["all_formal_runs_replayed"] and validation["optimizer_calls"] == 0
    assert summary["completed"] == 10 and len(summary["records"]) == 10
    raw = Path(identity["runtime_root"])
    archive = raw / "packages" / "round87_five_pairs_compact.tar.gz"
    assert not archive.exists(), "Do not overwrite a previous evidence package"
    files = []
    for path in sorted(STAGE.rglob("*")):
        if path.is_file():
            files.append((path, "results/unified_exact_round87/" + path.relative_to(STAGE).as_posix()))
    for name in ("round87_research.py", "round87_analyze.py", "round87_resume.py",
                 "round87_analyze_partial.py", "round87_package_partial.py", "round86_native_evidence.py"):
        path = ROOT / "scripts" / name
        files.append((path, "scripts/" + name))
    raw_campaign = raw / "campaign"
    for path in sorted(raw_campaign.iterdir()):
        if path.is_file():
            files.append((path, "raw/campaign/" + path.name))
    recovery = raw_campaign / "quota_interruption_recovery"
    for path in sorted(recovery.rglob("*")):
        if path.is_file():
            files.append((path, "raw/campaign/quota_interruption_recovery/" + path.relative_to(recovery).as_posix()))
    for launch in identity["launches"][:10]:
        directory = Path(launch["destination"])
        assert directory.is_dir()
        for path in files_without_formal_journals(directory):
            files.append((path, "raw/local_raw/" + directory.name + "/" + path.relative_to(directory).as_posix()))
        count = summary["records"][launch["number"] - 1]["observed_commits"]
        assert (directory / "journal" / "event_1.commit").is_file()
        assert (directory / "journal" / f"event_{count}.commit").is_file()
    excluded = Path(identity["launches"][10]["destination"])
    assert excluded.is_dir() and not (excluded / "completion.json").exists()
    for path in sorted(excluded.rglob("*")):
        if path.is_file():
            files.append((path, "raw/excluded_run11/" + path.relative_to(excluded).as_posix()))
    arcnames = [name for _, name in files]
    assert len(arcnames) == len(set(arcnames))
    archive.parent.mkdir(parents=True, exist_ok=True)
    manifest_files = []
    with tarfile.open(archive, "w:gz", compresslevel=6) as stream:
        for number, (path, arcname) in enumerate(files, 1):
            assert path.is_file()
            info = stream.gettarinfo(str(path), arcname=arcname)
            assert info.isfile()
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mtime = 0
            with path.open("rb") as source:
                stream.addfile(info, source)
            manifest_files.append(dict(path=str(path), archive_path=arcname,
                                       bytes=path.stat().st_size, sha256=base.sha(path)))
            if number % 100 == 0:
                print(json.dumps(dict(packaged_files=number)), flush=True)
    index = dict(schema="round87-five-pair-package-index-v1", archive_path=str(archive),
                 archive_bytes=archive.stat().st_size, archive_sha256=base.sha(archive),
                 archive_file_count=len(files), manifest_files=manifest_files,
                 formal_journals_in_archive=False,
                 formal_journal_policy="Retained at raw runtime root; all first-ten formal receipts independently rechecked against observations.json",
                 formal_journals=[dict(number=row["number"], id=row["id"], arm=row["arm"],
                                       path=str(Path(row["destination"]) / "journal"),
                                       verified_commits=row["observed_commits"])
                                  for row in summary["records"]],
                 excluded_run11_journal_in_archive=True,
                 original_protocol_planned_runs=18, user_closed_formal_runs=10)
    base.write(STAGE / "package_index.json", index)
    print(json.dumps(dict(archive=str(archive), bytes=index["archive_bytes"],
                          sha256=index["archive_sha256"], files=len(files))), flush=True)


if __name__ == "__main__":
    main()
