# Code signing

This project is applying for free code signing for open source through
[SignPath Foundation](https://signpath.org/).

**Code signing policy:** Free code signing provided by
[SignPath.io](https://signpath.io/), certificate by
[SignPath Foundation](https://signpath.org/).

## What is signed

- `RyzenTempLimit.exe` (the onedir build)
- `RyzenTempLimit-onefile.exe` (the single-file build)

The certificate is issued to SignPath Foundation, so the publisher shown by
Windows is "SignPath Foundation". This is the normal model for the free
open-source program. Signing does not remove SmartScreen warnings immediately;
reputation is built across releases.

## Eligibility

- OSI-approved license: GNU GPL v3.0.
- Public, actively developed repository.
- No proprietary components. Bundled dependencies: zenmaster (GPL-3.0),
  pystray (LGPL-3.0), Pillow (MIT-CMU), six (MIT), PyInstaller bootloader
  (GPL-2.0 with the PyInstaller exception), Python/Tcl/Tk/OpenSSL/libffi/zlib.
- Binaries are built from this repository by GitHub Actions from a tag.

## How to apply

1. Sign in at <https://signpath.io/> with a GitHub account.
2. Apply at <https://signpath.org/apply> with:
   - repository: `https://github.com/socrabs151/ryzen-temp-limit`
   - release page: `https://github.com/socrabs151/ryzen-temp-limit/releases`
   - license: GPL-3.0
   - build: GitHub Actions, PyInstaller, artifacts attached to tagged releases
3. After approval, create an organization and a project, then:
   - signing policy slug: `release-signing`
   - artifact configuration: see `signpath/artifact-config.xml`
   - create an API token
4. Add the API token as the repository secret `SIGNPATH_API_TOKEN`.
5. Add repository variables `SIGNPATH_ORG_ID`, `SIGNPATH_PROJECT_SLUG`,
   `SIGNPATH_POLICY_SLUG`, `SIGNPATH_ARTIFACT_CONFIG_SLUG`.
6. Replace the placeholder step in `.github/workflows/release.yml` with the
   snippet below, then publish the next tag.

## Workflow snippet

```yaml
      - name: Sign onedir executable
        uses: signpath/github-action-submit-signing-request@v1
        with:
          api-token: ${{ secrets.SIGNPATH_API_TOKEN }}
          organization-id: ${{ vars.SIGNPATH_ORG_ID }}
          project-slug: ${{ vars.SIGNPATH_PROJECT_SLUG }}
          signing-policy-slug: ${{ vars.SIGNPATH_POLICY_SLUG }}
          artifact-configuration-slug: ${{ vars.SIGNPATH_ARTIFACT_CONFIG_SLUG }}
          artifact-path: dist/RyzenTempLimit/RyzenTempLimit.exe
          output-artifact-directory: signed/onedir
          wait-for-completion: true
```

The exact step ordering depends on how SignPath expects multi-file artifacts;
the artifact configuration below is the source of truth. Signing must happen
before the onedir folder is zipped and before the checksums are calculated.

## Application text

```text
Project: Ryzen Temp Limit
Repository: https://github.com/socrabs151/ryzen-temp-limit
License: GNU GPL v3.0 (OSI approved)
Releases: https://github.com/socrabs151/ryzen-temp-limit/releases
Description: A small Windows utility that caps AMD Ryzen CPU temperature via the
signed PawnIO driver. Built with Python/Tkinter, packaged with PyInstaller.
All binaries are built by GitHub Actions from tagged commits.
No proprietary components; bundled dependencies are GPL/LGPL/MIT/PSF/BSD.
```
