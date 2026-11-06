import pytest

from gestura.controllers.backends import RecordingBackend
from gestura.controllers.keyboard_controller import KeyboardController
from gestura.controllers.virtual_keyboard_controller import VirtualKeyboardController
from gestura.ui.keyboard.layouts import layout


def vk(send=True):
    be = RecordingBackend()
    return VirtualKeyboardController(KeyboardController(be), can_send=lambda: send), be


def key(lay, label):
    for row in layout(lay):
        for k in row:
            if k.label == label:
                return k
    raise KeyError(label)


def press(c, k):
    return c.press(k.kind, k.value, k.shifted, k.letter)


@pytest.mark.parametrize("name", ["azerty", "qwerty"])
def test_layouts_have_required_keys(name):
    labels = {k.label for row in layout(name) for k in row}
    kinds = {(k.kind, k.value) for row in layout(name) for k in row}
    for needed in ("⌫", "Space", "Enter ⏎", "⇧ Shift", "Caps", "Tab", "Esc", "←", "→", "↑", "↓", "Ctrl", "Alt", "Win"):
        assert needed in labels, needed
    letters = {k.value for row in layout(name) for k in row if k.letter}
    assert letters == set("abcdefghijklmnopqrstuvwxyz")
    digits = {k.value for row in layout(name) for k in row} | {k.shifted for row in layout(name) for k in row}
    assert set("0123456789") <= digits
    assert ("mod", "shift") in kinds and ("caps", "caps") in kinds


def test_azerty_specifics():
    rows = layout("azerty")
    assert [k.value for k in rows[1][1:7]] == list("azerty")
    num = rows[0][1:11]
    assert num[1].value == "é" and num[1].shifted == "2" and num[9].value == "à"


def test_typing_letters_shift_and_caps():
    c, be = vk()
    a = key("qwerty", "A")
    press(c, a)
    press(c, key("qwerty", "⇧ Shift"))
    press(c, a)  # one-shot shift
    press(c, a)
    press(c, key("qwerty", "Caps"))
    press(c, a)
    press(c, key("qwerty", "⇧ Shift"))
    press(c, a)  # shift + caps -> lower
    assert [x[1] for x in be.named("write_text")] == ["a", "A", "a", "A", "a"]
    assert c.preview == "aAaAa"


def test_shift_on_symbols_and_azerty_digits():
    c, be = vk()
    press(c, key("azerty", "⇧ Shift"))
    press(c, key("azerty", "é"))
    press(c, key("azerty", "é"))
    assert [x[1] for x in be.named("write_text")] == ["2", "é"]


def test_double_shift_locks():
    c, be = vk()
    s, b = key("qwerty", "⇧ Shift"), key("qwerty", "B")
    press(c, s)
    press(c, s)
    for _ in range(3):
        press(c, b)
    press(c, s)  # unlock
    press(c, b)
    assert "".join(x[1] for x in be.named("write_text")) == "BBBb"


def test_ctrl_shortcut_and_release():
    c, be = vk()
    press(c, key("qwerty", "Ctrl"))
    press(c, key("qwerty", "C"))
    press(c, key("qwerty", "C"))
    assert be.named("hotkey") == [("hotkey", "ctrl", "c")]
    assert be.named("write_text") == [("write_text", "c")]


def test_special_keys_and_backspace_preview():
    c, be = vk()
    press(c, key("qwerty", "H"))
    press(c, key("qwerty", "I"))
    press(c, key("qwerty", "⌫"))
    press(c, key("qwerty", "←"))
    press(c, key("qwerty", "Alt"))
    press(c, key("qwerty", "Tab"))
    assert ("press", "backspace") in be.calls and ("press", "left") in be.calls
    assert ("hotkey", "alt", "tab") in be.calls
    assert c.preview == "h"


def test_space_key_types_a_space():
    c, be = vk()
    press(c, key("azerty", "Space"))
    assert be.named("write_text") == [("write_text", " ")]


def test_preview_only_when_sending_disabled():
    c, be = vk(send=False)
    desc = press(c, key("qwerty", "A"))
    press(c, key("qwerty", "Enter ⏎"))
    assert be.calls == [] and "not sent" in desc
