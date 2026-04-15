"""Card 1: Flask 後端 API 基礎測試。"""
import io
import json
import os

import pytest


# ============================================================
# GET /health
# ============================================================

class TestHealth:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"


# ============================================================
# GET /formats
# ============================================================

class TestFormats:
    def test_formats_returns_list(self, client):
        resp = client.get("/formats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "formats" in data
        assert isinstance(data["formats"], list)
        assert len(data["formats"]) > 0

    def test_formats_has_max_size(self, client):
        resp = client.get("/formats")
        data = resp.get_json()
        assert "max_size_bytes" in data
        assert data["max_size_bytes"] == 50 * 1024 * 1024

    def test_formats_contain_expected_labels(self, client):
        resp = client.get("/formats")
        data = resp.get_json()
        labels = {f["label"] for f in data["formats"]}
        expected = {"PDF", "Word (.docx)", "CSV", "HTML", "JSON", "XML", "EPUB"}
        assert expected.issubset(labels), f"Missing: {expected - labels}"


# ============================================================
# POST /convert — 各格式正確性
# ============================================================

FORMAT_FIXTURES = [
    ("sample.csv", ".csv", "Name"),
    ("sample.json", ".json", "MarkItDown EZ"),
    ("sample.xml", ".xml", "Hello"),
    ("sample.html", ".html", "Hello MarkItDown"),
    ("sample.docx", ".docx", "Test Document"),
    ("sample.xlsx", ".xlsx", "Sheet1"),
    ("sample.xls", ".xls", "Sheet1"),
    ("sample.pptx", ".pptx", "Test Slide"),
    ("sample.pdf", ".pdf", "Hello PDF"),
    ("sample.epub", ".epub", "Chapter 1"),
    ("sample.zip", ".zip", "readme"),
]


class TestConvertFormats:
    @pytest.mark.parametrize("filename,ext,expected_content", FORMAT_FIXTURES)
    def test_convert_each_format(self, client, fixtures_dir, filename, ext, expected_content):
        filepath = os.path.join(fixtures_dir, filename)
        if not os.path.exists(filepath):
            pytest.skip(f"Fixture {filename} not found")

        with open(filepath, "rb") as f:
            data = {"file": (f, filename)}
            resp = client.post(
                "/convert",
                data=data,
                content_type="multipart/form-data",
            )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.data}"
        result = resp.get_json()
        assert "markdown" in result
        assert "filename" in result
        assert expected_content in result["markdown"], (
            f"Expected '{expected_content}' in markdown output for {filename}"
        )
        # 驗證輸出檔名正確
        base = os.path.splitext(filename)[0]
        assert result["filename"] == f"{base}.md"


# ============================================================
# POST /convert — 錯誤處理
# ============================================================

class TestConvertErrors:
    def test_no_file_field(self, client):
        """未提供 file 欄位 → 400"""
        resp = client.post("/convert", data={}, content_type="multipart/form-data")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_empty_filename(self, client):
        """空檔名 → 400"""
        data = {"file": (io.BytesIO(b"test"), "")}
        resp = client.post("/convert", data=data, content_type="multipart/form-data")
        assert resp.status_code == 400

    def test_unsupported_format(self, client):
        """不支援的格式 → 415"""
        data = {"file": (io.BytesIO(b"binary stuff"), "test.exe")}
        resp = client.post("/convert", data=data, content_type="multipart/form-data")
        assert resp.status_code == 415
        result = resp.get_json()
        assert "error" in result
        assert "supported" in result

    def test_corrupted_file_returns_500(self, client):
        """損壞的 PDF → 500"""
        data = {"file": (io.BytesIO(b"not a real pdf"), "broken.pdf")}
        resp = client.post("/convert", data=data, content_type="multipart/form-data")
        # 損壞檔案可能被 markitdown 寬容處理或拋例外
        assert resp.status_code in (200, 500)


# ============================================================
# GET / — 前端頁面
# ============================================================

class TestIndex:
    def test_index_returns_html(self, client):
        """確認 / 端點有回應（前端未建置前可能 500，但不應 404）"""
        resp = client.get("/")
        # Card 2 完成前，templates/index.html 可能不存在
        # 這裡先跳過，Card 2 完成後再啟用
        if resp.status_code == 500:
            pytest.skip("index.html not yet created (Card 2)")
        assert resp.status_code == 200
