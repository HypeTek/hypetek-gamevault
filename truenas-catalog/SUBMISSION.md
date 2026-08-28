# TrueNAS Community Catalog submission staging

This directory is prepared for an upstream `truenas/apps` contribution.

## Copy into the TrueNAS Apps fork

Copy only:

`ix-dev/community/hypetek-mission-control/`

into the same path in a current fork/clone of `truenas/apps`.
Do **not** copy `SUBMISSION.md` into the upstream pull request; TrueNAS asks contributors to modify only `/ix-dev/` or `/library/` and generates catalog metadata automatically.

## Validate with the current TrueNAS toolchain

From the root of the current `truenas/apps` checkout:

```bash
./.github/scripts/ci.py --app hypetek-mission-control --train community --test-file basic-values.yaml --render-only=true
./.github/scripts/ci.py --app hypetek-mission-control --train community --test-file basic-values.yaml
./.github/scripts/generate_metadata.py --app hypetek-mission-control --train community
./.github/scripts/port_validation.py
```

The first CI run may generate `item.yaml`, populate `templates/library/` and refresh the library hash. Those are TrueNAS toolchain outputs, not files maintained in this Mission Control repository.

## Before opening the PR

1. Confirm `ghcr.io/hypetek/hypetek-gamevault:0.9.0-rc.2` exists and passes its `/health` check.
2. Test a clean install with a read-only game dataset.
3. Test the managed translator model volume and then an upgrade while preserving `/config`.
4. Supply the icon and screenshots in the PR description. A TrueNAS reviewer will provide the final CDN URLs.
5. Disclose the upstream Mission Control license exactly as published in `LICENSE.md`; the project is source-available rather than OSI open-source, so catalog acceptance is ultimately a TrueNAS maintainer decision.
6. After the RC is accepted, replace the prerelease container tag with the chosen stable Mission Control release and bump the catalog package `version`.

## RC note

This package intentionally uses catalog package version `1.0.1` for a new app while `app_version` tracks the upstream Mission Control container version `0.9.0-rc.2`.
