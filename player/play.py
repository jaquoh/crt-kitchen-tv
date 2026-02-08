import os
import subprocess
import time
from ui.hw import audio


MPV_BIN = "mpv"
MPV_DEBUG_LOG = "/tmp/crt-kitchen-tv-mpv.log"


def _log(message):
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(MPV_DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {message}\n")
    except Exception:
        pass


def play_media(source, config):
    audio_output = config.get("audio_output", "respeaker") if config else "respeaker"
    backend_pref = (config.get("mpv_backend", "drm") if config else "drm").lower()
    audio_args = audio.build_mpv_args(audio_output)
    base = [MPV_BIN, "--quiet", "--fs", "--no-terminal", "--ontop"]

    has_display = bool(os.environ.get("DISPLAY"))
    plans = []
    if backend_pref == "x11" and not has_display:
        _log("x11 requested but DISPLAY is not set")
        return False, "x11 backend selected but no X11 session (DISPLAY missing)", None

    if backend_pref == "x11":
        if has_display:
            plans.append(("x11", ["--vo=gpu", "--gpu-context=x11"], False))
        plans.append(("drm", ["--vo=drm"], True))
        plans.append(("auto", [], True))
    elif backend_pref == "sdl":
        plans.append(("sdl", ["--vo=sdl"], True))
        plans.append(("drm", ["--vo=drm"], True))
        plans.append(("auto", [], True))
    elif backend_pref == "auto":
        plans.append(("sdl", ["--vo=sdl"], True))
        plans.append(("drm", ["--vo=drm"], True))
        if has_display:
            plans.append(("x11", ["--vo=gpu", "--gpu-context=x11"], False))
        plans.append(("auto", [], False))
    else:
        # Default for CRT appliances: force non-X11 first.
        plans.append(("sdl", ["--vo=sdl"], True))
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
            _log(f"attempt backend={backend_name} source={source} args={' '.join(args)}")
            result = subprocess.run(
                args,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
        except FileNotFoundError:
            _log("mpv executable not found")
            return False, "mpv is not installed or not in PATH", None
        elapsed = time.time() - start_ts
        stderr_text = (result.stderr or "").strip()
        stdout_text = (result.stdout or "").strip()
        if stderr_text:
            _log(f"{backend_name} stderr: {stderr_text.splitlines()[-1]}")
        if stdout_text:
            _log(f"{backend_name} stdout: {stdout_text.splitlines()[-1]}")
        if result.returncode == 0 and elapsed >= 1.0:
            _log(f"success backend={backend_name} elapsed={elapsed:.1f}s")
            return True, None, f"{backend_name} ({elapsed:.1f}s)"
        err_line = (result.stderr or "").strip().splitlines()
        err_text = err_line[-1] if err_line else f"mpv exited with code {result.returncode}"
        if result.returncode == 0 and elapsed < 1.0:
            err_text = f"mpv exited too quickly ({elapsed:.1f}s)"
        errors.append(f"{backend_name}: {err_text}")
        _log(f"failed backend={backend_name} err={err_text}")
    return False, errors[-1] if errors else "Unable to start mpv", None
