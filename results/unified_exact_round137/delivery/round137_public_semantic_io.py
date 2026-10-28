"""I/O-only admission adapter for the exact downloaded Round137 checker.

No qualification, physical, numerical, derived-output or clock predicate is
changed. Only the declared-tree inventory uses cached Windows directory-entry
metadata rather than reopening every existing path for its realpath.
"""
import argparse, ast, hashlib, importlib, json, os, pathlib, stat, sys, time

ROUND='results/unified_exact_round137'
EXPECTED_MANIFEST='fba957ec57d42e1cfbb31704e016d9b3887ca9a2b9c231715a4a1618c7e7c99b'
EXPECTED_CHECKER='aeaa89cb335072468da5f2f81b2e7c9111b8162d023fa2a9ee5ee5fdff6853ab'
FORBIDDEN={'.exe','.dll','.o','.obj','.a','.lib'}
ADMISSION_RECORDS=[]

def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def fast_allow_tree(self,value):
    """Same complete file/dir inventory, with every reparse entry rejected."""
    path=self.resolve(value)
    assert path.is_dir(),('declared current evidence tree missing',str(path))
    self.allowed_trees.add(str(path));self.allowed_dirs.add(str(path))
    stack=[path];complete_parent_chains={str(self.root)}
    files=directories=0;started=time.perf_counter()
    while stack:
        directory=stack.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                assert entry.name not in {'.','..'} and os.path.basename(entry.name)==entry.name
                child=directory/entry.name
                assert child.parent==directory
                metadata=entry.stat(follow_symlinks=False)
                assert not (getattr(metadata,'st_file_attributes',0)&0x400),('linked declared evidence',str(child))
                assert not stat.S_ISLNK(metadata.st_mode),('linked declared evidence',str(child))
                if stat.S_ISREG(metadata.st_mode):
                    assert child.suffix.lower() not in FORBIDDEN
                    self.allowed_files.add(str(child));files+=1
                    parent=child.parent
                    # A completed chain cache preserves the exact ancestor set.
                    while parent==self.root or self.root in parent.parents:
                        key=str(parent);self.allowed_dirs.add(key)
                        if key in complete_parent_chains:break
                        complete_parent_chains.add(key);parent=parent.parent
                elif stat.S_ISDIR(metadata.st_mode):
                    self.allowed_dirs.add(str(child));stack.append(child);directories+=1
    self.metadata_admission_transport=dict(
        files=files,directories=directories,seconds=time.perf_counter()-started,
        full_tree_inventory=True,reparse_entries_rejected=True,
        file_suffix_blacklist_unchanged=True,real_reads_hashes_scopes_and_write_guards_unchanged=True)
    ADMISSION_RECORDS.append(dict(path=str(path),**self.metadata_admission_transport))

def minimal_fs(engine,root,recorded):
    fs=object.__new__(engine.ClosedRoot)
    fs.root=root;fs.recorded=pathlib.PureWindowsPath(recorded)
    fs.allowed_files=set();fs.allowed_trees=set();fs.allowed_dirs={str(root)}
    return fs

def run(root,receipt,fixture_only=False):
    root=root.resolve(strict=True)
    manifest_path=root/ROUND/'export_manifest.json'
    assert sha(manifest_path)==EXPECTED_MANIFEST
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    checker_path=root/'scripts/round137_portable_check.py'
    engine_path=root/'scripts/round133_portable_check.py'
    assert sha(checker_path)==EXPECTED_CHECKER==manifest['files']['scripts/round137_portable_check.py']['SHA256']
    assert sha(engine_path)==manifest['files']['scripts/round133_portable_check.py']['SHA256']
    sys.path.insert(0,str(root/'scripts'))
    checker=importlib.import_module('round137_portable_check')
    assert pathlib.Path(checker.__file__).resolve()==checker_path.resolve()
    engine=checker.engine
    assert pathlib.Path(engine.__file__).resolve()==engine_path.resolve()
    # Small actual restored fixture: exact full allow-lists, not a timing-only test.
    fixture=root/ROUND/'campaign/004'
    old=minimal_fs(engine,root,checker.RECORDED);new=minimal_fs(engine,root,checker.RECORDED)
    engine.ClosedRoot.allow_tree(old,fixture);fast_allow_tree(new,fixture)
    assert old.allowed_files==new.allowed_files and old.allowed_dirs==new.allowed_dirs
    assert old.allowed_trees==new.allowed_trees
    fixture_result=dict(files=len(old.allowed_files),directories=len(old.allowed_dirs),
        exact_allowed_files_dirs_trees_equal=True,original_and_fast_both_read_only=True)
    if fixture_only:
        receipt.parent.mkdir(parents=True,exist_ok=True)
        receipt.write_text(json.dumps(fixture_result,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(fixture_result));return
    # This class is used only by this process's exact downloaded checker.
    checker.CurrentRoot.allow_tree=fast_allow_tree
    result=checker.check(root,local=False)
    assert result['passed'] and result['formal_positions']==120
    result['metadata_IO_adapter']=dict(adapter_SHA=sha(__file__),
        original_checker_SHA=EXPECTED_CHECKER,manifest_SHA=EXPECTED_MANIFEST,
        fixture=fixture_result,admission_records=ADMISSION_RECORDS,
        change='Only complete declared-tree admission uses cached DirEntry metadata; every actual reader, file byte/hash, allowed scope, derived-write and semantic comparison predicate stays unchanged',
        native_execution_added=0)
    receipt.parent.mkdir(parents=True,exist_ok=True)
    receipt.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,positions=120,seconds=result['seconds'],Optimize=0,metadata_IO_adapter=True)))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=pathlib.Path,required=True)
    parser.add_argument('--receipt',type=pathlib.Path,required=True)
    parser.add_argument('--fixture-only',action='store_true')
    args=parser.parse_args();run(args.root,args.receipt,args.fixture_only)
