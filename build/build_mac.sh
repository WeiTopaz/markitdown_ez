#!/usr/bin/env bash
# MarkItDown EZ — macOS 打包腳本
# 產出：dist/MarkItDown EZ.app
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=== MarkItDown EZ macOS Build ==="
echo "Project dir: $PROJECT_DIR"

# 確認虛擬環境
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt
pip install -q pyinstaller

echo "Running tests before build..."
python -m pytest tests/ -q
echo ""

echo "Building .app with PyInstaller..."
pyinstaller \
    --name "MarkItDown EZ" \
    --windowed \
    --noconfirm \
    --clean \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --hidden-import markitdown \
    --hidden-import markitdown.converters \
    --hidden-import pdfminer \
    --hidden-import pdfminer.high_level \
    --hidden-import pdfplumber \
    --hidden-import mammoth \
    --hidden-import pptx \
    --hidden-import openpyxl \
    --hidden-import xlrd \
    --hidden-import pandas \
    --hidden-import bs4 \
    --hidden-import markdownify \
    --hidden-import magika \
    --hidden-import onnxruntime \
    --hidden-import charset_normalizer \
    --hidden-import ebooklib \
    app.py

echo ""
echo "Zipping .app bundle..."
cd dist
zip -r "../MarkItDown-EZ-mac.zip" "MarkItDown EZ.app"
cd ..

echo ""
echo "=== Build complete ==="
echo "Output: MarkItDown-EZ-mac.zip"
