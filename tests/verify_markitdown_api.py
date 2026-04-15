"""
Card 0: markitdown API 驗證腳本
驗證 convert() 的呼叫方式、回傳值結構、各格式支援狀態。
"""
import io
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")

from markitdown import MarkItDown  # noqa: E402

md = MarkItDown()

# ---------- 1. 驗證 convert() 簽名 ----------
print("=" * 60)
print("1. 驗證 convert() 方法簽名")
print("=" * 60)
import inspect

sig = inspect.signature(md.convert)
print(f"   convert() signature: {sig}")
print(f"   Parameters: {list(sig.parameters.keys())}")
print()

# ---------- 2. 驗證回傳值結構 ----------
print("=" * 60)
print("2. 驗證回傳值結構 (使用 sample.csv)")
print("=" * 60)
result = md.convert(os.path.join(FIXTURES_DIR, "sample.csv"))
print(f"   type(result): {type(result)}")
print(f"   dir(result):  {[a for a in dir(result) if not a.startswith('_')]}")
print(f"   result.text_content type: {type(result.text_content)}")
print(f"   result.text_content[:200]: {repr(result.text_content[:200])}")
print()

# ---------- 3. 測試 file-like object ----------
print("=" * 60)
print("3. 測試 file-like object 傳入方式")
print("=" * 60)
try:
    with open(os.path.join(FIXTURES_DIR, "sample.csv"), "rb") as f:
        result_fobj = md.convert(f)
    print(f"   ✅ file-like object 可用")
    print(f"   result.text_content[:100]: {repr(result_fobj.text_content[:100])}")
except Exception as e:
    print(f"   ❌ file-like object 不可用: {e}")
print()

# 也測試帶 file_extension 的 stream
try:
    with open(os.path.join(FIXTURES_DIR, "sample.csv"), "rb") as f:
        result_fobj2 = md.convert_stream(f, file_extension=".csv")
    print(f"   ✅ convert_stream() 可用")
    print(f"   result.text_content[:100]: {repr(result_fobj2.text_content[:100])}")
except AttributeError:
    print(f"   ℹ️  convert_stream() 方法不存在")
except Exception as e:
    print(f"   ❌ convert_stream() 失敗: {e}")
print()

# ---------- 4. 各格式逐一測試 ----------
print("=" * 60)
print("4. 各格式轉換測試")
print("=" * 60)

formats = {
    "PDF": "sample.pdf",
    "DOCX": "sample.docx",
    "PPTX": "sample.pptx",
    "XLSX": "sample.xlsx",
    "HTML": "sample.html",
    "CSV": "sample.csv",
    "JSON": "sample.json",
    "XML": "sample.xml",
    "EPUB": "sample.epub",
    "ZIP": "sample.zip",
}

results = {}
for fmt, filename in formats.items():
    filepath = os.path.join(FIXTURES_DIR, filename)
    print(f"\n--- {fmt} ({filename}) ---")
    try:
        r = md.convert(filepath)
        content = r.text_content
        results[fmt] = {
            "status": "✅",
            "content_length": len(content),
            "preview": repr(content[:150]),
            "has_content": bool(content.strip()),
        }
        print(f"   ✅ 成功 | 長度: {len(content)} chars")
        print(f"   Preview: {repr(content[:150])}")
    except Exception as e:
        results[fmt] = {
            "status": "❌",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
        print(f"   ❌ 失敗: {e}")

# ---------- 5. XLS (舊版 Excel) ----------
print(f"\n--- XLS (old Excel, no fixture) ---")
print("   ℹ️  需要 xlrd 套件，暫不測試（需確認 markitdown extras）")

# ---------- 6. 摘要 ----------
print("\n" + "=" * 60)
print("5. 摘要")
print("=" * 60)
for fmt, info in results.items():
    if info["status"] == "✅":
        print(f"   {info['status']} {fmt}: {info['content_length']} chars, has_content={info['has_content']}")
    else:
        print(f"   {info['status']} {fmt}: {info['error']}")
