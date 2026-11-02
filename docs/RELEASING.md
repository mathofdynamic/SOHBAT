# Windows releases

The canonical version is `sohbat/__init__.py`. Increment it before each public release. Setuptools, executable resources, installer filenames, and installer metadata read this same value.

Install Inno Setup 6.7.4 or newer and prepare the development environment and English Tiny Streaming model. Set `ISCC_PATH` if the compiler is outside its standard installation directory. Build with:

```powershell
./scripts/check.ps1
./scripts/build-installer.ps1
```

The build verifies all eight model files against the Moonshine manifest, bundles the runtime and dependency licenses, embeds the generated microphone icon, and renders the generated banner in the installer. Outputs are `dist/installers/SOHBAT-Setup-VERSION-windows-x64.exe` and `SHA256SUMS.txt`. Build artifacts and model weights must stay outside source control.

## Update contract

Never change AppId `{D0E533D9-A5F2-44B0-B513-BDA47EE40618}`. Keep the per-user installation scope and `UsePreviousAppDir=yes`. Existing registered paths are reused. Settings and external models are outside the runtime directory. Only the owned `_internal` runtime is cleaned during an update; installed model files are replaced from the verified payload. The installer preserves an existing startup entry and blocks downgrades. There is no automatic update service.

Before publishing, install over the previous version while it is running, verify that the executable version advances, settings remain byte-identical, startup points to the same installation, stale runtime files disappear, and only one uninstall entry remains. Launch the installed app and exercise tray Settings. Run the old installer afterward and verify that it refuses the downgrade without changing the executable or settings. Review the actual welcome page for banner, icon, typography and clipping.

## Release 0.1.1 evidence

Tested on Windows 11: installer 0.1.0 baseline followed by 0.1.1. Automated results are recorded locally under ignored `.perfection/installer-tests`. This is a same-machine upgrade test, not a clean Windows VM test. This preview is unsigned; do not describe it as signed or SmartScreen trusted.

Publish the exact checked installer and checksum as assets of the matching GitHub tag. Keep preview status until the limitations in README are resolved. Future releases must retain this update contract.

Installed 0.1.1 tray callback smoke passed with Settings visible and restored; model-ready was confirmed in the installed runtime log. Launch GUI smoke tests normally: a hidden process launch can override the first native window visibility.
