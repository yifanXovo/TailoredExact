"""Mechanical scoped reuse of the established producer and three clocks."""
from round130_common import *

def run():
    source=(ROOT/'scripts/round129_campaign.py').read_text()
    source=source.replace('from round129_common import *','from round130_common import *')
    source=source.replace('from round128_evidence import verify,extension','from round130_evidence import verify,extension')
    source=source.replace("[BUILD/'Round128ExportE2.exe'","[EXPORTER")
    source=source.replace("pe=E1 if layer=='E1' else E2","pe=E3")
    source=source.replace("arm='P-GRB' if method in ['P','PT'] else 'M-B'","arm='P-GRB' if method=='P' else 'P-S' if method=='PS' else 'M-B'")
    source=source.replace("cmd=original_command(p,arm,d);cmd[0]=str(pe)","cmd=original_command(p,'P-GRB' if method=='PS' else arm,d);cmd[0]=str(pe)")
    source=source.replace("if method=='P':","if method in ['P','PS']:")
    begin=source.index("        if layer in ['E1','E2']:")
    end=source.index('        launches.append(',begin)
    source=source[:begin]+'''        if method=='PS':cmd+=['--round112-ens-start-compact']
        else:cmd+=['--round127-mode',dict(P='p',S2='ms2',S2R='s2-root')[method]]
'''+source[end:]
    source=source.replace('Round129 active.','Round130 active.')
    (ROOT/'scripts/round130_campaign.py').write_text(source,encoding='utf-8')
    (OUT/'.gitignore').write_text('/fees/\n/campaign/\n/qualification/\n/recovery/\n/*.log\n',encoding='utf-8')
    print('R130 producer adapter written; no child launched')
if __name__=='__main__':run()
