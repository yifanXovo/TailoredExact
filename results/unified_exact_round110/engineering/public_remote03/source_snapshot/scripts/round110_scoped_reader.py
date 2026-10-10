"""Current primary reader entry after the actual scoped25 fault.

Reuse the byte-frozen rebuild loop and extend only signed scoped evidence.
"""
import round110_reader as frozen
import round110_scoped_evidence as current

frozen.numerical=current

if __name__=='__main__':
    import argparse
    from pathlib import Path
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--qualification-only',action='store_true');ap.add_argument('--compare',type=Path)
    args=ap.parse_args();summary=frozen.rebuild(args.root,args.out,args.qualification_only)
    summary.update(primary_reader_entry_SHA=frozen.sha(Path(__file__)),scoped_evidence_module_SHA=frozen.sha(args.root/'scripts/round110_scoped_evidence.py'))
    frozen.write(args.out/'summary.json',summary)
    print(frozen.json.dumps(summary,allow_nan=False))
    if args.compare:print(frozen.json.dumps(frozen.compare(args.compare,args.out),allow_nan=False))
