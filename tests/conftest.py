import os

# GUI tests run headless unless a display is explicitly provided for OS tests.
if os.environ.get("GESTURA_OS_TESTS") != "1":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
