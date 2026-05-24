"""MarkItDown EZ — Flask 後端（唯一 Python 入口）"""
import os
import signal
import sys
import tempfile
import threading
import time

from flask import Flask, jsonify, render_template, request
from markitdown import MarkItDown

app = Flask(__name__)

_converter = MarkItDown()

# ---------- 支援格式定義 ----------

MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
app.config["MAX_CONTENT_LENGTH"] = MAX_SIZE_BYTES  # Flask 上傳限制

# ---------- Watchdog 設定 ----------

# 啟動寬限期：page_closed 模式啟動後此秒數內不偵測，給瀏覽器開啟與首次 ping 留時間。
WATCHDOG_GRACE_SECONDS = 60
# 每 N 秒輪詢一次。
WATCHDOG_POLL_SECONDS = 10
# timeout 模式中，上次 ping 距今超過此秒數視為心跳已停。
WATCHDOG_TIMEOUT_SECONDS = 30

WATCHDOG_MODE_PAGE_CLOSED = "page_closed"
WATCHDOG_MODE_TIMEOUT = "timeout"
WATCHDOG_DEFAULT_MODE = WATCHDOG_MODE_PAGE_CLOSED
WATCHDOG_ENV_VAR = "MARKITDOWN_WATCHDOG_MODE"

SUPPORTED_FORMATS = {
    ".pdf": "PDF",
    ".docx": "Word (.docx)",
    ".pptx": "PowerPoint (.pptx)",
    ".xlsx": "Excel (.xlsx)",
    ".xls": "Excel (.xls)",
    ".html": "HTML",
    ".htm": "HTML",
    ".csv": "CSV",
    ".json": "JSON",
    ".xml": "XML",
    ".epub": "EPUB",
    ".zip": "ZIP",
}


# ---------- 路由 ----------


@app.route("/")
def index():
    """返回前端頁面。"""
    return render_template("index.html")


@app.route("/health")
def health():
    """健康檢查。"""
    return jsonify({"status": "ok"})


@app.route("/formats")
def formats():
    """回傳支援的格式清單。"""
    # 去重：.html 與 .htm 歸為同一格式
    unique = {}
    for ext, label in SUPPORTED_FORMATS.items():
        if label not in unique:
            unique[label] = []
        unique[label].append(ext)

    format_list = [
        {"label": label, "extensions": exts}
        for label, exts in unique.items()
    ]
    return jsonify({"formats": format_list, "max_size_bytes": MAX_SIZE_BYTES})


@app.route("/convert", methods=["POST"])
def convert():
    """接收上傳檔案，呼叫 markitdown 轉換後回傳 Markdown。"""
    if "file" not in request.files:
        return jsonify({"error": "未提供檔案，請在 'file' 欄位上傳。"}), 400

    uploaded = request.files["file"]
    if uploaded.filename == "" or uploaded.filename is None:
        return jsonify({"error": "檔案名稱為空。"}), 400

    original_name = uploaded.filename
    _, ext = os.path.splitext(original_name)
    ext_lower = ext.lower()

    if ext_lower not in SUPPORTED_FORMATS:
        return jsonify({
            "error": f"不支援的格式：{ext}",
            "supported": list(SUPPORTED_FORMATS.keys()),
        }), 415

    # 寫入暫存檔（保留副檔名，讓 markitdown/magika 正確辨識）
    tmp_path = None  # 提前初始化，確保 finally 無論如何都能清理
    try:
        with tempfile.NamedTemporaryFile(
            suffix=ext_lower, delete=False
        ) as tmp:
            tmp_path = tmp.name          # 先記下路徑，再 save；
            uploaded.save(tmp)           # 若 save 拋例外，tmp_path 仍可在 finally 清理

        result = _converter.convert(tmp_path)
        # text_content 可能為 None（markitdown 無法解析但不拋例外的情況）
        md_content = result.text_content or ""

        # 產出檔名：原檔名去掉原副檔名 + .md
        base_name = os.path.splitext(original_name)[0]
        md_filename = f"{base_name}.md"

        return jsonify({
            "markdown": md_content,
            "filename": md_filename,
        })

    except Exception as e:
        return jsonify({"error": f"轉換失敗：{str(e)}"}), 500

    finally:
        # 清理暫存檔（tmp_path 為 None 代表 NamedTemporaryFile 本身失敗，跳過清理）
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.errorhandler(413)
def too_large(e):
    """檔案超過大小限制。"""
    return jsonify({
        "error": f"檔案大小超過限制（上限 {MAX_SIZE_BYTES // 1024 // 1024} MB）。",
    }), 413


# ---------- Graceful Shutdown ----------

