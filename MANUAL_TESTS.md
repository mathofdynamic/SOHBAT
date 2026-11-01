# Manual acceptance checks

These require physical hardware, sign-in, or the real applications you use.

1. Hold Ctrl+Windows before launch, release, then dictate. Confirm startup does not unintentionally record.
2. Unplug the selected microphone during speech. Check for a readable error; reconnect and verify recovery or the documented need to relaunch.
3. Dictate into Notepad, a browser text area and your Electron editor. Verify insertion and clipboard restoration. Elevated applications may reject input from a normal process.
4. Run `.venv/Scripts/python scripts/smoke_injection.py`, immediately click its test input, and confirm the console reports PASS. Windows foreground rules can deny unattended activation.
5. Copy text or an image during clipboard restoration. Verify the newer copy remains.
6. On multiple monitors, test pill placement, readable text, click-through behavior and keyboard focus retention.
7. Run a five-minute dictation. Verify the cap warning, finalization and the next shortcut gesture. Toggle synchronization at the cap needs focused validation.
8. Enable Open at sign-in, sign out/in, and verify one SOHBAT instance starts. Disable it and repeat.
9. Check Windows screen-reader announcements and larger-text/200% scaling. These are not yet fully validated.
