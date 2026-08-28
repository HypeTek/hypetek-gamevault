# 0.9.0-rc.1 Release Candidate checklist

## Completed in this RC source package

- [x] Windows PowerShell 5.1 smart-quote parser regression fixed in the Chinese agent copy.
- [x] CI parses every `windows-agent/*.ps1` file with Windows PowerShell 5.1 and PowerShell 7.
- [x] CI rejects typographic smart double quotes in executable PowerShell source.
- [x] Prerelease-aware GitHub release creation (`--prerelease`).
- [x] RC container versions do not overwrite the stable `latest` tag.
- [x] Release manifest records the GHCR image digest and Windows installer SHA-256.
- [x] Container ships `curl` for the TrueNAS `/health` check.
- [x] TrueNAS Community Catalog staging package added under `truenas-catalog/ix-dev/community/hypetek-mission-control`.
- [x] Catalog package uses TrueNAS rendering library 2.3.11 and fixed internal port mapping to 8080.
- [x] Primary game library remains read-only; `/config` and translator models are persistent writable storage.

## Local checks run on the prepared archive

- [x] YAML parse: GitHub workflow, `app.yaml`, `ix_values.yaml`, `questions.yaml`, basic TrueNAS test values.
- [x] Jinja syntax parse for the TrueNAS Compose template.
- [x] JavaScript syntax: `app.js`, `i18n.js`, `service-worker.js`.
- [x] Python compile check for `server/`, `tests/` and `tools/`.
- [x] 32 non-Flask unit tests passed, including scanner, settings, database, metadata, translation, design profiles, maintenance and release metadata.
- [x] API/Translator PDF regenerated for 0.9.0-rc.1.

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
