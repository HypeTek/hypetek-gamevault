# 0.9.0-rc.5 Release Candidate checklist

## Completed in this RC source package

- [x] Windows PowerShell 5.1 smart-quote parser regression fixed in the Chinese agent copy.
- [x] CI parses every `windows-agent/*.ps1` file with Windows PowerShell 5.1 and PowerShell 7.
- [x] CI checks typographic smart double quotes by Unicode codepoint without embedding those delimiters in the PowerShell command itself.
- [x] Prerelease-aware GitHub release creation (`--prerelease`).
- [x] RC container versions do not overwrite the stable `latest` tag.
- [x] Release manifest records the GHCR image digest and Windows installer SHA-256.
- [x] Container ships `curl` for the TrueNAS `/health` check.
- [x] TrueNAS Community Catalog staging package added under `truenas-catalog/ix-dev/community/hypetek-mission-control`.
- [x] Catalog package uses TrueNAS rendering library 2.3.11 and fixed internal port mapping to 8080.
- [x] Primary game library remains read-only; `/config` and translator models are persistent writable storage.
- [x] Game-content target list now exposes Arabic and Chinese native targets plus `Klingon (Beta)` and `Elvish / Sindarin (Beta)` when English is available.
- [x] Experimental Klingon/Sindarin targets are explicitly non-canonical and use an English intermediate plus conservative local vocabulary.
- [x] LCARS top navigation uses contrast derived from the actual dark capsule background.
- [x] Windows Agent EXE download checks the versioned release asset and falls back to the bundled ZIP instead of sending users to GitHub 404.
- [x] Windows Agent confirmation dialog restores a working title-bar `X`; `X`, `Esc` and the negative button all cancel safely.
- [x] RC documentation keeps `HypeTek/hypetek-gamevault` as the canonical repository during the release-candidate phase.
- [x] Direct installers on mapped SMB drives are converted to UNC paths before a possible UAC elevation.
- [x] PowerShell regression test preserves spaces, apostrophes, brackets and long titles during mapped-drive resolution.
- [x] Settings cancellation uses the selected UI language in every integrated language pack.
- [x] Klingon and Sindarin beta packs cover the complete settings, library, design, maintenance and Translator workflow without English fallback.
- [x] Cover fit mode and 100–200 % zoom are stored per game and shared by card, preview and detail view.

## Local checks run on the prepared archive

- [x] YAML parse: GitHub workflow, `app.yaml`, `ix_values.yaml`, `questions.yaml`, basic TrueNAS test values.
- [x] Jinja syntax parse for the TrueNAS Compose template.
- [x] JavaScript syntax: `app.js`, `i18n.js`, `service-worker.js`.
- [x] Python compile check for `server/`, `tests/` and `tools/`.
- [x] 75 Python unit tests passed, including the complete Flask route suite, scanner, settings, database, metadata, translation, design profiles, maintenance and release metadata.
- [x] PowerShell 7 mapped-drive path regression test passed locally; Windows PowerShell 5.1 is enforced by GitHub Actions.
- [x] API/Translator PDF source updated for 0.9.0-rc.5; PDF regenerated and visually verified across all four pages.

## Must turn green in GitHub before treating this as a usable RC

- [ ] Full Python test job after dependency installation.
- [ ] Windows PowerShell 5.1 parser job.
- [ ] PowerShell 7 parser job.
- [ ] Inno Setup EXE build.
- [ ] GHCR image build/push and generated image digest.
- [ ] GitHub prerelease with EXE and `release-manifest.txt` attached.

## Before a TrueNAS Community Catalog pull request

- [ ] Copy the staged app into a current `truenas/apps` fork.
- [ ] Run the upstream TrueNAS `ci.py` render and deployment tests.
- [ ] Run TrueNAS metadata generation and port validation.
- [ ] Clean install test on a disposable TrueNAS app instance.
- [ ] Upgrade test with existing `/config` data.
- [ ] Rollback test with a backup of `/config`.
- [ ] Confirm LibreTranslate model-storage ownership for image v1.9.6.
- [ ] Provide icon/screenshots and replace temporary asset URLs with reviewer-provided TrueNAS CDN URLs.
- [ ] Disclose the source-available Mission Control license in the PR and obtain maintainer acceptance.

The upstream TrueNAS test toolchain is intentionally not copied into this repository; it is run from a current `truenas/apps` checkout so schema/library changes are tested against the actual catalog version.
