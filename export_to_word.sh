#!/bin/bash

# Export Research Paper to Word Format (.docx)
# Uses pandoc with academic styling

INPUT_FILE="RESEARCH_PAPER.md"
OUTPUT_FILE="RESEARCH_PAPER.docx"

echo "🔄 Converting $INPUT_FILE to Word format..."

# Use pandoc to convert markdown to Word with proper formatting
pandoc "$INPUT_FILE" \
    -f markdown \
    -t docx \
    -o "$OUTPUT_FILE" \
    --toc \
    --toc-depth=3 \
    --number-sections \
    --syntax-highlighting=tango \
    --metadata title="Mycelial Intelligence Networks: A Bio-Inspired Architecture for Distributed AI Agent Collaboration" \
    --metadata author="Qilbee Research Team" \
    --metadata date="November 1, 2025"

if [ $? -eq 0 ]; then
    echo "✅ Successfully exported to $OUTPUT_FILE"
    echo "📄 File size: $(ls -lh "$OUTPUT_FILE" | awk '{print $5}')"
    echo "📍 Location: $(pwd)/$OUTPUT_FILE"
else
    echo "❌ Export failed"
    exit 1
fi
