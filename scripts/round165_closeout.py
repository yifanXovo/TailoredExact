"""Document acceptance, protected-file checks and new-only public byte recovery."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, os, shutil, subprocess, sys, time, urllib.request
import round165_documents as doc

ROOT=doc.ROOT;OUT=doc.OUT;PAPER=doc.PAPER;TEMP=doc.TEMP
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return doc.sha(p)
def read(p):return doc.read(p)
def write(p,v):return doc.write(p,v)
def git(*args,cwd=ROOT):return subprocess.check_output(['git',*args],cwd=cwd).decode('utf-8',errors='replace').strip()

def protection():
    entries=read(OUT/'entry_state.json')['protected'];results=[]
    for e in entries:
        current=git('status','--porcelain=v1','-uno',cwd=e['root'])
        head=git('rev-parse','HEAD',cwd=e['root'])
        files=[dict(path=r['path'],expected=r['SHA256'],actual=sha(Path(e['root'])/r['path'])) for r in e['dirty_tracked']]
        results.append(dict(root=e['root'],same_HEAD=head==e['HEAD'],same_tracked_status=current==e['status'],dirty_hashes_unchanged=all(f['actual']==f['expected'] for f in files),files=files))
    tables=read(OUT/'main_table_reconciliation.json')['tables']
    csvs=[dict(path=t['path'],unchanged=sha(t['path'])==t['SHA256']) for t in tables]
    result=dict(UTC=utc(),passed=all(r['same_HEAD'] and r['same_tracked_status'] and r['dirty_hashes_unchanged'] for r in results) and all(r['unchanged'] for r in csvs),trees=results,CSV=csvs)
    write(OUT/'protection_final.json',result);assert result['passed']
    return result

def accept():
    import pdfplumber,PIL
    # This explicit acceptance records the actual root image inspection of
    # these exact snapshots. It must not certify unseen future exports.
    inspected={'manuscript.pdf':'3b24cdd828e666cb491dcb7a421889fdc4623eb05a2fe6b7a9087d290957dc71',
               'supplement.pdf':'5bebe69ae5d7b090ebe4dc0de8114e276ad5d1a9a1e72c234575cfde89cebbeb'}
    assert all(sha(PAPER/n)==expected for n,expected in inspected.items()),'A changed PDF needs a new actual visual review.'
    previous=read(OUT/'document_qa.json')
    write(OUT/'review/full_overview_qa.json',previous)
    checks=doc.source_checks();assert not checks['errors'],checks['errors']
    build=read(OUT/'document_build.json');manifest=read(OUT/'source_manifest.json')
    assert all(sha(ROOT/r['path'])==r['SHA256'] for r in manifest['components'])
    records=[]
    closeups=Path('E:/codes/ExactEBRP-work/temp/round165/pdf/final-closeups')
    for stem in ['manuscript','supplement']:
        pdf=PAPER/(stem+'.pdf');pages=[]
        with pdfplumber.open(pdf) as document:
            for i,p in enumerate(document.pages,1):
                text=p.extract_text() or ''
                outside=[c for c in p.chars if c['x0']<-.5 or c['x1']>p.width+.5 or c['top']<-.5 or c['bottom']>p.height+.5]
                assert not outside,(stem,i,'outside text')
                assert len(p.chars)>20,(stem,i,'blank page')
                assert '\ufffd' not in text and '[@' not in text,(stem,i,'unresolved text')
                pages.append(dict(page=i,characters=len(p.chars),width=p.width,height=p.height,opening=text[:120]))
        assert len(pages)==(52 if stem=='manuscript' else 39)
        old=next(r for r in previous['documents'] if r['path'].endswith(stem+'.pdf'))
        records.append(dict(path=pdf.relative_to(ROOT).as_posix(),SHA256=sha(pdf),bytes=pdf.stat().st_size,
            page_count=len(pages),pages=pages,blank_pages=[],outside_page_characters=0,replacement_characters=0,
            actual_visual_inspection_complete=True,
            overview=dict(PDF_SHA256=old['SHA256'],page_count=old['page_count'],contact_sheets=old['contact_sheets'],inspected_by='root actual image reads'),
            final_targeted_pages=[3,5,7,10,16,17,18,31,38,40,51,52] if stem=='manuscript' else [16,38,39],
            final_targeted_scope='Actual main closeups and figure; latest supplement availability-page render and complete text/bounds scan. Unchanged historical material covered by earlier full overview.',
            closeup_root=str(closeups)))
    qa=dict(UTC=utc(),status='PASS',documents=records,source_checks=checks,
        evidence_checks_SHA256=sha(OUT/'evidence_checks.json'),new_Optimize=0,
        visual_acceptance_not_inferred_from_file_existence=True,
        tools=dict(pdfplumber=pdfplumber.__version__,Pillow=PIL.__version__,Poppler=doc.run([doc.POPPLER/'pdftoppm.exe','-v']).strip()),
        actual_visual_inspection=dict(reviewer='/root',scope='Two full contact-sheet overviews for changed layouts, then 110dpi main closeups and targeted supplementary corrections; no repeated render of unchanged main PDF',
            findings_fixed=['old remote image path','TOC/abstract boundary','Table1 row split','B20 numerical-noise axis','orphan landscape headings/rows','final appendix spill','supplementary explanatory/availability blocks']),
        warnings_disposition='No missing character, unresolved citation or main formula overflow. Supplement Pandoc alignment warnings are <=0.174pt with all ink inside the page and no observed table clipping; hyperref duplicate colorlinks warning is harmless.')
    write(OUT/'document_qa.json',qa)
    build.update(visual_QA_pending=False,visual_QA_status='PASS',visual_QA_receipt='results/unified_exact_round165/document_qa.json')
    write(OUT/'document_build.json',build)
    export=read(PAPER/'pdf_export.json');export.update(visual_review_pending=False,visual_QA_status='PASS',visual_receipt='../unified_exact_round165/document_qa.json',page_counts=[52,39])
    write(PAPER/'pdf_export.json',export)
    write(OUT/'source_checks.json',checks)
    report_files=['math_implementation.md','data_reproducibility.md','research_manuscript.md']
    assert all('closure' in (OUT/'review'/n).read_text(encoding='utf-8').lower() for n in report_files)
    write(OUT/'review/identities.json',dict(UTC=utc(),kind='three actually spawned independent agents',human_review=False,licensed_replication=False,
        agents=[dict(returned_canonical_task='/root/'+task,tool='collaboration.spawn_agent',report='review/'+name,post_correction='PASS',SHA256=sha(OUT/'review'/name)) for task,name in zip(['math_review','data_review','contribution_review'],report_files)],
        parallel_time_accounting='included once in the shared parent work window; agent durations not added'))
    body=(PAPER/'paper_body.md').read_text(encoding='utf-8-sig');app=(PAPER/'model_and_algorithm_appendices.md').read_text(encoding='utf-8-sig');bib=(PAPER/'references.bib').read_text(encoding='utf-8-sig')
    integration=dict(UTC=utc(),status='PASS',unique_independent_findings_closed=6,
        corrections=dict(A10_explicit='inventory balance (A10)' in app,pre_repair_identified='historical pre-repair writer' in app,Seed0_map='6 inputs / 18 B, E+, P' in body,Koppe_numbering='Definition 3 and Structure Theorem 5' in bib,actual_XeTeX_version='MiKTeX-XeTeX' in build['versions']['xelatex'],B20_axis='ax.set_ylim(max(0,centre-.02),centre+.02)' in (ROOT/'scripts/round165_audit.py').read_text(encoding='utf-8')),
        unchanged_results=True,no_solver_or_production_build=True,remaining_conclusion_changing_document_defects=[],
        scientific_limits=['outer independent speed benefit unestablished','cross-module general performance consequence unestablished','all cohort n35 OPEN','C35 absolute primal deficit','Eplus has one-Seed limited proof evidence','full 2026 neighbour formulations unavailable'])
    assert all(integration['corrections'].values());write(OUT/'review/integration_review.json',integration)
    protection()
    elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat('2026-11-12T20:05:40+00:00')).total_seconds()
    write(OUT/'cost_report.json',dict(UTC=utc(),work_start_UTC='2026-11-12T20:05:40+00:00',science_document_end_UTC=utc(),
        conservative_shared_work_window_seconds=elapsed,capacity_seconds=21600,within_capacity=elapsed<21600,
        accounting='shared outer reading/writing/offline/build/QA/review window, counted once; no sum of parallel agent durations. Preliminary task-file read preceded the measured goal window and was not precision-metered. Ordinary publication/transfer I/O is recorded separately.',
        target_hours='2–4 target, 6 maximum; finish when complete, no waiting to exhaust it',
        new_Optimize=0,new_formal_arms=0,production_compile=0,new_seed=0,monetary_cost='not exposed by tools',
        failures_retained=['initial missing matplotlib import resolved with existing local R137 dependency directory','source-check generated-link/heading matcher repaired before assembly','first supplement export old remote image path repaired','bounded old R62 path assumption corrected from fixed source map','local command quoting/encoding typos repaired; no healthy solver rerun'],
        ordinary_Git_transfer_IO='entry/ref checks in tool transcript; timed publication commands/public_restore below; not historical C++ timing'))
    decision=dict(UTC=utc(),round=165,document_science_complete=True,main_method='B',Eplus='separately named limited proof extension, off in B',
        supported_claim='finite integrated-method certificate/endpoint advantage over specified compact controls',
        independent_outer_speed_gain_established=False,internal_substantive_review_ready=True,
        OR_gap='distinct incremental outer-versus-strengthened-root value and generalizable stock/service linkage effect remain unestablished',
        next_action='review current manuscript first',single_conditional_future_question='architecture choice: full GI-TBC versus the already defined strengthened root-only continuation under a uniform fixed contract',
        next_project_started=False,new_Optimize=0,new_performance_rows=0,CSV_106_found=False,available_working_CSV_rows=103,
        CSV_three_old_rows_unreconstructed=True,independent_agent_reviews=3,all_fixable_review_findings_closed=True,
        current_PDF_pages=[52,39],publication='normal Draft delivery pending',released_defaults_changed=False)
    write(OUT/'decision.json',decision)
    (OUT/'final_report.md').write_text('''# Current manuscript completed through R164

The maintained R137 component directory now contains one current English
paper, complete Appendix A/B, mathematical companion, bibliography, figures,
assembled manuscript and current reading PDFs: **52 pages main/appendices**
and **39 pages supplement**. The old R137 generator is guarded against
overwriting current prose. The component-only builder also retains TeX exports.

The contribution is an integrated exact method for the inherited physical
equity-routing model, together with a clear distinction between inventory
representation, valid proof information, physical realization and paid complete
performance. The single-product rectangle projection, conditional service
integrality, true-G embedding, inclusive cutoff complements and full coverage
are retained. Custom rows are static; Gurobi runs native branch-and-cut.

B remains main. Direct finite evidence is breadth9/12 versus P7/12 and PS7/12,
resource4/8 versus0/8 and0/8, and B3/6 versusP1/6 at each of three Seeds on
six later inputs. Those 18 B/P pairs/36 method observations include 24 added
in R164 and are not 18 independent inputs. E+ retains one X35 final-proof
gain at six equal physical U, no added certificate and only one substantive
paired time increase. Full-over-root gains are unestablished; row-deletion
directions reverse, all cohort n35 remain OPEN, C35's historical P fleet still
beats every B incumbent and added X35 runs miss the fixed absolute target.

The current paper is suitable for substantive internal review. The most
specific OR-level gap is the independent value of the outer controller over
the same strengthened root, and a generalizable explanation of the stock/service
connection's net consequences. Review this manuscript first. The sole conditional
future candidate is that architecture choice; no new project or experiment starts.

Targeted primary-source checks distinguish established Gupte/Köppe objects
from these service connections. Köppe's new arXiv read uses Definition3 and
StructureTheorem5. The 2026 neighbours' accessible primary abstracts support
only the stated equity/operation differences. Caggiani's openly listed VoR
failed web size and one normal direct HTTP403 request; no full-text claim,
paywall diagnosis or configuration workaround is made. The actual available
May HGA-TGBC draft was rechecked and retains model/decoder attribution.

Three actual independent agents reviewed mathematics/implementation, data/
reproducibility and research/manuscript. Six distinct fixable findings were
closed and read back. The independent data audit passed233 checks; later
closure checked only affected artifacts. Actual rendered overviews and
targeted final pages pass QA, with zero blank pages, out-of-page text or
replacement glyphs. Subpoint supplementary table-alignment warnings are
recorded and visually harmless. Source and PDF hashes are in the build/QA receipts.

The actual bounded CSV search found two91-row GB18030 user files and the
unchanged103-row/28-column R164 working copy (all12 increments already present).
The exact106-row attachment was unavailable; three old N/A-P original rows
cannot be fully reconstructed without their original descriptive/source fields.
No new instance/Seed performance data need appending. No user master was modified.

New Optimize/formal arms/production compilation/default changes: **0**.
The shared actual work window and failures are in cost_report.json; parallel
review is counted once, with ordinary publication/transfer I/O separate.
The dirty R155 paper-current entry, original repository and R164 tree are
protected. All new work is inside ExactEBRP-work; there is no old-round cleanup.

Normal commit/push, English Open Draft PR, new/changed-only public recovery
and zero-delete cleanup are recorded by publication.json,
public_restore_receipt.json and cleanup_record.json after their actual completion.

Read [contribution map](contribution_positioning.md), [author memo](author_decision_memo.md),
[current main PDF](../unified_exact_round137/manuscript.pdf),
[supplement PDF](../unified_exact_round137/supplement.pdf),
[build](document_build.json), [QA](document_qa.json),
[CSV reconciliation](main_table_reconciliation.md) and [review closure](review/integration_review.json).
''',encoding='utf-8')
    print(json.dumps(dict(status='DOCUMENT_SCIENCE_COMPLETE',PDF_pages=[52,39],shared_seconds=elapsed,Optimize=0)))

def public_restore():
    tick=time.perf_counter();commit=git('rev-parse','HEAD')
    names=git('diff','--name-only',doc.BASE,commit).splitlines()
    assert len(names)<100
    allowed=lambda p:p.startswith(('results/unified_exact_round137/','results/unified_exact_round165/','scripts/round165','docs/')) or p in ['README.md','.gitattributes','scripts/round137_documents.py','scripts/round137_pdf_qa.py']
    assert all(allowed(p) for p in names),names
    folder=Path('E:/codes/ExactEBRP-work/restore/round165')/commit
    folder.mkdir(parents=True,exist_ok=False)
    def fetch(path):
        expected=subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
        url='https://raw.githubusercontent.com/yifanXovo/TailoredExact/'+commit+'/'+path
        with urllib.request.urlopen(url,timeout=40) as response: data=response.read()
        destination=folder/path;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
        assert data==expected,path
        return dict(path=path,bytes=len(data),SHA256=hashlib.sha256(data).hexdigest(),URL=url,match=True)
    with ThreadPoolExecutor(max_workers=6) as pool: results=list(pool.map(fetch,names))
    result=dict(UTC=utc(),PASS=True,commit=commit,files=len(results),bytes=sum(r['bytes'] for r in results),members=results,
        scope='only new/changed current-round normal Git paper/document/delivery files; no old raw archives',
        destination=str(folder),seconds=time.perf_counter()-tick,ordinary_transfer_IO=True,anonymous=True,normal_TLS=True,new_Optimize=0)
    write(OUT/'public_restore_receipt.json',result);print(json.dumps({k:result[k] for k in ['PASS','commit','files','bytes','seconds']}))

def cleanup():
    before=shutil.disk_usage('E:/').free
    protected=protection();root=Path('E:/codes/ExactEBRP-work/temp/round165')
    files=[p for p in root.rglob('*') if p.is_file()]
    after=shutil.disk_usage('E:/').free
    write(OUT/'cleanup_record.json',dict(UTC=utc(),current_round_only=True,files_deleted=0,bytes_deleted=0,
        actual_free_before=before,actual_free_after=after,observed_free_delta=after-before,
        retained_temp_files=len(files),retained_temp_bytes=sum(p.stat().st_size for p in files),
        retained_reason='active current worktree, unique edit/build failure logs, inspected page renders and bounded source reads retained; no deletion necessary',
        public_recovery_passed=read(OUT/'public_restore_receipt.json')['PASS'],protected_checks_passed=protected['passed'],
        excluded_from_publication=['commercial executable/DLL/license/credentials','private author draft','foreign full text','old raw archives'],
        no_recursive_delete_or_move=True))
    print('Zero-delete cleanup and protected-tree readback PASS.')

if __name__=='__main__':globals()[sys.argv[1]]()
