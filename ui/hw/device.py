import os


def has_respeaker_hat():
    """Best-effort detection of the ReSpeaker HAT."""
    hat_product_path = "/proc/device-tree/hat/product"
    try:
        with open(hat_product_path, "rb") as f:
            name = f.read().decode(errors="ignore").lower()
            return "respeaker" in name or "seeed" in name
    except FileNotFoundError:
        pass

    # Fallback: check for seeed voicecard module
    try:
        with open("/proc/asound/cards", "r", encoding="utf-8") as f:
            content = f.read().lower()
            if "seeed-2mic-voicecard" in content or "seeed voicecard" in content:
                return True
    except FileNotFoundError:
        pass

    return False
