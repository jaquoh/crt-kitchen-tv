import os
import subprocess
import yaml
from flask import Flask, request, jsonify, render_template, redirect

CONFIG_PATH = os.environ.get("CRT_CONFIG", "/etc/crt-kitchen-tv/config.yaml")
VALID_AUDIO = {"respeaker", "hdmi", "analog"}
VALID_SORT = {"newest", "alpha"}
VALID_MPV_BACKEND = {"drm", "x11", "sdl", "auto"}
UI_DEBUG_LOG = "/tmp/crt-kitchen-tv-ui.log"
MPV_DEBUG_LOG = "/tmp/crt-kitchen-tv-mpv.log"
RESPEAKER_LOG = "/var/log/crt-kitchen-tv/respeaker-driver.log"


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def save_config(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f)


def validate(payload):
    errors = []
    cfg = load_config()
    cfg.update(payload)

    if not isinstance(cfg.get("news_streams", []), list):
        errors.append("news_streams must be a list")
    if not cfg.get("movies_dir"):
        errors.append("movies_dir is required")
    if cfg.get("audio_output") not in VALID_AUDIO:
        errors.append("audio_output must be respeaker|hdmi|analog")
    media_root = cfg.get("media_root", "")
    if not isinstance(media_root, str) or not media_root.strip():
        errors.append("media_root is required")
    collections = cfg.get("collections", [])
    if not isinstance(collections, list) or not all(isinstance(c, str) and c.strip() for c in collections):
        errors.append("collections must be a list of non-empty strings")
    if cfg.get("library_sort", "newest") not in VALID_SORT:
        errors.append("library_sort must be newest|alpha")
    if cfg.get("mpv_backend", "drm") not in VALID_MPV_BACKEND:
        errors.append("mpv_backend must be drm|x11|sdl|auto")
    overscan = cfg.get("overscan", {})
    for key in ("top", "bottom", "left", "right"):
        try:
            int(overscan.get(key, 0))
        except Exception:
            errors.append(f"overscan.{key} must be int")
    try:
        int(cfg.get("font_size", 48))
    except Exception:
        errors.append("font_size must be int")
    return errors


def normalize_payload(payload):
    if not isinstance(payload, dict):
        return {}
    norm = {}
    list_fields = {"news_streams", "collections"}
    for key, value in payload.items():
        if isinstance(value, list) and key not in list_fields and len(value) == 1:
            norm[key] = value[0]
        else:
            norm[key] = value
    if "news_streams" in norm and isinstance(norm["news_streams"], str):
        norm["news_streams"] = [v for v in norm["news_streams"].splitlines() if v.strip()]
    if "news_streams" in norm and isinstance(norm["news_streams"], list):
        lines = []
        for item in norm["news_streams"]:
            if isinstance(item, str):
                lines.extend([v for v in item.splitlines() if v.strip()])
        norm["news_streams"] = lines
    if "collections" in norm and isinstance(norm["collections"], str):
        norm["collections"] = [v for v in norm["collections"].splitlines() if v.strip()]
    if "collections" in norm and isinstance(norm["collections"], list):
        names = []
        for item in norm["collections"]:
            if isinstance(item, str):
                names.extend([v for v in item.splitlines() if v.strip()])
        norm["collections"] = names
    return norm


def read_tail(path, lines=120):
    if not os.path.exists(path):
        return f"{path}: not found"
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.readlines()
        return "".join(content[-lines:]).strip() or f"{path}: empty"
    except Exception as exc:
        return f"Failed reading {path}: {exc}"


def read_journal(unit, lines=120):
    cmd = ["journalctl", "-u", unit, "-n", str(lines), "--no-pager"]
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    except FileNotFoundError:
        return "journalctl not available"
    if result.returncode != 0:
        err = (result.stderr or "").strip()
        return f"journalctl error: {err or 'unknown'}"
    out = (result.stdout or "").strip()
    return out or "No entries"


def collect_logs(lines=120):
    return {
        "ui_debug": read_tail(UI_DEBUG_LOG, lines=lines),
        "mpv_debug": read_tail(MPV_DEBUG_LOG, lines=lines),
        "respeaker_driver": read_tail(RESPEAKER_LOG, lines=lines),
        "crt_ui_service": read_journal("crt-ui.service", lines=lines),
        "crt_web_service": read_journal("crt-web.service", lines=lines),
    }


def create_app():
    app = Flask(__name__)

    @app.route("/")
    def index():
        try:
            lines = int(request.args.get("lines", "120"))
        except ValueError:
            lines = 120
        lines = max(20, min(lines, 500))
        logs = collect_logs(lines=lines)
        return render_template("index.html", cfg=load_config(), logs=logs, lines=lines)

    @app.route("/api/logs", methods=["GET"])
    def api_logs():
        try:
            lines = int(request.args.get("lines", "120"))
        except ValueError:
            lines = 120
        lines = max(20, min(lines, 500))
        return jsonify({"lines": lines, "logs": collect_logs(lines=lines)})

    @app.route("/api/config", methods=["GET", "POST"])
    def api_config():
        if request.method == "GET":
            return jsonify(load_config())
        payload = request.get_json(silent=True) or request.form.to_dict(flat=False)
        payload = normalize_payload(payload)
        errors = validate(payload)
        if errors:
            return jsonify({"errors": errors}), 400
        cfg = load_config()
        cfg.update(payload)
        save_config(cfg)
        return jsonify({"status": "ok", "config": cfg})

    @app.route("/save", methods=["POST"])
    def save():
        raw = request.form.to_dict(flat=False)
        payload = {}
        # Flatten news streams (textarea -> newline separated)
        if "news_streams" in raw:
            payload["news_streams"] = [v for line in raw["news_streams"] for v in line.splitlines() if v]
        # Overscan fields arrive as overscan[top]
        overscan = {}
        for key, vals in raw.items():
            if key.startswith("overscan["):
                part = key[key.find("[") + 1 : key.find("]")]
                if vals:
                    overscan[part] = vals[0]
        if overscan:
            payload["overscan"] = overscan

        for k in ("movies_dir", "audio_output", "font_size"):
            if k in raw and raw[k]:
                payload[k] = raw[k][0]
        for k in ("media_root", "library_sort", "mpv_backend"):
            if k in raw and raw[k]:
                payload[k] = raw[k][0]
        if "collections" in raw:
            payload["collections"] = [v for line in raw["collections"] for v in line.splitlines() if v.strip()]

        payload["leds_enabled"] = raw.get("leds_enabled", ["off"])[0] == "on"
        errors = validate(payload)
        if errors:
            logs = collect_logs(lines=120)
            return render_template("index.html", cfg=load_config(), errors=errors, logs=logs, lines=120), 400
        cfg = load_config()
        cfg.update(payload)
        save_config(cfg)
        return redirect("/")

    return app



# WSGI entrypoint for production servers (e.g. waitress-serve server.app:app)
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
