from sohbat.hotkey import Gesture


def test_hold_and_short_tap():
    now = [0.0]
    events = []
    gesture = Gesture(events.append, clock=lambda: now[0])
    gesture.press()
    gesture.press()
    now[0] = .1
    gesture.release()
    assert events == ['start', 'cancel']
    gesture.press()
    now[0] = .5
    gesture.release()
    assert events[-2:] == ['start', 'stop']


def test_toggle():
    now = [0.0]
    events = []
    gesture = Gesture(events.append, 'toggle', lambda: now[0])
    for instant in [.3, .7]:
        gesture.press()
        now[0] = instant
        gesture.release()
    assert events == ['start', 'stop']
