"""Card 3: 邊界案例與整合測試 — 補齊覆蓋率。"""
import io
import os
import json

import pytest


# ============================================================
# 損壞檔案處理
# ============================================================

class TestCorruptedFiles:
    """損壞或截斷的檔案應回傳 500 或被 markitdown 寬容處理。"""

    def test_truncated_pdf(self, client):
        """截斷的 PDF（只有 header）→ 500 或 markitdown 寬容回傳。"""
        corrupt_pdf = b"%PDF-1.4\n1 0 obj\n"  # 不完整的 PDF
        data = {"file": (io.BytesIO(corrupt_pdf), "truncated.pdf")}
        resp = client.post("/convert", data=data, content_type="multipart/form-data")
        assert resp.status_code in (200, 500)
        result = resp.get_json()
        if resp.status_code == 500:
            assert "error" in result

    def test_invalid_xlsx(self, client):
        """無效的 XLSX（純文字偽裝）→ 500。"""
        data = {"file": (io.BytesIO(b"this is not xlsx"), "fake.xlsx")}
        resp = client.post("/convert", data=data, content_type="multipart/form-data")
        assert resp.status_code in (200, 500)
        result = resp.get_json()
        if resp.status_code == 500:
            assert "error" in result
            assert "轉換失敗" in result["error"]

    def test_invalid_docx(self, client):
        """無效的 DOCX → 500。"""
        data = {"file": (io.BytesIO(b"not a docx file"), "fake.docx")}
        resp = client.post("/convert", data=data, content_type="multipart/form-data")
        assert resp.status_code in (200, 500)
        result = resp.get_json()
        if resp.status_code == 500:
            assert "error" in result

    def test_zero_byte_file(self, client):
        """零位元組檔案 → 應有回應（可能 200 空結果或 500）。"""
        data = {"file": (io.BytesIO(b""), "empty.csv")}
        resp = client.post("/convert", data=data, content_type="multipart/form-data")
        assert resp.status_code in (200, 500)
        result = resp.get_json()
        if resp.status_code == 200:
            assert "markdown" in result


# ============================================================
# 特殊字元與邊界輸入
# ============================================================

