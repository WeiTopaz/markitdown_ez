"""MarkItDown EZ — Flask 後端（唯一 Python 入口）"""
import os
import signal
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

_last_heartbeat = None  # 由 __main__ 初始化


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


# ---------- 主入口 ----------

if __name__ == "__main__":
    import socket
    import sys
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

    # 心跳監控（方案 B）：若超過 30s 未收到前端 ping，自動退出
    _last_heartbeat = time.time()

    def heartbeat_watchdog():
        while True:
            time.sleep(10)
            if time.time() - _last_heartbeat > 30:
                print("MarkItDown EZ：前端已關閉，自動退出。")
                os.kill(os.getpid(), signal.SIGTERM)

    watchdog = threading.Thread(target=heartbeat_watchdog, daemon=True)
    watchdog.start()

    print(f"MarkItDown EZ 啟動於 {url}")
    app.run(host="127.0.0.1", port=port, debug=False)
