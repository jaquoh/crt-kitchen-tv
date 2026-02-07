import os
import yaml
from flask import Flask, request, jsonify, render_template, redirect

CONFIG_PATH = os.environ.get("CRT_CONFIG", "/etc/crt-kitchen-tv/config.yaml")


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
    if cfg.get("audio_output") not in {"respeaker", "hdmi", "analog"}:
        errors.append("audio_output must be respeaker|hdmi|analog")
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


def create_app():
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template("index.html", cfg=load_config())

    @app.route("/api/config", methods=["GET", "POST"])
    def api_config():
        if request.method == "GET":
            return jsonify(load_config())
        payload = request.get_json(silent=True) or request.form.to_dict(flat=False)
        # normalize form lists
        if isinstance(payload, dict):
            if "news_streams" in payload and not isinstance(payload["news_streams"], list):
                payload["news_streams"] = [payload["news_streams"]]
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

        payload["leds_enabled"] = raw.get("leds_enabled", ["off"])[0] == "on"
        errors = validate(payload)
        if errors:
            return render_template("index.html", cfg=load_config(), errors=errors), 400
        cfg = load_config()
        cfg.update(payload)
        save_config(cfg)
        return redirect("/")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=True)
