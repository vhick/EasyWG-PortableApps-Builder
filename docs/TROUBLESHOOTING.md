# Troubleshooting and safe rollback

- **Source resolver fails, 404:** Verify requested version on official Releases. Release must be stable and include `EasyWG.exe`. A core-v1 release is not an application version. Authentication failures / 403 / 429 should not be bypassed using random mirrors.
- **MSVC/rc compilation fails:** Open the `Build genuine Windows x64 C++ PortableApps launcher` log and share its exact error. Only the GitHub hosted Windows 2022 compiler is supported; do not run the build CMD on your workstation unless deliberately diagnosing.
- **Shared installer fails but ZIP passes:** Download the short-lived `easywg-verified-zip-after-failure` workflow artifact from Actions. Do not call the installer complete or publish an unvalidated EXE. Review the Package Builder log and fix that stage, then rerun.
- **EasyWG starts but no VPN:** Check genuine .conf credentials, internet connectivity and administrator approval. Missing `tunnel.dll` or `wireguard.dll` downloads may require internet/TLS/Windows support. Check upstream documentation, not random DLL sites.
- **App remains in tray:** Use EasyWG tray > Exit, rather than only closing main window. The wrapper waits for all accessible matching runtime processes and does not forcibly kill them.
- **Wrong installed application opens:** Upstream has its own global single-instance mutex; shut down installed EasyWG before testing. Do not delete installed app or registry data to make this package run.
- **Can’t update EasyWG.exe:** Exit tray and disconnect; wait for tunnel service to stop. The wrapper does not overwrite executable while its runtime path is reported active.
- **Accidentally enabled Windows startup:** From EasyWG options disable it and exit normally. Inspect HKCU Run `EasyWG Portable` value. If an installed app previously owned that name, restore it from an independent backup or from that application's settings. Do not blindly delete other startup items.
- **Moved the folder:** Run root launcher from new location; user-approved startup registry entries may point to old location and require manual repair. Keep `Data` with the folder; avoid external absolute `.conf` paths.
- **Upgrade corruption:** Exit/disconnect, make a complete current `Data` backup, restore the prior ZIP's `App`/`Other`/launcher, then if schema incompatibility exists restore the matching prior `Data` backup. Do not recursively erase user files.
- **Potential private key disclosure:** Treat `Data/Runtime/*.conf`, `EasyWG.ini`, backups, downloaded profiles and any saved diagnostic as sensitive. Never upload those to public issues or GitHub CI.
- **Failure during service cleanup:** Do not force-remove Windows services based merely on a similar name. Inspect the exact service image path, source, ownership and active use before authorized repair; the automated kit never performs broad deletion.


## b1r1 GitHub Actions error: LNK2019 __imp_MessageBoxW / LNK1120

**Symptom:** The `Build genuine Windows x64 C++ PortableApps launcher` step fails with `unresolved external symbol __imp_MessageBoxW`. This occurs after successful source download, staging and compilation but before any ZIP or installer is produced.

**Cause:** The launcher uses `MessageBoxW` from the Windows User32 import library; `User32.lib` was not linked in b1r1.

**Resolution in b1r2:** The source declares `#pragma comment(lib, "user32.lib")` and the MSVC invocation explicitly passes `user32.lib` after `/link`. Two offline regression tests check linker contract and synchronized release revisions. Replace the complete builder repo contents with b1r2, commit/push and rerun the main GitHub workflow. A successful hosted Windows linker run is required before treating this issue as confirmed resolved.

Do not attempt to fix this by installing User32.dll or copying DLLs into the application ZIP. `User32.lib` is a Windows SDK import library that the hosted Visual Studio build tools already provide.
