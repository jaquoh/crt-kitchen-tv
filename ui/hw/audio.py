import subprocess
import shlex

RESPEAKER_CARD_IDS = ["seeed-2mic-voicecard", "seeedvoicecard"]


def detect_respeaker_card():
    try:
        out = subprocess.check_output(["cat", "/proc/asound/cards"], text=True)
    except Exception:
        return None
    for line in out.splitlines():
        lower = line.lower()
        for card in RESPEAKER_CARD_IDS:
            if card in lower:
                return card
    return None


def audio_device_for(output_pref):
    if output_pref == "respeaker":
        card = detect_respeaker_card()
        if card:
            return f"alsa/plughw:CARD={card}"
    if output_pref == "hdmi":
        return "alsa/hw:0,0"
    if output_pref == "analog":
        return "alsa/hw:0,1"
    return "auto"


def set_volume(percent):
    try:
        subprocess.run(["amixer", "sset", "Master", f"{int(percent)}%"], check=False)
    except FileNotFoundError:
        pass


def build_mpv_args(output_pref):
    dev = audio_device_for(output_pref)
    if dev == "auto":
        return []
    return [f"--audio-device={dev}"]
