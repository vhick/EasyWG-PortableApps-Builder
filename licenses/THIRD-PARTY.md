# Third-party attribution and licensing

- **EasyWG Portable:** Terence0816, MIT. The build downloads unmodified `EasyWG.exe` from the author's official tagged GitHub Release, checks a SHA-256 digest, and includes upstream tagged `LICENSE` in `Other/Source`.
- **WireGuard / WireGuardNT / Wintun:** Copyright/licensing belongs to their respective upstream authors. Components are **not included** in the builder source kit or initial package binaries. EasyWG may download them after first run using its own source-defined mechanisms; review those components' licenses and checksums before distributing a modified/frozen bootstrap bundle.
- **Portable-Package-Builder@v1.0.0** and **portable-release-publisher@v1.1.1:** Called as pinned GitHub Actions, not bundled or represented as original builder code. Their own repository licenses remain applicable.
- **EasyWG application icon:** Extracted from the official author-released `EasyWG.exe`, not fabricated. GitHub users should check the upstream license and trademark expectations before branding or redistribution.
- **This builder's own code:** LICENSE-BUILDER.txt (MIT). Does not override any upstream or dependency license.

The released package is an unofficial community package; not an official WireGuard, PortableApps.com or Microsoft product.
