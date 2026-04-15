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

## 快速使用（推薦）

> 不需安裝 Python，不需網路，下載即用。

### 步驟

1. 前往 [GitHub Releases](../../releases) 頁面
2. 依平台下載對應檔案：

   | 平台 | 下載檔案 |
   |------|---------|
   | macOS | `MarkItDown-EZ-mac.zip` |
   | Windows | `MarkItDown-EZ-win.zip` |

3. 解壓縮後執行：
   - **macOS**：雙擊 `MarkItDown EZ.app`
   - **Windows**：雙擊 `MarkItDown EZ.exe`

4. 瀏覽器自動開啟，拖曳或選擇檔案 → 點擊「轉換」→ 下載 `.md` 檔案

---

### macOS 首次開啟說明

未經 Apple 公證的應用程式，第一次開啟時 macOS 會顯示安全警告。

**方法一（推薦）**：右鍵點擊 `MarkItDown EZ.app` → 選擇「開啟」→ 點選「開啟」

**方法二**（終端機）：
```bash
xattr -cr "MarkItDown EZ.app"
```
執行後即可正常雙擊開啟。

---

### Windows 首次執行說明

首次執行 `.exe` 時，Windows SmartScreen 可能顯示「已保護您的電腦」警告。

點選「**更多資訊**」→「**仍要執行**」即可。

---

## 從原始碼執行（開發用）

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

## 打包發版（維護者）

在各自平台上執行打包腳本，產出可發布的 zip 檔案。

**macOS**（在 Mac 上執行）：
```bash
bash build/build_mac.sh
```
產出：`MarkItDown-EZ-mac.zip`（內含 `MarkItDown EZ.app`）

**Windows**（在 Windows 上執行）：
```bat
build\build_win.bat
```
產出：`MarkItDown-EZ-win.zip`（內含 `MarkItDown EZ\` 資料夾）

腳本會依序：建立虛擬環境 → 安裝依賴 → 執行測試（失敗則中止）→ PyInstaller 打包 → 壓縮為 zip。

手動調整打包設定（圖示、Info.plist、hiddenimports 等）：
```bash
pyinstaller markitdown_ez.spec --noconfirm --clean
```

### 用 GitHub Actions 觸發正式 Release

只要 push 一個符合 `v*.*.*` 格式的 tag，GitHub 就會自動執行 `.github/workflows/build.yml`：

```bash
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin v1.0.1
```

workflow 會自動完成以下工作：

1. 在 **macOS runner** 打包 `MarkItDown-EZ-mac.zip`（內含 `MarkItDown EZ.app`）
2. 在 **Windows runner** 打包 `MarkItDown-EZ-win.zip`（內含 `MarkItDown EZ.exe`）
3. 自動建立對應的 **GitHub Release**，並把兩個 zip 當成附件上傳

可在 GitHub 的 **Actions** 頁面查看建置進度，完成後到 **Releases** 頁面下載：

- `MarkItDown-EZ-win.zip`
- `MarkItDown-EZ-mac.zip`

---

## 專案結構

```
markitdown_ez/
├── app.py                  # Flask 後端（唯一 Python 入口）
├── requirements.txt        # 依賴清單
├── markitdown_ez.spec      # PyInstaller 打包設定
├── .github/
│   └── workflows/
│       └── build.yml       # CI/CD：build + release
├── build/
│   ├── build_mac.sh        # macOS 本機打包腳本（備案）
│   └── build_win.bat       # Windows 本機打包腳本（備案）
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

---

## API 端點

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

---

## 執行測試

```bash
# 啟用虛擬環境後
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## 運作原理

1. 啟動時自動綁定隨機可用 port，避免與其他服務衝突
2. 前端每 10 秒送出心跳；若超過 30 秒無心跳，後端自動退出
3. 瀏覽器關閉時觸發 `beforeunload` 呼叫 `/shutdown`，應用程式延遲 1 秒後退出
4. 上傳的檔案寫入系統暫存目錄，轉換完成後立即刪除，不留存任何使用者資料
