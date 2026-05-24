# tools/

Experimental scripts. Not shipped to end users — for prototyping only.

## demo_mascot.py

A minimal "show me what mascot overlay could look like" demo.

### Setup (one-time)

Pillow gives proper PNG-with-alpha rendering on Tk 9.0. Use a project-local
venv to bypass PEP 668 system-pip restrictions:

```bash
cd /path/to/better-phrase
python3 -m venv .venv
.venv/bin/python3 -m pip install pillow
```

(Already done if you ran the setup; the venv lives at `.venv/`.)

### Run

```bash
cd /path/to/better-phrase

# Single image, 3-second popup at bottom-right of screen:
.venv/bin/python3 tools/demo_mascot.py assets/mascots/idle.png

# Two-frame "alive" animation (cycles every 500ms):
.venv/bin/python3 tools/demo_mascot.py assets/mascots/idle.png assets/mascots/tip.png

# Custom duration:
.venv/bin/python3 tools/demo_mascot.py assets/mascots/idle.png --duration 5

# Custom background color (try 'white' or '#ffffff' if your art is on white):
.venv/bin/python3 tools/demo_mascot.py assets/mascots/idle.png --bg white
```

### Background color

Tk on macOS doesn't reliably support a truly transparent window. The script
composites the PNG onto a solid background. Default is dark grey (`#1e1e1e`)
which works for most anime art. If your image was generated on a white
background, pass `--bg white` to make the seam invisible.

### What this proves

- A floating, always-on-top, borderless window CAN be triggered from Python
- It WILL be visible on top of Claude Code's terminal
- Frame-cycling between PNGs gives a "fake animation" feel
- Fade-out makes it feel less abrupt

### What this doesn't (yet) prove

- Integration with the hook (currently you run this manually)
- Real Live2D rigged animation (eye blink, breathing, mouth sync)
- True transparency around the character (requires Electron / native window APIs)
- Cross-platform polish (macOS is the main test target)

For those, the path is a proper Electron + Live2D sister project. This
script is just to validate the visual concept on your machine, now.
