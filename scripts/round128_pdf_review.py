"""Reuse the established Poppler review and identify the changed reading pages."""
from round128_common import *
import argparse,re
import round127_pdf_review as inherited
from round127_release import idle

inherited.OUT=OUT
inherited.TEMP=TEMP

def inspect(attempt):
    idle();inherited.inspect(attempt)
    target=TEMP/'pdf_review'/attempt
    pages=(target/'pages.txt').read_text(encoding='utf-8').split('\f')
    patterns=['Round128 separately','6.8 Inclusive-root','Table R128.1','Table R128.2',
        'Round128 clarification','B.12 Separately','bounded stage decision',
        'That remains the historical','maintained mathematical appendices']
    hits={p:[n for n,page in enumerate(pages,1) if p in page] for p in patterns}
    write(target/'changed_page_map.json',dict(PDF_SHA256=sha(OUT/'manuscript.pdf'),hits=hits,
        scope='Changed passages and adjacent layout require actual image inspection; extraction alone is not a visual pass.'))
    print(json.dumps(hits))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['inspect','render'])
    parser.add_argument('--attempt',required=True);parser.add_argument('--pages');args=parser.parse_args()
    if args.mode=='inspect':inspect(args.attempt)
    else:idle();inherited.render(args.attempt,args.pages)
