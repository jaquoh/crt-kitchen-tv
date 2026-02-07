import os
import subprocess
from ui.hw import audio


MPV_BIN = "mpv"


def play_media(source, config):
    audio_output = config.get("audio_output", "respeaker") if config else "respeaker"
    args = [MPV_BIN, "--quiet", "--fs", "--vo=drm", "--no-terminal", "--ontop"]
    args += audio.build_mpv_args(audio_output)
    args.append(source)
    env = os.environ.copy()
    env.setdefault("SDL_VIDEODRIVER", "fbcon")
    try:
        subprocess.run(args, env=env, check=False)
    except FileNotFoundError:
        print("mpv is not installed or not in PATH")
