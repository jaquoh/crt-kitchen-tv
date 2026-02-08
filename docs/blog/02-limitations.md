

## 02 – Limitations, Reality Checks, and a Better Direction

When this project started, the idea was simple and ambitious at the same time:  
turn a small 5″ CRT TV into a modern-but-curated kitchen display, driven by a Raspberry Pi and a custom UI. News, videos, maybe even live streams — all controlled through a deliberately minimal interface.

The hardware choice for the first iteration was a **Raspberry Pi Zero**, mainly because it is:
- tiny,
- low power,
- cheap,
- and perfectly sized for being mounted directly onto a CRT.

This post documents the moment where theory met reality.

---

### The first hard limit: live video streaming

The biggest open question early on was:  
**Can a Raspberry Pi Zero handle modern video streams?**

After getting everything else working — boot process, framebuffer, X11, pygame UI, mpv integration — the answer became very clear:

> **Live HLS video streams are not a realistic workload for a Pi Zero.**

Even when forcing:
- the lowest-quality HLS variant,
- no audio,
- aggressive frame dropping,
- minimal buffering,

the result was effectively a slideshow: a few frames per minute, high CPU load, and no usable playback experience.

This was not a configuration bug, nor missing libraries. It is simply a consequence of:
- single-core ARMv6 CPU,
- no reliable hardware video decoding path on modern kernels,
- software H.264 decoding being far too expensive.

At that point, the project reached a clear boundary set by physics and silicon.

---

### Important clarification: this is *not* a dead end

It’s important to stress what this *doesn’t* mean:

- The UI architecture works.
- The install script works.
- The X11 + pygame + mpv stack works.
- The same code **will** work on stronger hardware (Pi 3, Pi 4, CM4).

Live streams were not removed or abandoned — they are simply **not the primary target** for the Pi Zero class of hardware.

This distinction matters, because it shaped the next design decision.

---

### Reframing the project: from “live streaming” to “local media appliance”

Once live streaming was set aside as a *hardware-dependent feature*, a much more interesting and robust direction emerged:

> Treat the Pi Zero as a **media appliance**, not a streaming device.

Instead of asking the Pi to decode unpredictable, high-bitrate live streams in real time, we let it do what it *is* good at:

- deterministic workloads,
- local files,
- curated content,
- predictable performance.

This led to a new main focus for the project.

---

### The new primary feature: a local video library

The core idea is now:

- The Pi hosts a **local media library**.
- Video files are transferred to it over the local network.
- The CRT UI presents them in a simple, readable, remote-friendly menu.
- Playback is instant, smooth, and reliable.

This approach has several advantages:

- Local files can be **pre-transcoded** to formats the Pi Zero handles well.
- No buffering, no network jitter, no adaptive bitrate surprises.
- The UI feels like a real appliance, not a web browser.

In practice, this means:
- a shared “Inbox” folder on the Pi,
- drag-and-drop file transfer from any device,
- automatic appearance of new content in the CRT menu.

---

### Live streams are still part of the project — just not mandatory

Crucially, live streams were **not removed** from the design.

They remain:
- an optional feature,
- enabled automatically on more capable hardware,
- or usable for very low-bitrate sources if available.

The project is now explicitly **hardware-aware**:
- Pi Zero → local media first
- Pi 3 / Pi 4 → local media *plus* live streams

Same codebase. Same UI. Different capability profiles.

---

### Why this is actually the better design

In hindsight, this limitation turned out to be a strength.

The project is no longer trying to imitate a modern smart TV.  
Instead, it embraces what a small CRT and limited hardware do best:

- curated content,
- intentional viewing,
- no endless feeds,
- no notifications,
- no autoplay algorithms.

In other words: a calm, reliable, purpose-built device.

---

### Next steps

With this new direction established, the following features became the priority:

1. A local media library with clear structure.
2. Very easy file transfer to the Pi (Samba).
3. Automatic appearance of new content in the UI.
4. Optional automated downloads (news episodes, daily shows, retention rules).
5. Keeping the door open for live streams on stronger hardware.

That is where the project really starts to feel complete.