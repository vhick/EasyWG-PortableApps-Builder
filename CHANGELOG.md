# EasyWG PortableApps Builder release history

## b1r2 (2026-11-09)

- Fix: resolve MSVC linker error LNK2019 for __imp_MessageBoxW by linking User32.lib explicitly in the launcher build and documenting the dependency in source.
- Tests: add regression checks for User32.lib linker references and package/build revision consistency.
- Metadata: increment builder revision to b1r2 and installer revision to r2 so repaired outputs have a distinct release identity.
- Unchanged: upstream official EasyWG verification and profile layout, pinned shared builder and publisher commit SHAs.
- Verification: offline Python unittest tests only; hosted Windows build and interactive VPN testing not performed as part of this revision's creation.

## b1r1 (2026-11-09)

- Initial PortableApps-specific kit. The user's first GitHub Actions build failed at MSVC linking when MessageBoxW's User32.lib was omitted.
