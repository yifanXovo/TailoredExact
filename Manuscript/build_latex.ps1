$ErrorActionPreference = 'Stop'
$userMiktex = Join-Path $env:LOCALAPPDATA 'Programs\MiKTeX\miktex\bin\x64'
if (Test-Path $userMiktex) {
    $env:PATH = "$userMiktex;$env:PATH"
}
Push-Location $PSScriptRoot
try {
    if (Get-Command pdflatex -ErrorAction SilentlyContinue) {
        pdflatex -interaction=nonstopmode -halt-on-error main.tex
        bibtex main
        pdflatex -interaction=nonstopmode -halt-on-error main.tex
        pdflatex -interaction=nonstopmode -halt-on-error main.tex
    } elseif ((Get-Command latexmk -ErrorAction SilentlyContinue) -and (Get-Command perl -ErrorAction SilentlyContinue)) {
        latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
    } elseif (Get-Command xelatex -ErrorAction SilentlyContinue) {
        xelatex -interaction=nonstopmode -halt-on-error main.tex
        bibtex main
        xelatex -interaction=nonstopmode -halt-on-error main.tex
        xelatex -interaction=nonstopmode -halt-on-error main.tex
    } elseif (Get-Command tectonic -ErrorAction SilentlyContinue) {
        tectonic main.tex
    } else {
        throw 'No supported LaTeX engine found (latexmk, pdflatex, xelatex, tectonic).'
    }
} finally {
    Pop-Location
}
