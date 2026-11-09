# EasyWG PortableApps Builder b1r1

**Mode: PORTABLEAPPS only**. Builds a validated ZIP plus an independent *custom-NSIS PortableApps-style* `.paf.exe` installer from the author's genuine Windows EasyWG release. The builder runs on hosted **Windows Server 2022 / x64 GitHub Actions**. No local compiler, fork, manual Git initialization, or private action is necessary.

## Why this architecture

Tagged upstream `src/main.cpp` uses `GetModuleDirectory()` to locate `EasyWG.ini` and to extract ZIP-imported configuration. It also places automatically downloaded core DLLs beside the running executable. Therefore a pure launcher approach is possible: a compiled Windows `EasyWGPortable.exe` starts an **unchanged official upstream EasyWG.exe** from `Data/Runtime/EasyWG.exe`. Settings, imported profiles, empty directories, component DLLs and secrets remain in `Data/Runtime` without broad harvesting of the host AppData directories.

`App/EasyWG/EasyWG.exe` is the official versioned **read-only package seed**. `Data/Runtime/EasyWG.exe` is the actual run location and survives updates. This intentionally duplicates the executable once per package so the official source binary stays intact while portable data is centralized. No custom driver or VPN security bypass is performed. Windows Tunnel service creation still requires Windows privileges.

### Beginner-friendly GitHub Desktop setup

1. In GitHub, click **New repository**, name it `EasyWG-PortableApps-Builder`. Choose public or private. Do **not** fork the upstream repository. Ensure **Actions** is allowed.
2. Open GitHub Desktop, **File > Clone repository**, select your new repository.
3. Extract the entire builder kit ZIP into your cloned repository folder. Include the hidden `.github` directory and all subfolders. Do **not** place the kit inside an extra nested folder.
4. In GitHub Desktop, write commit summary `Initial EasyWG PortableApps builder b1r1`, then **Commit to main** and **Push origin**.
5. Open your repository on GitHub. Go to **Actions > EasyWG Portable - Build ZIP and Installer > Run workflow**. Leave upstream version as `latest` or specify an exact stable tag such as `v0.2.9.2`.
6. Inspect all logs. Look for source/tag/asset digest resolution, **MSVC compile**, **ZIP validation**, shared **custom-NSIS build**, installer validation, dry-run, and real publication. A red workflow means the release is not fully verified.
7. Click **Releases** in the builder repository. Download the `EasyWGPortable-...zip` or the separate `...custom-nsis-r1.paf.exe` and `SHA256SUMS.txt` generated automatically by the shared publisher.
8. Verify the downloaded file hash in Windows PowerShell: `Get-FileHash 'C:\path\to\download.zip' -Algorithm SHA256`. Compare with `SHA256SUMS.txt`.
9. **ZIP:** Extract it into a permanent/USB folder (for example, `D:\PortableApps\EasyWGPortable`) and start `EasyWGPortable.exe`. **Installer:** run the independent PortableApps-style installer, choose destination, then use PortableApps Platform **Apps > Refresh App Icons**.
10. Import/select your `.conf` file (prefer copying it into `Data\Runtime` first) and connect only on machines/networks you are authorized to access. Accept elevation only if you intend to create the tunnel service. Before moving/ejecting/updating, click **Disconnect**, then **Exit** in the tray, and wait until EasyWG processes stop.
11. **Upgrade:** Back up the entire `Data` folder, install/extract the updated package **without deleting/replacing existing `Data`**, and start the root launcher. **Rollback:** close/disconnect, back up `Data`, then restore the old package version. Data/schema rollback may require restoring its matching backup.

### Typical output structure

```
EasyWGPortable/
  EasyWGPortable.exe                 compiled Win32 x64 PortableApps launcher
  App/
    AppInfo/appinfo.ini
    AppInfo/appicon.ico
    AppInfo/appicon_16.png
    AppInfo/appicon_32.png
    EasyWG/EasyWG.exe                authentic official upstream binary
  Data/
    Runtime/                         actual EasyWG.exe and persistent data after first run
    Backups/                         previous runtime binary (only if replaced)
  Other/Source/                      source + provenance + original upstream MIT LICENSE
  README.txt
```

### Build security / provenance

