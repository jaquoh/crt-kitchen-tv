import os
import subprocess
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
        if result.returncode == 0:
            return True, None
        err_line = (result.stderr or "").strip().splitlines()
        errors.append(err_line[-1] if err_line else f"mpv exited with code {result.returncode}")
    return False, errors[-1] if errors else "Unable to start mpv"
