"""Finite serial campaign lease; unchanged per-arm supervisor and reader."""
from round105_common import *
import round105_campaign as campaign

if __name__=='__main__':
    name=sys.argv[1];first=int(sys.argv[2]);last=int(sys.argv[3]);label=sys.argv[4]
    q=read(OUT/name/'identity.json');assert 1<=first<=last<=len(q['launches'])
    assert last-first+1<=8
    dest=OUT/name/label;dest.mkdir(exist_ok=False)
    frozen=sha(__file__)
    write(dest/'launch.json',dict(first=first,last=last,declared_native_children=last-first+1,
        identity_sha256=sha(OUT/name/'identity.json'),batch_runner_sha256=frozen,
        scope='finite serial original per-arm process launches; no nested time double charge'))
    for number in range(first,last+1):
        assert sha(__file__)==frozen
        write(dest/f'{number:02d}_before.json',dict(number=number,arm=q['launches'][number-1]['arm']))
        campaign.run(name,number)
        write(dest/f'{number:02d}_after.json',dict(number=number,completed_and_audited=True))
    write(dest/'completion.json',dict(completed=True,native_children=last-first+1))
