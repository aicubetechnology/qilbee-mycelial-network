#!/bin/bash

# Export Research Paper to Multiple Formats
# Generates Word (.docx), PDF, and HTML versions

INPUT_FILE="RESEARCH_PAPER.md"
OUTPUT_WORD="RESEARCH_PAPER.docx"
OUTPUT_PDF="RESEARCH_PAPER.pdf"
OUTPUT_HTML="RESEARCH_PAPER.html"

echo "📚 Exporting Research Paper to Multiple Formats"
echo "================================================"
echo ""

# Metadata
TITLE="Mycelial Intelligence Networks: A Bio-Inspired Architecture for Distributed AI Agent Collaboration"
AUTHOR="Qilbee Research Team"
DATE="November 1, 2025"

# Export to Word (.docx)
echo "🔄 [1/3] Exporting to Word (.docx)..."
pandoc "$INPUT_FILE" \
    -f markdown \
    -t docx \
    -o "$OUTPUT_WORD" \
    --toc \
    --toc-depth=3 \
    --number-sections \
    --syntax-highlighting=tango \
    --metadata title="$TITLE" \
    --metadata author="$AUTHOR" \
    --metadata date="$DATE"

if [ $? -eq 0 ]; then
    echo "✅ Word export successful: $OUTPUT_WORD ($(ls -lh "$OUTPUT_WORD" | awk '{print $5}'))"
else
    echo "❌ Word export failed"
fi

echo ""

# Export to HTML
echo "🔄 [2/3] Exporting to HTML..."
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
    --metadata title="$TITLE" \
    --metadata author="$AUTHOR" \
    --metadata date="$DATE"

if [ $? -eq 0 ]; then
    echo "✅ HTML export successful: $OUTPUT_HTML ($(ls -lh "$OUTPUT_HTML" | awk '{print $5}'))"
else
    echo "❌ HTML export failed"
fi

echo ""

# Export to PDF (using weasyprint via venv)
echo "🔄 [3/3] Exporting to PDF..."
if [ -d "venv" ]; then
    source venv/bin/activate
    weasyprint "$OUTPUT_HTML" "$OUTPUT_PDF" 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "✅ PDF export successful: $OUTPUT_PDF ($(ls -lh "$OUTPUT_PDF" | awk '{print $5}'))"
    else
        echo "❌ PDF export failed"
    fi
else
    echo "⚠️  Virtual environment not found. Install weasyprint: pip install weasyprint"
fi

echo ""
echo "================================================"
echo "✅ Export Complete!"
echo ""
echo "📄 Available formats:"
echo "   • Markdown: $INPUT_FILE"
echo "   • Word:     $OUTPUT_WORD"
echo "   • HTML:     $OUTPUT_HTML"
echo "   • PDF:      $OUTPUT_PDF"
echo ""
echo "📍 Location: $(pwd)"
