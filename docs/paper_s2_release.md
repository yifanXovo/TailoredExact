# R172 document rebuild and historical GI-TBC run guide

- **Current scientific manuscript, R172.** Read the released PDFs or follow the author reading guide. The [R172 document script](../scripts/round172_documents.py) assembles the maintained [main text](../results/unified_exact_round137/paper_body.md) and [appendices](../results/unified_exact_round137/model_and_algorithm_appendices.md). It exports the [assembled manuscript](../results/unified_exact_round137/manuscript.md) and the maintained [supplement](../results/unified_exact_round137/supplement.md). [Main PDF](../results/unified_exact_round137/manuscript.pdf) · [Supplement PDF](../results/unified_exact_round137/supplement.pdf) · [Author reading guide](paper_review.md)
- **Historical R137 solver launch.** The [`paper_s2.py` launcher](../scripts/paper_s2.py) reads the [R137 frozen profile](../config/gi_tbc_round137.json). Its default source, executable, command vector, clocks, affinity and qualification belong to R137. Use R172 [Table 1 in §4.1](../results/unified_exact_round137/paper_body.md#41-comparators-and-panel-protocols) and the individual panel records for later observations.

## Rebuild R172 in a new checkout

The released PDFs are ready to read. For an optional local rebuild, pin the published R172 content commit, [`b770e94be267f27aabfee81bcdd6e7e142034aa3`](https://github.com/yifanXovo/TailoredExact/tree/b770e94be267f27aabfee81bcdd6e7e142034aa3). The local example uses a shared Git store that already has this commit and a fresh dedicated root under `E:\codes\ExactEBRP-work\rebuilds`. Set the Git store path to your copy of the repository.

```powershell
$gitStore = 'E:\codes\ExactEBRP\.git'
$r172 = 'b770e94be267f27aabfee81bcdd6e7e142034aa3'
$runId = [guid]::NewGuid().ToString('N')
$rebuildRoot = Join-Path 'E:\codes\ExactEBRP-work\rebuilds' "r172-$runId"
$checkout = Join-Path $rebuildRoot 'worktrees\paper'
if (Test-Path -LiteralPath $rebuildRoot) { throw 'Choose an unused rebuild root.' }

git --git-dir=$gitStore worktree add --detach --no-checkout $checkout $r172
if ($LASTEXITCODE -ne 0) { throw 'Could not create the R172 worktree.' }
@(
    '/.gitattributes'
    '/scripts/'
    '/results/unified_exact_round137/*.*'
    '/results/unified_exact_round137/figures/'
    '/results/unified_exact_round135/figures/count_bound_scope.png'
    '/results/unified_exact_round171/comparison_BP.csv'
    '/results/unified_exact_round172/'
) | git -C $checkout sparse-checkout set --no-cone --stdin
if ($LASTEXITCODE -ne 0) { throw 'Could not set the document checkout paths.' }
git -C $checkout read-tree -mu HEAD
if ($LASTEXITCODE -ne 0) { throw 'Could not populate the document checkout.' }

Set-Location -LiteralPath $checkout
$python = 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $python -B scripts\round172_documents.py paths
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect the R172 paths.' }
```

`paths` prints the bindings and exits. Before rebuilding, verify the printed **Current paper**, **Receipts**, and **Temporary** paths all lie within the new `$rebuildRoot`. The script resolves them as follows.

| Binding | Location in this layout |
| --- | --- |
| `ROOT` | The isolated checkout, `$rebuildRoot\worktrees\paper` |
| `PAPER` | `ROOT/results/unified_exact_round137`, the maintained paper files and local outputs |
| `OUT` | `ROOT/results/unified_exact_round172`, the local R172 document records |
| `TEMP` | `ROOT.parents[1]/temp/round172/pdf`, which is `$rebuildRoot\temp\round172\pdf` |

The printed **Base** is `e8c4a0d3ccbaf1c1a6e6f83242d9163fe29e74e4`, the R171 comparison commit used by the R172 script. The printed **Branch** identifies the published R172 document lineage.

Run the following stages in order only when an export is needed, with `$python` and the checkout from above. Continue to the next stage after the previous one succeeds.

```powershell
& $python -B scripts\round172_documents.py assemble
if ($LASTEXITCODE -ne 0) { throw 'R172 assembly failed.' }
& $python -B scripts\round172_documents.py pdf
if ($LASTEXITCODE -ne 0) { throw 'R172 PDF export failed.' }
& $python -B scripts\round172_documents.py qa
if ($LASTEXITCODE -ne 0) { throw 'R172 PDF QA failed.' }
```

`assemble` writes the assembled Markdown and source records. `pdf` exports both PDFs and their TeX intermediates. `qa` checks those exports and writes page samples under `TEMP` and a QA record under `OUT`. These stages write into the isolated local copies under `PAPER` and `OUT` and use the dedicated `TEMP`. Git leaves the generated files and records local unless someone explicitly commits them.

R172's Windows build used the Python executable shown above (3.12.14 with `pdfplumber`), Pandoc 3.9, XeLaTeX from MiKTeX 25.12, and Poppler's `pdftoppm` on PATH. The export uses the installed Times New Roman, Arial and Consolas fonts and stamps the build date. The published PDFs are the reference for the accepted bytes. [R172 source manifest](../results/unified_exact_round172/source_manifest.json) · [Build record](../results/unified_exact_round172/document_build.json) · [Page QA](../results/unified_exact_round172/document_qa.json) · [Technical review](../results/unified_exact_round172/review_record.md) · [Author memo](../results/unified_exact_round172/author_decision_memo.md)

## Historical R137 solver launch

GI-TBC is Gini-interval tailored branch-and-cut. The R137 launch uses historical S2/ms2 with complete own H, M-B shared inventory/service states, VD-P, uniform pair-only support and AP off. The bare executable's ENS-C compatibility default and the [earlier R135 profile](../config/paper_s2.json) have separate identities.

| R137 binding | Recorded value |
| --- | --- |
| Measured C++ source | `779713ad9a0b01edc538ecb64df9438739127be3` |
| Windows PE | `E:\codes\ExactEBRP-work\build-cache\round137\ExactEBRP.exe`, SHA-256 `d6fd9e6687ac7d4377e2d7fd683d59bd3354d7dfb3a9e5b3723d0fe62b6c7fbd` |
| Gurobi DLL | `D:\gurobi1302\win64\bin\gurobi130.dll`, SHA-256 `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88` |
| AM and guards | AM 0.08, maximum outer depth 8, minimum width `1e-4` |
| H and Native solver | Own H seed 20260626. Gurobi 13.0.2, one thread, presolve −1, Windows affinity mask 4. Solver Seed 0 and the preselected Seed 1 repeat. |
| Physical time | `--T` is the route horizon. The study used 60/60 seconds per unit for pickup/drop, including return unloading. |
| R137 panel budgets | Process caps of 600/1,200/2,400 seconds for 15/20/35 stations, respectively, in the [R137 frozen matrix](../results/unified_exact_round137/matrix_frozen.json). |
| R137 launch clocks | `--cap` is the whole solver-process budget. The frozen vector uses a 30-second shutdown margin, a Native `--time-limit` of cap minus 6, and a supervisor hard stop at cap minus 2. |

The [R137 candidate manifest](../results/unified_exact_round137/candidate_manifest.json) binds the runtime identity. The [R137 entry receipt](../results/unified_exact_round137/entry_check.json) records qualification of 28 default vectors against the 120-position matrix and six refusal cases, with zero native runs. The [continuation record](../results/unified_exact_round137/RESUME.md) records the actual scope of the historical public recovery.

### Display one R137-profile command

The example uses a fresh isolated checkout of the [R137 science commit](https://github.com/yifanXovo/TailoredExact/tree/e735c3447eb1443713c700942d873de1783a4a26) and requires access to the R137 executable and the local launcher Python. Choose an unoccupied checkout and output path under the workspace root.

```powershell
$gitStore = 'E:\codes\ExactEBRP\.git'
$r137 = 'e735c3447eb1443713c700942d873de1783a4a26'
$runId = [guid]::NewGuid().ToString('N')
$checkout = Join-Path 'E:\codes\ExactEBRP-work\worktrees' "r137-reader-$runId"
$output = Join-Path 'E:\codes\ExactEBRP-work\runs' "r137-reader-$runId"
if ((Test-Path -LiteralPath $checkout) -or (Test-Path -LiteralPath $output)) { throw 'Choose unused paths.' }

git --git-dir=$gitStore worktree add --detach --no-checkout $checkout $r137
if ($LASTEXITCODE -ne 0) { throw 'Could not create the R137 worktree.' }
git -C $checkout sparse-checkout set --cone --no-sparse-index config scripts results/unified_exact_round130/inputs
if ($LASTEXITCODE -ne 0) { throw 'Could not set the launcher checkout paths.' }
git -C $checkout read-tree -mu HEAD
if ($LASTEXITCODE -ne 0) { throw 'Could not populate the launcher checkout.' }

Set-Location -LiteralPath $checkout
& 'D:\msys64\ucrt64\bin\python.exe' -B scripts\paper_s2.py `
  --input results\unified_exact_round130\inputs\UC-B20-B.txt `
  --out-dir $output `
  --T 7200 --pickup-time 60 --drop-time 60 --lambda 0.15 --cap 1200 --seed 0 --json
```

The default dry run validates the input, unused output path and executable, then prints the expanded command or JSON plan. With no `--exe`, planning requires the verified R137 PE at its default path. A supplied `--exe` is recorded by its actual hash, along with whether it matches that PE. An invocation with `--run` creates the output directory and starts the Windows C++ producer with the recorded affinity. The default executable run also checks the verified DLL. The Python launcher handles orchestration. Formal H, objective and physical verification, Start, model construction and Optimize are C++ operations.

Production pays for own H, construction, online checks, solve/proof, cleanup and required output. The campaign records separate postverification and total clocks, with H/LP/MIP/Work nested inside production. A launch plan or producer journal covers the entry only. Consult the [R137 reproducibility record](../results/unified_exact_round137/reproducibility.md) for the registered inputs, exact argv, independent checks and full fees.

### Identify the later measured panels

Rounds 169–171 share measured C++ source `781c548b410a2749190e3f0c4b149c2ad885c054` and PE SHA-256 `c6ddf0b62f1200d02a8c654fd3f278ced704130f1a8950fc1e6464b9cbb11e57`. Each panel retains its own input identities, actual argv and complete costs. For example, R171 has a 6-second shutdown margin and a 1,200-second process cap across its 50-station panel. The R137 profile binds the R137 argv even when `--exe` changes the executable.

| Panel | Actual commands, source and results |
| --- | --- |
| R169 paid initialization | [Execution matrix and argv](../results/unified_exact_round169/matrix_execution_frozen.json) · [Source and PE record](../results/unified_exact_round169/source_manifest.json) · [Reproducibility and costs](../results/unified_exact_round169/reproducibility.md) |
| R170 paid confirmation and matched cold controls | [Frozen matrix and argv](../results/unified_exact_round170/matrix_frozen.json) · [Source record](../results/unified_exact_round170/source_manifest.json) · [Reproducibility and costs](../results/unified_exact_round170/reproducibility.md) |
| R171 50-station endpoints | [Frozen matrix](../results/unified_exact_round171/matrix_frozen.json) · [Actual argv records](../results/unified_exact_round171/argv_templates.json) · [Source record](../results/unified_exact_round171/source_manifest.json) · [Reproducibility and costs](../results/unified_exact_round171/reproducibility.md) |

Use R172 [Table 1](../results/unified_exact_round137/paper_body.md#41-comparators-and-panel-protocols) for the paper's panel protocols and the [research index](unified_exact_research_index.md) for the separately recorded earlier studies.