# None 表示「服務啟動以來從未收到任何 /heartbeat」。page_closed 模式只用它判斷
# 「網頁從未開啟」；timeout 模式遇到 None 時應 skip，避免 None - float。
_last_heartbeat = None
# 服務啟動時間，由 start_watchdog 設定；用於 page_closed 模式的寬限期判斷。
_service_start_ts = None


@app.route("/shutdown", methods=["POST"])
def shutdown():
    """前端 beforeunload 呼叫此端點，延遲退出。"""
    def _exit():
        os.kill(os.getpid(), signal.SIGTERM)

    threading.Timer(1.0, _exit).start()
    return jsonify({"status": "shutting_down"})


@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    """前端定期 ping，重設心跳計時。"""
    global _last_heartbeat
    _last_heartbeat = time.time()
    return jsonify({"status": "ok"})


# ---------- Watchdog 判斷邏輯（pure helper，可單元測試）----------


def _should_exit_page_closed(now, start_ts, last_heartbeat):
    """page_closed 模式單輪判斷：True 表示應退出。

    - 啟動寬限期內（now - start_ts < WATCHDOG_GRACE_SECONDS）一律不退，
      避免使用者啟動服務但瀏覽器尚未送出第一次 ping 就被誤關。
    - 寬限期過後若 last_heartbeat 仍為 None → 視同網頁從未開啟＝已關閉。
    - 只要曾收到 heartbeat，就不因 heartbeat stale 退出；瀏覽器背景節流或
      系統睡眠可能延後前端 timer，不能代表頁面已關閉。
    """
    if now - start_ts < WATCHDOG_GRACE_SECONDS:
        return False
    return last_heartbeat is None


def _should_exit_timeout(now, last_heartbeat):
    """timeout 模式單輪判斷：True 表示應退出。

    向下相容語意：last_heartbeat 為 None 時不退出（重構後初值為 None，
    舊版本則被 __main__ 立即覆寫為 time.time()，行為等價）。
    """
    if last_heartbeat is None:
        return False
    return (now - last_heartbeat) > WATCHDOG_TIMEOUT_SECONDS


def _exit_due_to(reason):
    print(f"MarkItDown EZ：{reason}，自動退出。")
    os.kill(os.getpid(), signal.SIGTERM)


def _run_page_closed_watchdog():
    """page_closed 模式 loop：寬限期後只偵測網頁從未開啟。"""
    while True:
        time.sleep(WATCHDOG_POLL_SECONDS)
        if _should_exit_page_closed(time.time(), _service_start_ts, _last_heartbeat):
            _exit_due_to("偵測到網頁未開啟")
            return


def _run_timeout_watchdog():
    """timeout 模式 loop：維持舊版「距上次 ping 超過 30 秒即關」行為。"""
    while True:
        time.sleep(WATCHDOG_POLL_SECONDS)
        if _should_exit_timeout(time.time(), _last_heartbeat):
            _exit_due_to("前端已關閉")
            return


def start_watchdog(mode):
    """依模式啟動 watchdog daemon thread；回傳 (thread, normalized_mode)。

    未知 mode 印 warning 並 fallback 至 page_closed。設定 _service_start_ts。
    """
    global _service_start_ts
    normalized = (mode or "").strip().lower()
    if normalized == WATCHDOG_MODE_PAGE_CLOSED:
        target = _run_page_closed_watchdog
    elif normalized == WATCHDOG_MODE_TIMEOUT:
        target = _run_timeout_watchdog
    else:
        print(
            f"MarkItDown EZ：未知 watchdog 模式 '{mode}'，fallback 至 "
            f"{WATCHDOG_DEFAULT_MODE}。",
            file=sys.stderr,
        )
        normalized = WATCHDOG_DEFAULT_MODE
        target = _run_page_closed_watchdog

    _service_start_ts = time.time()
    print(f"MarkItDown EZ：watchdog 模式 = {normalized}")
    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return thread, normalized


# ---------- 主入口 ----------

if __name__ == "__main__":
    import socket
    import webbrowser

    # 自動選擇空閒 port
    # 加上 SO_REUSEADDR，讓 Flask 能 bind 到相同 port
    # 縮短 close → re-bind 的 race condition 視窗
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    url = f"http://127.0.0.1:{port}"

    def open_browser():
        webbrowser.open(url)

    # 延遲開啟瀏覽器，讓 Flask 有時間啟動
    threading.Timer(1.5, open_browser).start()

    mode = os.environ.get(WATCHDOG_ENV_VAR, WATCHDOG_DEFAULT_MODE)
    start_watchdog(mode)

    print(f"MarkItDown EZ 啟動於 {url}")
    app.run(host="127.0.0.1", port=port, debug=False)