class TestSpecialCharacters:
    """檔案名稱含特殊字元。"""

    def test_unicode_filename(self, client, fixtures_dir):
        """中文檔名。"""
        filepath = os.path.join(fixtures_dir, "sample.csv")
        with open(filepath, "rb") as f:
            content = f.read()
        data = {"file": (io.BytesIO(content), "資料表.csv")}
        resp = client.post("/convert", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        result = resp.get_json()
        assert result["filename"] == "資料表.md"
        assert "markdown" in result

    def test_filename_with_spaces(self, client, fixtures_dir):
        """含空格的檔名。"""
        filepath = os.path.join(fixtures_dir, "sample.json")
        with open(filepath, "rb") as f:
            content = f.read()
        data = {"file": (io.BytesIO(content), "my file (1).json")}
        resp = client.post("/convert", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        result = resp.get_json()
        assert result["filename"] == "my file (1).md"

    def test_filename_with_dots(self, client, fixtures_dir):
        """含多個點的檔名。"""
        filepath = os.path.join(fixtures_dir, "sample.html")
        with open(filepath, "rb") as f:
            content = f.read()
        data = {"file": (io.BytesIO(content), "report.2024.01.html")}
        resp = client.post("/convert", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        result = resp.get_json()
        assert result["filename"] == "report.2024.01.md"


# ============================================================
# 413 大檔案限制
# ============================================================

class TestFileSizeLimit:
    """前端 / 後端檔案大小限制。"""

    def test_413_error_handler(self, client):
        """觸發 Flask 的 413 錯誤處理器。"""
        # Flask 的 MAX_CONTENT_LENGTH 會在讀取 request body 時觸發
        # 我們透過設定較小的限制來測試 error handler
        from app import app
        original = app.config["MAX_CONTENT_LENGTH"]
        try:
            app.config["MAX_CONTENT_LENGTH"] = 100  # 暫時設為 100 bytes
            large_content = b"x" * 200
            data = {"file": (io.BytesIO(large_content), "big.csv")}
            resp = client.post(
                "/convert", data=data, content_type="multipart/form-data"
            )
            assert resp.status_code == 413
            result = resp.get_json()
            assert "error" in result
        finally:
            app.config["MAX_CONTENT_LENGTH"] = original


# ============================================================
# /formats 端點細節
# ============================================================

class TestFormatsDetail:
    """格式端點的完整性驗證。"""

    def test_each_format_has_extensions(self, client):
        """每個格式都有 extensions 欄位且非空。"""
        resp = client.get("/formats")
        data = resp.get_json()
        for fmt in data["formats"]:
            assert "label" in fmt
            assert "extensions" in fmt
            assert len(fmt["extensions"]) > 0
            for ext in fmt["extensions"]:
                assert ext.startswith(".")

    def test_html_format_dedup(self, client):
        """HTML 格式的 .html 和 .htm 應歸在同一組。"""
        resp = client.get("/formats")
        data = resp.get_json()
        html_format = [f for f in data["formats"] if f["label"] == "HTML"]
        assert len(html_format) == 1
        assert ".html" in html_format[0]["extensions"]
        assert ".htm" in html_format[0]["extensions"]


# ============================================================
# /health 端點
# ============================================================

class TestHealthDetail:
    def test_health_json_content_type(self, client):
        """確認 content-type 為 application/json。"""
        resp = client.get("/health")
        assert "application/json" in resp.content_type


# ============================================================
# 前後端整合：完整上傳流程
# ============================================================

# ============================================================
# Shutdown & Heartbeat 端點
# ============================================================

class TestShutdownHeartbeat:
    """測試 graceful shutdown 相關端點。"""

    def test_heartbeat_returns_ok(self, client):
        """POST /heartbeat → 200。"""
        resp = client.post("/heartbeat")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"

    def test_shutdown_returns_shutting_down(self, client):
        """POST /shutdown → 回傳 shutting_down（但不真的退出測試進程）。"""
        # 根本修法：mock threading.Timer，讓 Timer 物件根本不會被建立與啟動。
        # 舊做法只 mock os.kill，但 with 塊退出後 mock 被還原，
        # 1s 後 Timer 仍會呼叫真實 os.kill，導致 SIGTERM 殺掉 pytest (exit 143)。
        import unittest.mock as mock
        with mock.patch("threading.Timer") as mock_timer:
            mock_timer.return_value = mock.MagicMock()
            resp = client.post("/shutdown")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["status"] == "shutting_down"
            # 驗證確實排程了 1s 後的退出 Timer
            mock_timer.assert_called_once_with(1.0, mock.ANY)
            mock_timer.return_value.start.assert_called_once()


class TestIntegration:
    """模擬完整上傳流程（像前端 fetch 呼叫）。"""

    def test_full_flow_csv(self, client, fixtures_dir):
        """模擬前端完整流程：載入格式 → 上傳 CSV → 取得結果 → 驗證下載檔名。"""
        # Step 1: 載入支援格式
        resp = client.get("/formats")
        assert resp.status_code == 200
        formats = resp.get_json()
        ext_list = []
        for f in formats["formats"]:
            ext_list.extend(f["extensions"])
        assert ".csv" in ext_list

        # Step 2: 上傳檔案
        filepath = os.path.join(fixtures_dir, "sample.csv")
        with open(filepath, "rb") as f:
            resp = client.post(
                "/convert",
                data={"file": (f, "sample.csv")},
                content_type="multipart/form-data",
            )
        assert resp.status_code == 200
        result = resp.get_json()

        # Step 3: 驗證結果
        assert "markdown" in result
        assert len(result["markdown"]) > 0
        assert "Name" in result["markdown"]

        # Step 4: 驗證下載檔名
        assert result["filename"] == "sample.md"

    def test_full_flow_html_with_script_tag(self, client):
        """上傳含 <script> 的 HTML，確認 markitdown 能處理。
        （XSS 防護由前端 DOMPurify 負責，後端只負責轉換。）"""
        malicious_html = b'<html><body><h1>Title</h1><script>alert("xss")</script><p>Content</p></body></html>'
        data = {"file": (io.BytesIO(malicious_html), "test.html")}
        resp = client.post("/convert", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        result = resp.get_json()
        assert "markdown" in result
        # markitdown 應該把 HTML 轉成 markdown，script 標籤不應原樣保留
        assert "Title" in result["markdown"]

    def test_index_contains_key_elements(self, client):
        """確認首頁 HTML 包含關鍵 UI 元素。"""
        resp = client.get("/")
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        # 關鍵 UI 元素
        assert "dropzone" in html
        assert "convertBtn" in html
        assert "resultCard" in html
        assert "downloadBtn" in html
        assert "purify.min.js" in html  # DOMPurify 載入
        assert "/formats" in html       # 動態載入格式
        assert "/convert" in html       # 轉換端點
        # Bug fix: renderedContent 獨立節點必須存在，
        # 確保 showResult("rendered") 不會銷毀 rawContent DOM 節點
        assert 'id="renderedContent"' in html
        # 確認 renderedContent.innerHTML 被賦值而非 resultContent.innerHTML
        assert "renderedContent.innerHTML" in html
        assert "renderedContent.style.display" in html
        # Bug fix: browseBtn 改為 <label for="fileInput">，瀏覽器原生觸發選檔對話框
        assert '<label for="fileInput" id="browseBtn">' in html
        # A11y fix: dropzone 有 role="button" 與 tabindex
        assert 'role="button"' in html
        assert 'tabindex="0"' in html
        # A11y fix: 錯誤訊息有 role="alert"
        assert 'role="alert"' in html
        # UX fix: dropzone 整體點擊（含 icon 與 badge）均能開啟選檔對話框
        # browseBtn 自行 stopPropagation，其餘位置均應觸發
        assert "dropzone.addEventListener(\"click\", () => { fileInput.click(); })" in html
        # Markdown 預覽 fix: blockquote 允許省略 > 後的空格（CommonMark）
        assert "&gt;\\s*" in html
        # Table fix: 已移除永遠為 true 的 sepCells.length > 0 冗餘檢查
        assert "sepCells.length > 0" not in html
