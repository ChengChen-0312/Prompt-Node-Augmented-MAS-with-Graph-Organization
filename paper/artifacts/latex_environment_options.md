# LaTeX Environment Options

- Installation performed: `False`
- latexmk: `None`
- pdflatex: `None`
- Compile status: `blocked_no_latex_engine`

## Install Options

### MacTeX

- Command/source: `Install MacTeX from tug.org/mactex or Homebrew cask if acceptable locally.`
- Tradeoff: Most complete and least likely to miss packages; large install.

### TinyTeX

- Command/source: `Install TinyTeX, then add missing packages on demand.`
- Tradeoff: Smaller footprint; may need iterative package installs.

### Tectonic

- Command/source: `Install tectonic for self-contained compilation.`
- Tradeoff: Convenient for many papers, but journal-specific style compatibility should be checked.

## Compile Command After Engine Exists

- `cd paper && latexmk -pdf -interaction=nonstopmode main.tex`
- `cd paper && pdflatex -interaction=nonstopmode main.tex && bibtex main && pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex`
- `cd paper && tectonic main.tex`
