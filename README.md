# MarkItDown EZ

將各種文件格式一鍵轉換為 Markdown 的本地桌面應用程式。基於 [Microsoft MarkItDown](https://github.com/microsoft/markitdown) 封裝，提供簡潔的 Web UI，無需雲端、無需帳號，所有轉換在本機完成。

---

## 支援格式

| 格式 | 副檔名 |
|------|--------|
| PDF | `.pdf` |
| Word | `.docx` |
| PowerPoint | `.pptx` |
| Excel | `.xlsx` / `.xls` |
| HTML | `.html` / `.htm` |
| CSV | `.csv` |
| JSON | `.json` |
| XML | `.xml` |
| EPUB | `.epub` |
| ZIP | `.zip` |

> 單檔上限：**50 MB**

---

## 快速使用

### 直接執行（已打包版）

**macOS**

1. 從 `dist/` 取得 `MarkItDown EZ.app`
2. 雙擊開啟，瀏覽器會自動彈出
3. 拖曳或選擇檔案 → 點擊「轉換」→ 下載 `.md` 檔案

**Windows**

1. 從 `dist/` 取得 `MarkItDown EZ/MarkItDown EZ.exe`
2. 雙擊執行，瀏覽器會自動彈出
3. 操作方式同上

### 從原始碼執行

```bash
# 建立虛擬環境並安裝依賴
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate.bat
pip install -r requirements.txt

# 啟動應用程式
python app.py
```

瀏覽器會自動在隨機可用 port 開啟（例如 `http://127.0.0.1:54321`）。  
關閉瀏覽器頁籤後，應用程式會在 30 秒內自動退出。

---

## 打包說明

打包前請確認已啟用虛擬環境，且 `requirements.txt` 依賴均已安裝。

### macOS → `.app`

```bash
bash build/build_mac.sh
```

產出位置：`dist/MarkItDown EZ.app`

腳本會依序執行：
1. 建立 / 啟用虛擬環境
2. 安裝依賴及 PyInstaller
3. 執行測試套件（通過才繼續）
4. 呼叫 PyInstaller 打包為 `.app` bundle

### Windows → `.exe`

```bat
build\build_win.bat
```

產出位置：`dist\MarkItDown EZ\MarkItDown EZ.exe`

### 手動使用 spec 檔打包

如需細調打包設定（例如修改 Info.plist、圖示、額外 hiddenimports），可直接編輯 `markitdown_ez.spec` 後執行：

```bash
pyinstaller markitdown_ez.spec --noconfirm --clean
```

---

## 開發說明

### 專案結構

```
markitdown_ez/
├── app.py                  # Flask 後端（唯一 Python 入口）
├── requirements.txt        # 依賴清單
├── markitdown_ez.spec      # PyInstaller 打包設定
├── build/
│   ├── build_mac.sh        # macOS 打包腳本
│   └── build_win.bat       # Windows 打包腳本
├── templates/
│   └── index.html          # 前端單頁應用
├── static/
│   └── purify.min.js       # DOMPurify（XSS 防護）
└── tests/
    ├── conftest.py
    ├── fixtures/           # 各格式測試用樣本檔
    ├── generate_fixtures.py
    ├── test_app.py         # API 基礎測試
    ├── test_edge_cases.py  # 邊界條件測試
    └── verify_markitdown_api.py
```

### API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| `GET` | `/` | 前端頁面 |
| `GET` | `/health` | 健康檢查 |
| `GET` | `/formats` | 支援格式清單及上傳大小限制 |
| `POST` | `/convert` | 上傳檔案，回傳 Markdown |
| `POST` | `/heartbeat` | 前端心跳 ping |
| `POST` | `/shutdown` | 觸發延遲退出 |

**`POST /convert` 範例**

```bash
curl -X POST http://127.0.0.1:PORT/convert \
  -F "file=@document.pdf" \
  | jq '{filename, preview: .markdown[:200]}'
```

回應格式：
```json
{
  "markdown": "# Document Title\n...",
  "filename": "document.md"
}
```

### 執行測試

```bash
# 啟用虛擬環境後
pytest tests/ -v --cov=app --cov-report=term-missing
```

測試前請先確認 `tests/fixtures/` 下已有各格式的樣本檔。若尚未產生，可執行：

```bash
python tests/generate_fixtures.py
```

### 依賴更新

修改 `requirements.txt` 後重新安裝：

```bash
pip install -r requirements.txt
```

目前核心依賴版本：

| 套件 | 版本 |
|------|------|
| `markitdown[pdf,docx,pptx,xlsx]` | 0.1.5 |
| `xlrd` | 2.0.2 |
| `Flask` | 3.1.3 |
| `pytest` | 9.0.3 |
| `pytest-cov` | 7.1.0 |

---

## 運作原理

1. 啟動時自動綁定隨機可用 port，避免與其他服務衝突
2. 前端每 10 秒送出心跳；若超過 30 秒無心跳，後端自動退出
3. 瀏覽器關閉時觸發 `beforeunload` 呼叫 `/shutdown`，應用程式延遲 1 秒後退出
4. 上傳的檔案寫入系統暫存目錄，轉換完成後立即刪除，不留存任何使用者資料
