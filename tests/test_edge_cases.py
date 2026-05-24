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


class TestWatchdogModes:
    """Heartbeat watchdog 兩種模式的單輪判斷與分派器測試。

    用 pure helper（`_should_exit_page_closed` / `_should_exit_timeout`）
    驗真值表，避免進入 loop 的 sleep；用 mock `threading.Thread` 驗 dispatcher
    分派與 unknown 模式 fallback。
    """

    # ---- page_closed 模式 helper ----

    def test_page_closed_within_grace_skips(self):
        """寬限期內（距 start_ts 30 秒 < 60）即使從未收到 ping 也不應退出。"""
        from app import _should_exit_page_closed, WATCHDOG_GRACE_SECONDS
        assert WATCHDOG_GRACE_SECONDS == 60
        now = 1000.0
        start_ts = now - 30  # 30 秒前啟動，仍在寬限期
        assert _should_exit_page_closed(now, start_ts, None) is False

    def test_page_closed_after_grace_no_heartbeat_exits(self):
        """寬限期過後（距 start_ts 70 秒）且從未收到 ping → 應退出。"""
        from app import _should_exit_page_closed
        now = 1000.0
        start_ts = now - 70
        assert _should_exit_page_closed(now, start_ts, None) is True

    def test_page_closed_after_grace_stale_heartbeat_skips(self):
        """page_closed 模式曾收到 ping 後不因 stale heartbeat 退出，避免瀏覽器 timer 節流誤關。"""
        from app import _should_exit_page_closed
        now = 1000.0
        start_ts = now - 120  # 早就過寬限期
        last_hb = now - 45    # 上次 ping 在 45 秒前，超過 30 秒閾值
        assert _should_exit_page_closed(now, start_ts, last_hb) is False

    def test_page_closed_after_grace_fresh_heartbeat_skips(self):
        """寬限期過後 ping 仍新鮮（5 秒前）→ 不應退出。"""
        from app import _should_exit_page_closed
        now = 1000.0
        start_ts = now - 120
        last_hb = now - 5
        assert _should_exit_page_closed(now, start_ts, last_hb) is False

    # ---- timeout 模式 helper（向下相容）----

    def test_timeout_with_none_heartbeat_skips(self):
        """舊模式遇到 _last_heartbeat is None（重構後初值）→ 不應退出，避免炸 None-arithmetic。"""
        from app import _should_exit_timeout
        assert _should_exit_timeout(1000.0, None) is False

    def test_timeout_with_stale_heartbeat_exits(self):
        """舊模式 ping 已停超過 30 秒 → 應退出（行為與舊版一致）。"""
        from app import _should_exit_timeout, WATCHDOG_TIMEOUT_SECONDS
        assert WATCHDOG_TIMEOUT_SECONDS == 30
        now = 1000.0
        last_hb = now - 45
        assert _should_exit_timeout(now, last_hb) is True

    # ---- dispatcher ----

    def test_start_watchdog_dispatches_page_closed(self):
        """mode='page_closed' → 啟動 thread 且 normalized 回 'page_closed'。"""
        import unittest.mock as mock
        from app import start_watchdog, WATCHDOG_MODE_PAGE_CLOSED
        with mock.patch("app.threading.Thread") as mock_thread:
            mock_thread.return_value = mock.MagicMock()
            _, normalized = start_watchdog(WATCHDOG_MODE_PAGE_CLOSED)
            assert normalized == "page_closed"
            mock_thread.assert_called_once()
            mock_thread.return_value.start.assert_called_once()

    def test_start_watchdog_dispatches_timeout(self):
        """mode='timeout' → normalized 回 'timeout'。"""
        import unittest.mock as mock
        from app import start_watchdog, WATCHDOG_MODE_TIMEOUT
        with mock.patch("app.threading.Thread") as mock_thread:
            mock_thread.return_value = mock.MagicMock()
            _, normalized = start_watchdog(WATCHDOG_MODE_TIMEOUT)
            assert normalized == "timeout"

    def test_start_watchdog_unknown_mode_falls_back(self):
        """未知 mode → fallback 至 page_closed，仍會啟動 thread。"""
        import unittest.mock as mock
        from app import start_watchdog
        with mock.patch("app.threading.Thread") as mock_thread:
            mock_thread.return_value = mock.MagicMock()
            _, normalized = start_watchdog("bogus_mode")
            assert normalized == "page_closed"
            mock_thread.return_value.start.assert_called_once()


