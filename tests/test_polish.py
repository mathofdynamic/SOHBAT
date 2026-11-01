from sohbat.polish import polish


def test_polish():
    assert polish(" um hello   world uh ") == "Hello world."
    assert polish("what?") == "What?"
    assert polish("  ") == ""
    assert polish("um hi", False) == "Um hi."
    assert polish("umbrella") == "Umbrella."
