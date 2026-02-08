

# Deployment workflow

This document describes the intended workflow for developing **crt-kitchen-tv** on a separate machine and deploying updates to the Raspberry Pi.

The Raspberry Pi is treated as a **deployment target**, not a development environment.

---

## Roles

### Development machine

The development machine (Linux, macOS, or Windows) is used for:

- Writing and refactoring code
- UI design and iteration
- Managing git history (commits, branches, merges)
- Editing documentation

All changes to the repository originate here.

### Raspberry Pi (target system)

The Raspberry Pi is used for:

- Running the application
- Testing on real CRT hardware
- Playing media
- Receiving input (IR, GPIO)

The Pi **does not create commits**. It only pulls updates.

---

## Repository ownership

On the Raspberry Pi, the repository is located at:

```
/opt/crt-kitchen-tv
```

- The directory is owned by user `crt`
- All services run as user `crt`
- System changes are performed via `sudo`

Never run `git` as root inside the repository.

---

## Updating the Pi

After pushing changes from the development machine, update the Pi as follows:

```
cd /opt/crt-kitchen-tv
git fetch origin
git reset --hard origin/main
sudo systemctl restart crt-ui
```

This ensures the Pi exactly matches the repository state.

---

## Local-only files on the Pi

Some files may exist only on the Pi and should not be committed upstream, such as:

- `__pycache__/`
- Runtime-generated files
- Temporary test artifacts

These are excluded locally using:

```
.git/info/exclude
```

This keeps the repository clean without modifying `.gitignore` globally.

---

## Updating dependencies

If `requirements.txt` changes upstream:

1. Pull the repository as described above
2. Reinstall Python dependencies:

```
cd /opt/crt-kitchen-tv
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart crt-ui
```

---

## Services

Two systemd services are used:

- `crt-ui.service` — fullscreen CRT UI (pygame via X11)
- `crt-web.service` — web-based configuration interface

Service management:

```
sudo systemctl restart crt-ui
sudo systemctl restart crt-web
journalctl -u crt-ui -n 50 --no-pager
```

---

## Philosophy

The Raspberry Pi behaves like an appliance:

- No interactive development
- No desktop environment
- Deterministic boot into the UI

This separation keeps the system reliable and reproducible.