# Decisions

- Windows is the implemented platform. Win32 input, UI Automation and startup registration are isolated in the input/accessibility/platform modules. Porting requires native replacements, not just packaging changes.
- Python 3.14.3 and Windows 11 were used for local verification. The source declares Python 3.10+; CI uses Python 3.12.
- The installed `moonshine-voice==0.1.5` source and signatures were inspected before implementing streaming. The engine uses `create_stream`, listener events, `add_audio` and `stop`, with one warm `Transcriber` per worker.
- Audio sent to the model is mono normalized float32 at 16 kHz. Native 16 kHz capture is preferred. The fallback resamples native-rate blocks using scipy polyphase filtering; continuity across those fallback blocks needs further work.
- Audio callbacks only copy into a bounded deque and compute levels. The speech worker serializes inference. Qt signals deliver UI updates. The worker blocks on its command queue while idle.
- Normal launch never downloads models. Setup is an explicit network operation; normal dictation uses local files. Logs contain exceptions and timing, not transcript text.
- Ctrl+Windows is the default hold shortcut. Both modifiers must be released before paste to avoid invoking a modified Windows shortcut. Toggle presses also require 250 ms, matching short-tap suppression.
- Insertion targets the foreground window captured at recording start. A changed foreground cancels insertion. UI Automation checks editable/read-only state; optional compatibility handles browser hosts that do not expose a native caret. Password fields are excluded when accessibility identifies them.
- Clipboard MIME data is preserved and restored only if the clipboard still contains the app's text. A newer user copy is preserved.
- Preferences use three bounded pages, Inter typography, theme-aware neutral surfaces and native keyboard-accessible controls. Inter and its OFL license are bundled; no runtime font request is needed.
- The recording island is painted inside a fixed click-through, nonactivating tool window. Analytic critically damped springs animate its dimensions and opacity from current position and velocity. Hidden windows stop their animation timer. The surface now renders a clipped blurred desktop sample, with a dark tint; no undocumented Windows blur API is used.
- Reduced motion freezes ongoing animation and uses opacity transitions; the Windows animation preference is respected. Reduced transparency raises surface opacity. Overlay preview has its own instance and cancellable timer.
- Informational outcomes remain visible longer than successful insertion, which dismisses in under 400 ms in the measured check.
- SOHBAT replaces the former Flowlet branding and Python package name. First load copies legacy preferences and managed models when no SOHBAT configuration exists. Existing SOHBAT preferences take precedence. Legacy data is retained, and the installer removes the old startup entry/shortcut.
- Local install/update targets `%LOCALAPPDATA%/Programs/SOHBAT`. Configuration lives separately under `%LOCALAPPDATA%/SOHBAT`. Source publication includes no downloaded model weights, local settings, logs, builds or release binaries.
- The public repository starts from a clean source snapshot. Local development history remains in the original branch; session checkpoints are not part of the public branch.
- The logo and banner are image-generated project assets. Windows ICO sizes are derived from the transparent logo. Source code is MIT; Inter and dependencies keep their own licenses.
- Multilingual/Whisper support is deferred. The default engine is English Tiny Streaming, architecture 2.

- Windows system-backdrop and accent prototypes did not preserve the animated capsule clip and were discarded. The final implementation uses documented temporary capture exclusion on our own window plus Qt blur, with a half-resolution cache updated at up to 10 Hz only while visible and settled. Affinity restoration is guarded by finally blocks. No background pixel data is written to disk by the app. Reduced transparency and sampling failure use a fully opaque fallback.

- Tray Trigger and DoubleClick explicitly open preferences. Settings menu activation waits40ms for the shell menu to release focus, then restores and raises a centered preferences window. Native tray callback regression is exercised by scripts/smoke_tray_windows.py against Qt6.10.3.


## Windows installer and version identity

- Inno Setup packages the runtime and verified English Tiny Streaming model for offline first launch. The existing generated icon and banner are embedded; the wizard privately loads Inter.
- Permanent AppId `{D0E533D9-A5F2-44B0-B513-BDA47EE40618}` and per-user scope identify one installation across releases. Registered install paths are reused; older versions cannot overwrite newer versions.
- `sohbat.__version__` is the single source for package, executable and installer versions. Release 0.1.1 follows a local 0.1.0 upgrade baseline.
- Settings, logs and external model paths are preserved. Updates replace only the app-owned runtime and bundled model; obsolete runtime files are removed to prevent mixed dependency versions.
- Startup registration is retained if previously enabled. Fresh users choose startup in Settings. Updates remain manual to preserve offline operation.
- Dependency notices and full Qt LGPL/GPL texts are distributed with replaceable shared libraries and source links. The unsigned preview does not claim code-signing trust.

- Launch the GUI executable with normal window visibility. Windows `STARTF_USESHOWWINDOW` from a hidden process launch can suppress the first Settings window despite Qt reporting it visible; the app itself starts tray-only.

- Model selection supports English streaming architectures 2, 4 and 5 through the installed Moonshine downloader with progress callbacks. Downloads run on a background daemon; engine replacement stays on the existing audio worker and saves only after successful loading. Explicit user-triggered downloads are the only runtime network operation.

- Model downloads show aggregate progress in a themed progress bar; internal filenames stay out of the interface. Download, engine-loading, success and retry states are distinct. Selection is locked until loading finishes, and Models hides the unrelated Save action.
