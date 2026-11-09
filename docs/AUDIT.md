# EasyWG source-based portability audit (PORTABLEAPPS only)

Inspected upstream release: `v0.2.9.2`, GitHub release tag shown with short commit `d18c1fc`. Workflow retrieves complete commit SHA from GitHub API, exact tagged source ZIP, and release binary, then verifies runtime source evidence before packaging.

Public code: https://raw.githubusercontent.com/Terence0816/easy-wg-portable/v0.2.9.2/src/main.cpp
License: https://github.com/Terence0816/easy-wg-portable/blob/main/LICENSE (MIT per repository)

| Finding | Source evidence | File / registry | Responsible component | NATIVE remedy (not selected) | PORTABLEAPPS remedy | Data safety / functionality tradeoff | Test | Limitation |
|---|---|---|---|---|---|---|---|---|
| Module-relative INI | Tagged `src/main.cpp`, `GetIniPath`, `LoadSettings`, `SaveSettings` | `EasyWG.ini` next to active EXE | EasyWG | Not applicable | Run an unchanged official `EasyWG.exe` from `Data/Runtime` | Protects INI, language, last selected config, tray settings | First run/change/relaunch, move folder | Absolute `LastConfig` paths outside app are not rewritten |
| ZIP import / configs | `ImportZipConfig`, `GetModuleDirectory` | Extracted `.conf` in EXE directory | EasyWG + PowerShell | Not applicable | Data/Runtime is executable directory | Credentials are in local Data; no host scavenging | ZIP import and content persistence | Never publish real private keys |
| Core component bootstrap | `kTunnelDownloadUrl`, `GetModuleDirectory` and bootstrap | `tunnel.dll`, `wireguard.dll` etc. beside EXE | EasyWG / WireGuard core | Not applicable | Downloaded components are naturally stored in Data/Runtime | Existing DLLs preserved across installer updates | Missing-DLL bootstrap, update check | Network access required, redistribution/licensing independent |
| Opt-in autostart | `SetAutostartRegistry` | HKCU Run value `EasyWG Portable` | EasyWG | Not applicable | Snapshot named value; if changed to this package's specific runtime EXE, point at root launcher after full exit, protect same-name prior entry | Prior entry may be overwritten *during* operation; do not enable with installed EasyWG | Before/after registry; normal exit, forced crash | Not guaranteed crash-safe; no broad ShellGuard implemented |
| Tunnel service | `CreateServiceW` and service-control functions | Windows service control database / adapter state | EasyWG/Windows WireGuard driver | Not applicable | Leave necessary, explicitly authorized OS work to upstream; don't delete unrelated services | Networking requires elevation; automatic cleanup must be verified manually | Connect/disconnect, service snapshot | Can't promise no host traces or support arbitrary no-admin VPN |
| Restart/single-instance | Mutex constant and `/restart-helper` source paths | `Local\\EasyWGPortableMainInstance` | EasyWG | Not applicable | Launcher watches matching `Data/Runtime/EasyWG.exe` processes; no termination or arbitrary mutex deletion | Can conflict with installed / separately portable copy | Restart while connected; tray exit | Elevated descendant visibility may be limited |
| Temporary PowerShell scripts | `MakeTempFilePath`, `GetTempPathW`, script writer/cleanup | System temporary folder (short-lived) | EasyWG/Powershell | Not applicable | Leave upstream lifecycle; never globally replace TEMP or sweep it | Unexpected crash can leave script or result | Process crash, observe app-owned temporary files | No persistent TEMP recovery without attribution |
| Windows caches and activity | Windows service/driver/system behavior | Event log, prefetch, DNS/routes, security caches | Windows | Not applicable | Document exceptions | Never delete host-managed history | Observe with VM snapshots | Inherently cannot guarantee zero OS activity |

Classification: source paths are **SOURCE-INSPECTED**. Actual filesystem, registry, GUI, service and crash outcomes are **NOT YET VERIFIED**, not runtime-observed. GUI/tray notification identity is Win32 native, not Electron; no invented Electron AUMID or CLSID management is included.

### Build identity and upstream app base

- Language/framework: native C++ / Windows Win32 (no Electron/CEF/WebView2). Official tagged native Windows `EasyWG.exe` is the package app base, so the full upstream source compilation is **not** part of the selected PortableApps pipeline.
- API finds latest stable release; resolves tag commit and tagged source ZIP. Only official release asset named `EasyWG.exe` is acceptable; independent SHA-256 is compared when GitHub release metadata or upstream checksums supply one.
- Source paths are checked against tagged `main.cpp` to fail closed when upstream architecture changes. A source adapter is not applied because it is not required for source-evidenced local profile redirection.
- The root C++ launcher is source-built by Visual Studio 2022 toolchain during GitHub Actions (Windows Server 2022). It uses no third-party binaries other than the official EasyWG release binary and Windows system libraries.
- Pinned shared actions from `vhick` are independently inspected at their *specified tag* before runtime use, but the workflow references the verified full release commit SHAs and checks tag-to-commit `action.yml` equivalence.

### Non-goals / hard limits

- The custom NSIS installer is not an official PortableApps.com Installer. The software is an unofficial WireGuard frontend; neither WireGuard nor PortableApps.com certification/endorsement is implied.
- No arbitrary HKLM, driver, network adapter, service or system TEMP cleaning. Such cleanup could destroy installed VPNs or other services.
- Manual Windows tests are required for private key safety, service cleanup, installed version coexistence, Windows 7, autostart failure recovery, install/reinstall, and moving an active tunnel.
