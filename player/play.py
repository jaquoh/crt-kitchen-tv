import os
import subprocess
import time
from ui.hw import audio


MPV_BIN = "mpv"


def play_media(source, config):
    audio_output = config.get("audio_output", "respeaker") if config else "respeaker"
    backend_pref = (config.get("mpv_backend", "drm") if config else "drm").lower()
    audio_args = audio.build_mpv_args(audio_output)
    base = [MPV_BIN, "--quiet", "--fs", "--no-terminal", "--ontop"]

    has_display = bool(os.environ.get("DISPLAY"))
    plans = []
    if backend_pref == "x11":
        if has_display:
            plans.append(("x11", ["--vo=gpu", "--gpu-context=x11"], False))
        plans.append(("drm", ["--vo=drm"], True))
        plans.append(("auto", [], True))
    elif backend_pref == "auto":
        plans.append(("drm", ["--vo=drm"], True))
        if has_display:
            plans.append(("x11", ["--vo=gpu", "--gpu-context=x11"], False))
        plans.append(("auto", [], False))
    else:
        # Default for CRT appliances: force non-X11 first.
        plans.append(("drm", ["--vo=drm"], True))
        plans.append(("auto", [], True))
        if has_display:
            plans.append(("x11", ["--vo=gpu", "--gpu-context=x11"], False))

    errors = []
    for backend_name, backend_args, force_console_env in plans:
        args = base + backend_args + audio_args + [source]
        start_ts = time.time()
        env = os.environ.copy()
        if force_console_env:
            env.pop("DISPLAY", None)
            env.pop("WAYLAND_DISPLAY", None)
        try:
            result = subprocess.run(
                args,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
        except FileNotFoundError:
            return False, "mpv is not installed or not in PATH", None
        elapsed = time.time() - start_ts
        if result.returncode == 0 and elapsed >= 1.0:
            return True, None, f"{backend_name} ({elapsed:.1f}s)"
        err_line = (result.stderr or "").strip().splitlines()
        err_text = err_line[-1] if err_line else f"mpv exited with code {result.returncode}"
        if result.returncode == 0 and elapsed < 1.0:
            err_text = f"mpv exited too quickly ({elapsed:.1f}s)"
        errors.append(f"{backend_name}: {err_text}")
    return False, errors[-1] if errors else "Unable to start mpv", None
