# -*- mode: python ; coding: utf-8 -*-
# MarkItDown EZ — PyInstaller spec
# 手動維護此檔以確保 magika ONNX 模型與其他 data files 正確打入。

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 收集 magika 的所有 data files（含 ONNX 模型、config JSON 等）
magika_datas = collect_data_files("magika", includes=["**/*"])

# 收集 markitdown converters 目錄下所有資料
markitdown_datas = collect_data_files("markitdown")

a = Analysis(
    ["app.py"],
    pathex=["."],
    binaries=[],
    datas=[
        # 前端資源
        ("templates", "templates"),
        ("static", "static"),
        # magika ONNX 模型及 config
        *magika_datas,
        # markitdown 內部資料（如有）
        *markitdown_datas,
    ],
    hiddenimports=[
        # Flask & Werkzeug
        "flask",
        "werkzeug",
        "werkzeug.serving",
        "werkzeug.middleware",
        # markitdown 核心
        "markitdown",
        "markitdown._markitdown",
        "markitdown.converters",
        "markitdown.converter_utils",
        # PDF
        "pdfminer",
        "pdfminer.high_level",
        "pdfminer.layout",
        "pdfminer.pdfpage",
        "pdfminer.pdfinterp",
        "pdfminer.converter",
        "pdfplumber",
        # Word
        "mammoth",
        "docx",
        "docx2txt",
        # PowerPoint
        "pptx",
        # Excel
        "openpyxl",
        "xlrd",
        # HTML
        "bs4",
        "markdownify",
        # EPUB
        "ebooklib",
        # 其他
        "charset_normalizer",
        "magika",
        "onnxruntime",
        "pandas",
        "numpy",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的大型套件
        "speechrecognition",
        "youtube_transcript_api",
        "azure",
        "matplotlib",
        "tkinter",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MarkItDown EZ",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不顯示終端機視窗
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MarkItDown EZ",
)

# macOS .app bundle
app = BUNDLE(
    coll,
    name="MarkItDown EZ.app",
    icon=None,
    bundle_identifier="com.markitdown.ez",
    info_plist={
        "NSHighResolutionCapable": True,
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1.0.0",
        "LSUIElement": False,  # 顯示在 Dock
        "NSAppTransportSecurity": {
            "NSAllowsLocalNetworking": True,
        },
    },
)
