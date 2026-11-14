"""Expand/run the explicitly named default-off C166 research candidate.

The mature pure GI-TBC launch planner is reused with a separate frozen config.
Stable B/ENS defaults and their launcher/config files are unchanged.
"""
from pathlib import Path
import paper_s2
paper_s2.CONFIG=Path(__file__).resolve().parents[1]/'config/gi_tbc_c166_round166.json'
paper_s2.__doc__=__doc__
if __name__=='__main__':raise SystemExit(paper_s2.main())