- Latest version discovery uses GitHub REST releases sorted by **numeric** 3- or 4-segment version, excludes prerelease/draft/core tags and respects an explicitly requested stable version. Missing or invalid official assets fail the build; no fallback to `main` or unofficial mirrors.
- Downloads exact official `EasyWG.exe` and the **same tagged** source code. Records the release tag, upstream Git commit SHA, builder Git commit SHA, source-main SHA-256, source archive SHA-256, binary SHA-256, builder revision and release identity in `BUILD-IDENTITY.json`. Release tags include upstream/source, binary and builder commit identifiers so changed builder code cannot silently reuse a published package identity.
- Pins the official published `v0.2.9.2` executable SHA-256 and verifies a publisher-provided SHA-256 asset or GitHub's asset digest for other releases **when present**; if neither exists, it records the limitation rather than presenting an independently authenticated digest. Windows Authenticode signature status is **not** asserted.
- `appicon.ico`/PNG files are extracted from the official upstream executable, not replaced with invented branding.
- Built launcher uses un-obfuscated C++17 and MSVC `/MT`; no hidden developer-only tools or production action upgrades.
- Shared action baselines are `vhick/Portable-Package-Builder@v1.0.0` and `vhick/portable-release-publisher@v1.1.1`, pinned in the workflow to verified full release commit SHAs (`0112c35580e83b37eb8757ebcb949274e1631a04` and `cb64f86ac2d8c67506db5832de07f9ff58cbeaeb`). Their tagged `action.yml` must match the immutable-commit `action.yml` bytes before any build.
- Generates independently validated ZIP **before** invoking shared installer. Both pass to publisher after its mandatory dry-run. Publisher generates an official release `SHA256SUMS.txt` for the two assets. `prune=false` and `keep-releases=3` protect unrelated releases.
- If installer generation or publishing fails, an already validated ZIP is uploaded as a short-lived workflow artifact (3 days); it is **not** represented as a finished published installer.

### Special EasyWG host and co-existence precautions

- `Data\Runtime\EasyWG.ini` stores app settings and may reference the config. A `.conf` file contains a plaintext WireGuard private key. Do **not** commit the `Data` folder or real `.conf` files to any GitHub repository.
- Upstream `SetAutostartRegistry` writes the exact HKCU `Software\Microsoft\Windows\CurrentVersion\Run` value `EasyWG Portable` when the user enables its startup option. The root launcher verifies/rewrites its own value to launch through `EasyWGPortable.exe` after normal exit. If a pre-existing same-name value belongs to another installed app, the launcher attempts to restore it after normal exit. The upstream can still temporarily overwrite it during operation and an abrupt process kill can interrupt restoration. **Avoid opting into autostart when an installed EasyWG uses the same name**. Manual registry audit is required after crashes.
- Upstream's `Local\EasyWGPortableMainInstance` single-instance mutex can conflict with another EasyWG instance (installed or a second portable copy). Do not change or delete another application's mutex, registry record, service, network adapter or driver.
- The app establishes a temporary Windows tunnel service with user-authorized elevation. It may create Win7 legacy debug logs and framework/OS-managed temporary files, driver state, network settings and event logs. This kit uses **no broad TraceGuard or ShellGuard scavenger** because module-relative profile storage already works and host-level service state must be handled by upstream, not blindly deleted.
- Windows 10/11 x64 are the intended package targets; Windows 7 support claimed by the upstream app has **not** been validated for this custom MSVC launcher.

### Independent verification status

| Stage | Status in this distributed source kit |
|---|---|
| Main EasyWG source path and startup/service evidence | SOURCE-INSPECTED (tagged public source) |
| Pinned action contracts and publisher behavior | SOURCE-INSPECTED (public pinned action files) |
| Kit Python unit tests, static YAML checks | STATIC-VALIDATED locally |
| Downloading actual official binary through GitHub Actions | NOT YET VERIFIED |
| Native Windows launcher compilation | NOT YET VERIFIED |
| ZIP built on Windows runner | NOT YET VERIFIED |
| Shared NSIS installer built on Windows runner | NOT YET VERIFIED |
| GUI, tray, reconnect, service and data containment | NOT YET VERIFIED |
| Autostart/registry crash recovery and installed-app coexistence | NOT YET VERIFIED |
| Installer install/reinstall/upgrade and data safety | NOT YET VERIFIED |
| Published release | NOT YET VERIFIED |

**This ZIP is the builder source kit, not the compiled app itself.** Windows CI and manual acceptance must pass before a ready-to-run app can be claimed.

### Manual Windows acceptance checklist

1. Extract ZIP under an ordinary user directory, run launcher, verify GUI and `Data/Runtime/EasyWG.ini` are created. Verify no config or binary written beside package root. Repeat with a space/Unicode folder name.
2. Import a real user-owned `.conf` and a ZIP containing a `.conf`; verify import files are in `Data/Runtime`; restart, select a profile, verify settings and keys retained. Do not put credentials in screenshots or logs.
3. With user approval connect to a test WireGuard endpoint; verify tunnel handshake, DNS/routes, tray close/show/exit and disconnection. Confirm temporary owned service exits. Compare Windows services before/during/after, **do not** delete unidentified services.
4. Run a test with installed EasyWG present, including the same-name HKCU Run value and separate configs; verify launcher does not permanently modify other profile/Run data on **normal exit**. Test the crash case in an isolated VM and manually inspect the Run value.
5. Enable startup **only in a disposable VM**, check entry targets the root launcher after normal exit and is removed when disabled; move folder, verify stale startup needs explicit repair.
6. Verify update/reinstall preserves `Data`, empty directories, `.conf` and profiles, and rollback behavior with a backup. Test installer selection and destination, too.
7. Examine Windows Event Viewer, system TEMP, registry and Windows service/driver history. Do not interpret unavoidable Windows activity as a bug unless app-owned permanent state is proven.

See `docs/AUDIT.md`, `docs/TROUBLESHOOTING.md`, and `docs/PORTABLE-RUNTIME.txt` for limitations and recovery details.
