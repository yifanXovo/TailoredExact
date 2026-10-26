"""Declared consecutive campaign subset; no repeat or implicit extra launch."""
import sys
import round100_campaign as campaign
if __name__=='__main__':
    name=sys.argv[1];numbers=list(map(int,sys.argv[2:]))
    assert numbers and numbers==list(range(numbers[0],numbers[-1]+1))
    for number in numbers:campaign.run(name,number)
