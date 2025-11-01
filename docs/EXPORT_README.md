# Research Paper Export Guide

This directory contains scripts to export the research paper (`RESEARCH_PAPER.md`) to multiple formats suitable for academic publication and distribution.

## Available Formats

| Format | File | Use Case |
|--------|------|----------|
| **Markdown** | `RESEARCH_PAPER.md` | Source format, version control |
| **Word** | `RESEARCH_PAPER.docx` | Editing, journal submissions |
| **PDF** | `RESEARCH_PAPER.pdf` | Final distribution, printing |
| **HTML** | `RESEARCH_PAPER.html` | Web publishing, previewing |

## Quick Start

### Export All Formats at Once

```bash
./export_all.sh
```

This will generate Word, HTML, and PDF versions in one command.

### Export Individual Formats

```bash
# Word only
./export_to_word.sh

# PDF only (requires venv with weasyprint)
source venv/bin/activate
./export_to_pdf_simple.sh
```

## Dependencies

All export scripts require **pandoc**:

```bash
brew install pandoc
```

For PDF generation, **weasyprint** is required:

```bash
# Install in virtual environment
source venv/bin/activate
pip install weasyprint
```

## Export Features

### Word (.docx) Export

- ✅ Automatic table of contents
- ✅ Numbered sections and subsections
- ✅ Syntax highlighting for code blocks
- ✅ Proper academic metadata (title, author, date)
- ✅ Compatible with Microsoft Word, Google Docs, LibreOffice

### PDF Export

- ✅ Professional layout with margins
- ✅ Table of contents with page numbers
- ✅ Numbered sections
- ✅ Syntax highlighting
- ✅ High-quality typography
- ✅ Printable (Letter size)

### HTML Export

- ✅ Standalone file (CSS embedded)
- ✅ GitHub-style markdown CSS
- ✅ Interactive table of contents
- ✅ Responsive design
- ✅ Can be opened in any browser

## Generated Files

After running `./export_all.sh`:

```
RESEARCH_PAPER.md       67KB    Original markdown
RESEARCH_PAPER.docx     46KB    Microsoft Word format
RESEARCH_PAPER.html    ~80KB    Web format
RESEARCH_PAPER.pdf     277KB    Print-ready PDF
```

## Academic Submission

### Conference Submissions (NeurIPS, ICML, AAAI)

Most conferences accept:
1. **PDF** (primary format) - Use `RESEARCH_PAPER.pdf`
2. **LaTeX source** (optional) - Can be converted from markdown if needed

### Journal Submissions

Most journals accept:
1. **Word** (preferred) - Use `RESEARCH_PAPER.docx`
2. **PDF** (for review) - Use `RESEARCH_PAPER.pdf`

### ArXiv Preprints

ArXiv accepts:
1. **PDF** (compiled) - Use `RESEARCH_PAPER.pdf`
2. **LaTeX source** (for processing) - Can be generated via pandoc

## Advanced Options

### Custom Styling

Edit the export scripts to customize:
- Page margins
- Font sizes
- CSS styling
- Syntax highlighting themes

### LaTeX/PDF Alternative

If you prefer LaTeX-based PDF generation (requires LaTeX installation):

```bash
# Install BasicTeX (requires sudo password)
brew install --cask basictex

# Add to PATH
export PATH="/Library/TeX/texbin:$PATH"

# Use LaTeX engine
pandoc RESEARCH_PAPER.md -o RESEARCH_PAPER.pdf \
  --pdf-engine=pdflatex \
  --toc --number-sections
```

## Troubleshooting

### "pandoc: command not found"

```bash
brew install pandoc
```

### "weasyprint: command not found"

```bash
source venv/bin/activate
pip install weasyprint
```

### PDF Export Fails

1. Check that `venv` exists and weasyprint is installed
2. Try HTML export first: `./export_to_word.sh`
3. Open HTML in browser and print to PDF manually

### LaTeX Not Found

LaTeX-based PDF generation requires BasicTeX or MacTeX:

```bash
brew install --cask basictex
```

## Automation

To automatically export after changes:

```bash
# Watch for changes and auto-export
while true; do
  inotifywait -e modify RESEARCH_PAPER.md
  ./export_all.sh
done
```

Or use a file watcher like `entr`:

```bash
echo RESEARCH_PAPER.md | entr ./export_all.sh
```

## File Locations

All exported files are placed in the project root:

```
/Users/kimera/projects/qilbee-mycelial-network/
├── RESEARCH_PAPER.md       # Source
├── RESEARCH_PAPER.docx     # Word
├── RESEARCH_PAPER.html     # Web
├── RESEARCH_PAPER.pdf      # PDF
├── export_all.sh           # Main export script
├── export_to_word.sh       # Word only
└── export_to_pdf_simple.sh # PDF only
```

## Quality Checklist

Before submission, verify:

- [ ] All tables render correctly
- [ ] All citations are properly formatted
- [ ] All figures/diagrams are included
- [ ] Table of contents is accurate
- [ ] Page numbers are correct (PDF)
- [ ] Metadata (title, author, date) is correct
- [ ] No formatting errors or broken sections

## Support

For issues with export scripts, check:
1. Pandoc version: `pandoc --version` (should be 3.8+)
2. Python version: `python --version` (should be 3.11+)
3. Weasyprint installation: `pip show weasyprint`

---

**Last Updated**: November 1, 2025
**Export Tools**: Pandoc 3.8.2.1, Weasyprint 66.0
