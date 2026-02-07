import time

try:
    import spidev
except ImportError:  # running on dev machine
    spidev = None


class Apa102Leds:
    def __init__(self, enabled=True, num_leds=3, brightness=0.2):
        self.enabled = bool(enabled) and spidev is not None
        self.num_leds = num_leds
        self.brightness = brightness
        if self.enabled:
            try:
                self.spi = spidev.SpiDev()
                self.spi.open(0, 0)  # bus 0, device 0
                self.spi.max_speed_hz = 8000000
            except Exception:
                self.enabled = False
                self.spi = None
        else:
            self.spi = None

    def _frame(self, r, g, b):
        # APA102 frame: 0b111xxxxx brightness, then BGR
        level = max(1, min(31, int(self.brightness * 31)))
        return [0b11100000 | level, b & 0xFF, g & 0xFF, r & 0xFF]

    def set_all(self, r, g, b):
        if not self.enabled:
            return
        frames = [[0x00, 0x00, 0x00, 0x00]]
        frames += [self._frame(r, g, b) for _ in range(self.num_leds)]
        frames += [[0xFF, 0xFF, 0xFF, 0xFF]]
        flat = [byte for frame in frames for byte in frame]
        try:
            self.spi.xfer2(flat)
        except Exception:
            self.enabled = False

    def pulse(self, r, g, b, times=1, delay=0.15):
        for _ in range(times):
            self.set_all(r, g, b)
            time.sleep(delay)
            self.set_all(0, 0, 0)
            time.sleep(delay)

    def off(self):
        self.set_all(0, 0, 0)

    def close(self):
        if self.spi:
            try:
                self.spi.close()
            except Exception:
                pass
