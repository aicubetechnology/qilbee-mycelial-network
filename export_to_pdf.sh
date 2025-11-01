#!/bin/bash

# Export Research Paper to PDF Format
# Uses pandoc with LaTeX engine for high-quality academic PDF

INPUT_FILE="RESEARCH_PAPER.md"
OUTPUT_FILE="RESEARCH_PAPER.pdf"

echo "🔄 Converting $INPUT_FILE to PDF format..."

# Check if LaTeX is installed
if ! command -v pdflatex &> /dev/null; then
    echo "⚠️  LaTeX not found. Installing BasicTeX for PDF generation..."
    brew install --cask basictex

    # Update PATH for current session
    export PATH="/Library/TeX/texbin:$PATH"

    # Update tlmgr and install required packages
    sudo tlmgr update --self
    sudo tlmgr install collection-fontsrecommended
fi

# Use pandoc to convert markdown to PDF with academic styling
pandoc "$INPUT_FILE" \
    -f markdown \
    -t pdf \
    -o "$OUTPUT_FILE" \
    --toc \
    --toc-depth=3 \
    --number-sections \
    --syntax-highlighting=tango \
    --pdf-engine=pdflatex \
    --variable geometry:margin=1in \
    --variable fontsize=11pt \
    --variable documentclass=article \
    --variable classoption=twocolumn \
    --metadata title="Mycelial Intelligence Networks: A Bio-Inspired Architecture for Distributed AI Agent Collaboration" \
    --metadata author="Qilbee Research Team" \
    --metadata date="November 1, 2025"

if [ $? -eq 0 ]; then
    echo "✅ Successfully exported to $OUTPUT_FILE"
    echo "📄 File size: $(ls -lh "$OUTPUT_FILE" | awk '{print $5}')"
    echo "📍 Location: $(pwd)/$OUTPUT_FILE"
else
    echo "❌ Export failed"
    echo "💡 Note: PDF export requires LaTeX. Install with: brew install --cask basictex"
    exit 1
fi
