"""Real CLI dry plans and frozen same-new-PE controls; no Native load."""
import ast
import paper_s2 as base
from round149_common import *


def main():
    configure();profile=read(ROOT/'config/gi_tbc_penalty_feedback_round149.json')
    matrix=read(OUT/'k35_matrix.json');facts=[]
    for mode in ['off','on']:
        output=TEMP/('entry_unused_'+mode)
        command=[PYTHON,'-B',ROOT/'scripts/paper_s2_penalty_feedback.py','--input',
            ROOT/'results/unified_exact_round132/inputs/K-35-U.txt','--out-dir',output,
            '--T','10800','--lambda','.15','--cap','2400','--seed','0','--json','--pf',mode]
        result=subprocess.run(list(map(str,command)),cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
        assert result.returncode==0,result.stderr
        launch=json.loads(result.stdout);assert launch['dry_run'] and not output.exists()
        assert launch['GD'] and not launch['STOCK'] and not launch['Shared_S'] and launch['PF']==(mode=='on')
        assert launch['matches_verified_PE'] and launch['matches_verified_DLL']
        expected=matrix['groups'][mode=='on']['launch']['command']
        assert base.normalize(launch['command'],profile)==base.normalize(expected,profile)
        facts.append(dict(PF=mode,actual_CLI=True,normalized_frozen_command_equal=True,
            PE_SHA=launch['executable_SHA256'],output_not_created=True))
    syntax=[]
    for path in [*sorted((ROOT/'scripts').glob('round149*.py')),ROOT/'scripts/paper_s2_penalty_feedback.py']:
        ast.parse(path.read_text(encoding='utf-8'),filename=str(path));syntax.append(path.name)
    write(OUT/'qualification_entry.json',dict(PASS=True,Optimize=0,Native_load=0,compile=0,
        facts=facts,syntax_checked=syntax,old_profiles_unmodified=True,
        profile_SHA=sha(ROOT/'config/gi_tbc_penalty_feedback_round149.json'),entry_SHA=sha(ROOT/'scripts/paper_s2_penalty_feedback.py')))
    print('PASS actual PF on/off dry CLI, PE/DLL, frozen normalized commands and syntax')


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='run':
        assert metered('qualification_entry','diagnostic',[PYTHON,'-B',__file__],60,90)==0
    else:main()
