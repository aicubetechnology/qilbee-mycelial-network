#!/bin/bash

# Export Research Paper to PDF Format (via HTML)
# Uses pandoc to convert markdown to HTML, then uses wkhtmltopdf or print to PDF

INPUT_FILE="RESEARCH_PAPER.md"
OUTPUT_HTML="RESEARCH_PAPER_temp.html"
OUTPUT_FILE="RESEARCH_PAPER.pdf"

echo "🔄 Converting $INPUT_FILE to PDF format (via HTML)..."

# First, convert to standalone HTML with styling
pandoc "$INPUT_FILE" \
    -f markdown \
    -t html \
    -o "$OUTPUT_HTML" \
    --standalone \
    --toc \
    --toc-depth=3 \
    --number-sections \
    --syntax-highlighting=tango \
    --css=https://cdn.jsdelivr.net/npm/github-markdown-css@5.5.1/github-markdown.min.css \
    --metadata title="Mycelial Intelligence Networks: A Bio-Inspired Architecture for Distributed AI Agent Collaboration" \
    --metadata author="Qilbee Research Team" \
    --metadata date="November 1, 2025"

if [ $? -ne 0 ]; then
    echo "❌ HTML conversion failed"
    exit 1
fi

echo "✅ HTML generated: $OUTPUT_HTML"

# Check for wkhtmltopdf
if command -v wkhtmltopdf &> /dev/null; then
    echo "🔄 Converting HTML to PDF using wkhtmltopdf..."
    wkhtmltopdf \
        --enable-local-file-access \
        --page-size Letter \
        --margin-top 20mm \
        --margin-bottom 20mm \
        --margin-left 20mm \
        --margin-right 20mm \
        "$OUTPUT_HTML" "$OUTPUT_FILE"

    if [ $? -eq 0 ]; then
        echo "✅ Successfully exported to $OUTPUT_FILE"
        echo "📄 File size: $(ls -lh "$OUTPUT_FILE" | awk '{print $5}')"
        echo "📍 Location: $(pwd)/$OUTPUT_FILE"
        rm "$OUTPUT_HTML"
        exit 0
    fi
fi

# If wkhtmltopdf not available, use weasyprint
if command -v weasyprint &> /dev/null; then
    echo "🔄 Converting HTML to PDF using weasyprint..."
    weasyprint "$OUTPUT_HTML" "$OUTPUT_FILE"

    if [ $? -eq 0 ]; then
        echo "✅ Successfully exported to $OUTPUT_FILE"
        echo "📄 File size: $(ls -lh "$OUTPUT_FILE" | awk '{print $5}')"
        echo "📍 Location: $(pwd)/$OUTPUT_FILE"
        rm "$OUTPUT_HTML"
        exit 0
    fi
fi

echo "⚠️  No PDF converter found. You can:"
echo "   1. Install wkhtmltopdf: brew install --cask wkhtmltopdf"
echo "   2. Install weasyprint: pip install weasyprint"
echo "   3. Or open $OUTPUT_HTML in a browser and print to PDF"
echo ""
echo "📄 HTML file available at: $(pwd)/$OUTPUT_HTML"
