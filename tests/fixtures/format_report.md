# MarkItDown API 格式驗證報告

> **日期**：2026-04-15  
> **markitdown 版本**：0.1.5  
> **Python 版本**：3.12.4  

---

## 1. `convert()` 方法簽名

```python
convert(
    source: Union[str, requests.models.Response, pathlib.Path, BinaryIO],
    *,
    stream_info: Optional[StreamInfo] = None,
    **kwargs: Any
) -> DocumentConverterResult
```

### 呼叫方式

| 方式 | 支援 | 說明 |
|---|---|---|
| `convert(file_path: str)` | ✅ | 傳入檔案路徑字串 |
| `convert(file_path: Path)` | ✅ | 傳入 pathlib.Path |
| `convert(file_obj: BinaryIO)` | ✅ | 傳入 file-like object（已開啟的 `rb` 模式檔案） |
| `convert_stream(stream, file_extension=".csv")` | ✅ | 傳入 stream + 指定副檔名 |

### 回傳值結構

```python
DocumentConverterResult:
    .text_content: str   # 轉換後的 Markdown 文字
    .markdown: str       # 同 text_content（別名）
    .title: str          # 文件標題（若有）
```

**結論**：後端使用 `convert(file_path)` 即可，傳入暫存檔案路徑最簡單。

---

## 2. 各格式測試結果

| 格式 | 檔案 | 狀態 | 輸出長度 | 內容預覽 | 所需 extras/依賴 |
|---|---|---|---|---|---|
| PDF | sample.pdf | ✅ | 11 chars | `Hello PDF` | `[pdf]` → pdfminer-six, pdfplumber |
| DOCX | sample.docx | ✅ | 60 chars | `# Test Document\n\nThis is a test...` | `[docx]` → mammoth |
| PPTX | sample.pptx | ✅ | 66 chars | `<!-- Slide number: 1 -->\n# Test Slide...` | `[pptx]` → python-pptx |
| XLSX | sample.xlsx | ✅ | 68 chars | `## Sheet1\n\| Name \| Score \|...` | `[xlsx]` → openpyxl, pandas |
| XLS | sample.xls | ✅ | 57 chars | `## Sheet1\n\| Name \| Score \|...` | 需額外安裝 `xlrd` |
| HTML | sample.html | ✅ | 49 chars | `# Hello MarkItDown\n\nThis is a **test**...` | 內建（beautifulsoup4, markdownify） |
| CSV | sample.csv | ✅ | 86 chars | `\| Name \| Age \| City \|...` | 內建 |
| JSON | sample.json | ✅ | 102 chars | `{\n  "project": "MarkItDown EZ"...` | 內建 |
| XML | sample.xml | ✅ | 110 chars | `<?xml version="1.0"...` | 內建 |
| EPUB | sample.epub | ✅ | 52 chars | `**Title:** Test EPUB\n\n# Chapter 1...` | 內建（ZIP 解壓 + HTML 處理） |
| ZIP | sample.zip | ✅ | 211 chars | `Content from the zip file...` | 內建 |

---

## 3. requirements.txt 調整建議

原計畫：`markitdown[pdf,docx,pptx,xlsx]`

**建議新增**：
- `xlrd`：XLS 格式支援需要此套件，markitdown extras 未包含
- `xlwt`：僅用於測試 fixture 產生，**不需**加入生產依賴

**最終 extras**：`markitdown[pdf,docx,pptx,xlsx]` + `xlrd`（獨立安裝）

---

## 4. 注意事項

1. **JSON/XML 格式**：markitdown 對 JSON 和 XML 的「轉換」是原文保留（非結構化轉 Markdown 表格），這是正常行為
2. **file-like object**：雖然支援，但建議後端使用檔案路徑方式呼叫，因為 markitdown 內部的 magika（檔案類型偵測）對路徑更穩定
3. **magika 依賴**：markitdown 0.1.5 使用 magika 做自動格式偵測，會拉入 onnxruntime（~17MB），這會影響打包體積
4. **python-docx**：mammoth 處理 DOCX，但 fixture 產生需要 python-docx；mammoth 是 markitdown[docx] 的依賴，python-docx 不是
