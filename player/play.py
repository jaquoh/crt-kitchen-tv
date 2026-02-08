import os
import subprocess
import time
from ui.hw import audio


MPV_BIN = "mpv"


def play_media(source, config):
    audio_output = config.get("audio_output", "respeaker") if config else "respeaker"
    audio_args = audio.build_mpv_args(audio_output)
    base = [MPV_BIN, "--quiet", "--fs", "--no-terminal", "--ontop"]
    backends = []
    if os.environ.get("DISPLAY"):
        backends.append(["--vo=gpu", "--gpu-context=x11"])
    backends.append(["--vo=drm"])
    backends.append([])

    errors = []
    for backend_args in backends:
        args = base + backend_args + audio_args + [source]
        start_ts = time.time()
        try:
            result = subprocess.run(
                args,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
        except FileNotFoundError:
            return False, "mpv is not installed or not in PATH"
        elapsed = time.time() - start_ts
        if result.returncode == 0 and elapsed >= 1.0:
            return True, None
        backend_name = "x11" if "--gpu-context=x11" in backend_args else ("drm" if "--vo=drm" in backend_args else "auto")
        err_line = (result.stderr or "").strip().splitlines()
        err_text = err_line[-1] if err_line else f"mpv exited with code {result.returncode}"
        if result.returncode == 0 and elapsed < 1.0:
            err_text = f"mpv exited too quickly ({elapsed:.1f}s)"
        errors.append(f"{backend_name}: {err_text}")
    return False, errors[-1] if errors else "Unable to start mpv"
