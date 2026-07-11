# LaTeX Compile Status

Final multi-pass compilation succeeded with MiKTeX 25.12 using `pdflatex`,
`bibtex`, and two additional `pdflatex` passes. The fresh package-local table
is included and `main.pdf` contains eight pages. The complete final transcript
is in `compile_log.txt`.

Rebuild with:

```powershell
powershell -ExecutionPolicy Bypass -File Manuscript/build_latex.ps1
```

The build script tries `latexmk`, `pdflatex`, `xelatex`, then `tectonic`.