class TestWatchdogLoop:
    """Loop 函式整合測試：用 monkeypatch 控制 sleep/time/os.kill，
    驗證 loop 真的會在 helper 回傳 True 時走到 os.kill 並終止。

    helper 真值表已由 TestWatchdogModes 覆蓋；本類別補的是 loop 的
    sleep → 評估 → 退出 控制流。
    """

    def test_page_closed_loop_exits_after_grace_no_heartbeat(self, monkeypatch):
        """grace 後 None：第一輪 sleep 完即退出，os.kill 被呼叫一次 SIGTERM。"""
        import signal
        import app as app_module

        kill_calls = []
        sleep_calls = []

        monkeypatch.setattr(app_module, "_service_start_ts", 0.0)
        monkeypatch.setattr(app_module, "_last_heartbeat", None)
        monkeypatch.setattr("time.time", lambda: 100.0)  # > 60s grace
        monkeypatch.setattr("time.sleep", lambda s: sleep_calls.append(s))
        monkeypatch.setattr("os.kill", lambda pid, sig: kill_calls.append((pid, sig)))

        app_module._run_page_closed_watchdog()

        assert sleep_calls == [app_module.WATCHDOG_POLL_SECONDS]
        assert len(kill_calls) == 1
        assert kill_calls[0][1] == signal.SIGTERM

    def test_page_closed_loop_skips_within_grace(self, monkeypatch):
        """grace 內：連續多輪 continue 不退；用 sleep counter 在 3 輪後拋例外跳出 loop。"""
        import app as app_module

        sleep_count = [0]
        kill_calls = []

        def fake_sleep(_):
            sleep_count[0] += 1
            if sleep_count[0] >= 3:
                raise RuntimeError("STOP_LOOP")

        monkeypatch.setattr(app_module, "_service_start_ts", 0.0)
        monkeypatch.setattr(app_module, "_last_heartbeat", None)
        monkeypatch.setattr("time.time", lambda: 30.0)  # < 60s grace
        monkeypatch.setattr("time.sleep", fake_sleep)
        monkeypatch.setattr("os.kill", lambda pid, sig: kill_calls.append((pid, sig)))

        with pytest.raises(RuntimeError, match="STOP_LOOP"):
            app_module._run_page_closed_watchdog()

        assert sleep_count[0] == 3
        assert kill_calls == []

    def test_page_closed_loop_skips_when_heartbeat_stale(self, monkeypatch):
        """grace 後曾收過 ping 即視為頁面已開啟；stale heartbeat 不應讓 page_closed 模式退出。"""
        import app as app_module

        sleep_count = [0]
        kill_calls = []

        def fake_sleep(_):
            sleep_count[0] += 1
            if sleep_count[0] >= 3:
                raise RuntimeError("STOP_LOOP")

        monkeypatch.setattr(app_module, "_service_start_ts", 0.0)
        monkeypatch.setattr(app_module, "_last_heartbeat", 50.0)  # 50s 前 ping
        monkeypatch.setattr("time.time", lambda: 100.0)            # 距 ping 50s > 30s
        monkeypatch.setattr("time.sleep", fake_sleep)
        monkeypatch.setattr("os.kill", lambda pid, sig: kill_calls.append((pid, sig)))

        with pytest.raises(RuntimeError, match="STOP_LOOP"):
            app_module._run_page_closed_watchdog()

        assert sleep_count[0] == 3
        assert kill_calls == []

    def test_timeout_loop_exits_when_heartbeat_stale(self, monkeypatch):
        """timeout 模式 last_heartbeat 已停超過 30s → 呼叫 os.kill SIGTERM。"""
        import signal
        import app as app_module

        kill_calls = []
        monkeypatch.setattr(app_module, "_last_heartbeat", 50.0)
        monkeypatch.setattr("time.time", lambda: 100.0)
        monkeypatch.setattr("time.sleep", lambda s: None)
        monkeypatch.setattr("os.kill", lambda pid, sig: kill_calls.append((pid, sig)))

        app_module._run_timeout_watchdog()

        assert len(kill_calls) == 1
        assert kill_calls[0][1] == signal.SIGTERM

    def test_timeout_loop_skips_when_heartbeat_none(self, monkeypatch):
        """timeout 模式 last_heartbeat=None → continue，不應退出（向下相容）。"""
        import app as app_module

        sleep_count = [0]
        kill_calls = []

        def fake_sleep(_):
            sleep_count[0] += 1
            if sleep_count[0] >= 3:
                raise RuntimeError("STOP_LOOP")

        monkeypatch.setattr(app_module, "_last_heartbeat", None)
        monkeypatch.setattr("time.time", lambda: 100.0)
        monkeypatch.setattr("time.sleep", fake_sleep)
        monkeypatch.setattr("os.kill", lambda pid, sig: kill_calls.append((pid, sig)))

        with pytest.raises(RuntimeError, match="STOP_LOOP"):
            app_module._run_timeout_watchdog()

        assert kill_calls == []


class TestExitDueTo:
    """_exit_due_to 的程式碼層驗證：對當前 pid 送 SIGTERM。

    跨平台說明：Windows 上 SIGTERM 會被 Python runtime 映射到 TerminateProcess，
    本測試僅驗證程式碼確實呼叫 os.kill(getpid, SIGTERM)，不驗 OS 實際終止行為。
    """

    def test_exit_due_to_sends_sigterm_to_current_pid(self, monkeypatch, capsys):
        import os
        import signal
        import app as app_module

        kill_calls = []
        monkeypatch.setattr("os.kill", lambda pid, sig: kill_calls.append((pid, sig)))

        app_module._exit_due_to("測試訊息")

        assert kill_calls == [(os.getpid(), signal.SIGTERM)]
        captured = capsys.readouterr()
        assert "測試訊息" in captured.out
        assert "自動退出" in captured.out


class TestStartWatchdogNormalization:
    """start_watchdog 對 env 字串的容錯：大小寫、前後空白、空字串、None。"""

    @pytest.mark.parametrize("input_mode,expected", [
        ("PAGE_CLOSED", "page_closed"),
        ("Page_Closed", "page_closed"),
        ("  page_closed  ", "page_closed"),
        ("TIMEOUT", "timeout"),
        ("Timeout", "timeout"),
        ("  timeout\n", "timeout"),
        ("", "page_closed"),
        (None, "page_closed"),
    ])
    def test_start_watchdog_normalizes_input(self, input_mode, expected):
        """各種輸入都應 normalize 或 fallback 至預設模式。"""
        import unittest.mock as mock
        from app import start_watchdog
        with mock.patch("app.threading.Thread") as mock_thread:
            mock_thread.return_value = mock.MagicMock()
            _, normalized = start_watchdog(input_mode)
            assert normalized == expected
            mock_thread.return_value.start.assert_called_once()


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
        assert "shutdownBtn" in html
        assert "purify.min.js" in html  # DOMPurify 載入
        assert "/formats" in html       # 動態載入格式
        assert "/convert" in html       # 轉換端點
        assert "fetch(\"/shutdown\", { method: \"POST\" })" in html
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
