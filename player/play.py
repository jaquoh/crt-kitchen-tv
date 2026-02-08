import subprocess
from ui.hw import audio


MPV_BIN = "mpv"


def play_media(source, config):
    audio_output = config.get("audio_output", "respeaker") if config else "respeaker"
    args = [MPV_BIN, "--quiet", "--fs", "--vo=gpu", "--gpu-context=x11", "--no-terminal", "--ontop"]
    args += audio.build_mpv_args(audio_output)
    args.append(source)
    try:
        subprocess.run(args, check=False)
    except FileNotFoundError:
        print("mpv is not installed or not in PATH")
