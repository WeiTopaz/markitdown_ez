@echo off
REM MarkItDown EZ — Windows 打包腳本
REM 產出：dist\MarkItDown EZ\MarkItDown EZ.exe

cd /d "%~dp0\.."
echo === MarkItDown EZ Windows Build ===
echo Project dir: %CD%

REM 確認虛擬環境
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat
pip install -q -r requirements.txt
pip install -q pyinstaller

echo Running tests before build...
python -m pytest tests/ -q
echo.

echo Building .exe with PyInstaller...
pyinstaller ^
    --name "MarkItDown EZ" ^
    --noconfirm ^
    --clean ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --hidden-import markitdown ^
    --hidden-import markitdown.converters ^
    --hidden-import pdfminer ^
    --hidden-import pdfminer.high_level ^
    --hidden-import pdfplumber ^
    --hidden-import mammoth ^
    --hidden-import pptx ^
    --hidden-import openpyxl ^
    --hidden-import xlrd ^
    --hidden-import pandas ^
    --hidden-import bs4 ^
    --hidden-import markdownify ^
    --hidden-import magika ^
    --hidden-import onnxruntime ^
    --hidden-import charset_normalizer ^
    --hidden-import ebooklib ^
    app.py

echo.
echo Zipping output folder...
powershell -Command "Compress-Archive -Path 'dist\MarkItDown EZ' -DestinationPath 'MarkItDown-EZ-win.zip' -Force"

echo.
echo === Build complete ===
echo Output: MarkItDown-EZ-win.zip
pause
